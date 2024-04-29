"""
bleekware.Client
"""

import asyncio
import functools
import inspect

from java import jarray, jbyte, jclass, jint, jvoid, Override, static_proxy
from java.util import UUID

from android.bluetooth import (
    BluetoothAdapter,
    BluetoothGatt,
    BluetoothGattCallback,
    BluetoothProfile,
    BluetoothGattCharacteristic,
    BluetoothGattDescriptor,
)
from android.os import Build

from . import BLEDevice, BLEGattService
from . import bleekWareError, bleekWareCharacteristicNotFoundError


received_data = []
status_message = []
services = []

# Client Characteristic Configuration Descriptor
CCCD = '00002902-0000-1000-8000-00805f9b34fb'


class _PythonGattCallback(static_proxy(BluetoothGattCallback)):
    """Callback class for GattClient. PRIVATE."""

    def __init__(self, client):
        super(_PythonGattCallback, self).__init__()
        self.client = client

    @Override(jvoid, [BluetoothGatt, jint, jint])
    def onConnectionStateChange(self, gatt, status, newState):
        """Register connect or disconnect events.

        This is the callback function for Android's 'device.ConnectGatt'.
        """
        if newState == BluetoothProfile.STATE_CONNECTED:
            status_message.append('connected')
            gatt.discoverServices()
        elif newState == BluetoothProfile.STATE_DISCONNECTED:
            status_message.append('disconnected')
            gatt = None
            services.clear()
            if self.client.disconnected_callback:
                self.client.disconnected_callback()

    @Override(jvoid, [BluetoothGatt, jint])
    def onServicesDiscovered(self, gatt, status):
        """Write services to list.

        This is the callback function for Android's 'gatt.discoverServices'.
        """
        services.extend(gatt.getServices().toArray())
        # getServices returns an ArrayList, must be converted to Array to work
        # with Python

    @Override(
        jvoid,
        [BluetoothGatt, BluetoothGattCharacteristic, jarray(jbyte), jint],
    )
    @Override(jvoid, [BluetoothGatt, BluetoothGattCharacteristic, jint])
    def onCharacteristicRead(self, gatt, characteristic, *args):
        """Put characteristic's read value to a data list.

        This is the callback function for Android's 'gatt.readCharacteristic'.

        Covers the deprecated version (API level < 33 / Android 12 and older)
        and the actual version (API level 33 upwards  / Android 13 and newer).
        """
        status = args[-1]
        # Android 12 and below:
        if len(args) == 1:
            value = characteristic.getValue()
        else:
            value = args[0]
        if status == BluetoothGatt.GATT_SUCCESS:
            received_data.append(value)

    @Override(
        jvoid, [BluetoothGatt, BluetoothGattCharacteristic, jarray(jbyte)]
    )
    def onCharacteristicChanged(self, gatt, characteristic, value):
        """Read the notification.

        This is the callback function for notifying services.
        """
        received_data.append(characteristic.getValue())

    @Override(jvoid, [BluetoothGatt, jint, jint])
    def onMtuChanged(self, gatt, mtu, status):
        """Handle change in MTU size.

        This is the callback function for changes in MTU.
        """
        if status == BluetoothGatt.GATT_SUCCESS:
            self.client.mtu = mtu


class Client:
    """Class to connect to a Bluetooth LE GATT server and communicate."""

    client = None

    def __init__(
        self,
        address_or_ble_device,
        disconnected_callback=None,
        services=None,
        *,
        timeout=10.0,
        **kwargs,
    ):
        self.activity = self.context = jclass(
            'org.beeware.android.MainActivity'
        ).singletonThis

        if isinstance(address_or_ble_device, BLEDevice):
            self._address = address_or_ble_device.address
            self.device = address_or_ble_device.details
        else:
            self._address = address_or_ble_device
            self.device = BluetoothAdapter.getDefaultAdapter().getRemoteDevice(
                self._address
            )

        self.disconnected_callback = (
            None
            if disconnected_callback is None
            else functools.partial(disconnected_callback, self)
        )
        if services:
            raise NotImplementedError()
        self.adapter = kwargs.get('adapter', kwargs.get('device', None))
        self.gatt = None
        self.services = []
        self.mtu = 23

    def __str__(self):
        return f'{self.__class__.__name__}, {self.address}'

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self, **kwargs):
        """Connect to a GATT server."""
        self.adapter = BluetoothAdapter.getDefaultAdapter()
        if self.adapter is None:
            raise bleekWareError('Bluetooth is not supported on this device')
        if self.adapter.getState() != BluetoothAdapter.STATE_ON:
            raise bleekWareError('Bluetooth is turned off')

        if self.gatt is not None:
            self.gatt.connect()
        else:
            # Make a reference for external access
            Client.client = self

            # Create a GATT connection
            self.gatt_callback = _PythonGattCallback(Client.client)
            self.gatt = self.device.connectGatt(
                self.activity, False, self.gatt_callback
            )
            self.gatt_callback.gatt = self.gatt

            # Read the services
            while not services:
                await asyncio.sleep(0.1)
            self.services = await self.get_services()

            # Ask for max Mtu size
            self.gatt.requestMtu(517)

    async def disconnect(self):
        """Disconnect from connected GATT server."""
        if self.gatt is None:
            return True
        try:
            self.gatt.disconnect()
            self.gatt.close()
        except Exception as e:
            status_message.append(e)

        self.gatt = None
        self.services.clear()
        services.clear()
        status_message.clear()
        received_data.clear()
        Client.client = None

    async def get_services(self):
        """Read and store the announced services of a GATT server.

        The characteristics of the services are also read. Both are
        stored in a list of BLEGattService objects.
        """
        if self.services:
            return self.services
        for service in services:
            new_service = BLEGattService(service)
            characts = service.getCharacteristics().toArray()
            for charact in characts:
                new_service.characteristics.append(str(charact.getUuid()))
            self.services.append(new_service)
        return self.services

    async def start_notify(self, char_specifier, callback, *kwargs):
        """Start notification of a notifying characteristic.

        ``char_specifier`` must be an UUID as string
        ``callback`` must be a synchronous callback method
        """
        if not self.is_connected:
            raise bleekWareError('Client not connected')

        self.notification_callback = callback
        characteristic = self._find_characteristic(char_specifier)
        if characteristic:
            self.gatt.setCharacteristicNotification(characteristic, True)
            descriptor = characteristic.getDescriptor(UUID.fromString(CCCD))
            descriptor.setValue(
                BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            )
            self.gatt.writeDescriptor(descriptor)

            # Send received data to callback function
            while self.notification_callback:
                if received_data:
                    data = received_data.pop()
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(
                            callback(char_specifier, bytearray(data))
                        )
                    else:
                        callback(char_specifier, bytearray(data))
                await asyncio.sleep(0.1)

    async def stop_notify(self, char_specifier):
        """Stop notification of a notifying characteristic."""
        characteristic = self._find_characteristic(char_specifier)
        if characteristic:
            self.gatt.setCharacteristicNotification(characteristic, False)
            descriptor = characteristic.getDescriptor(UUID.fromString(CCCD))
            descriptor.setValue(
                BluetoothGattDescriptor.DISABLE_NOTIFICATION_VALUE
            )
            self.gatt.writeDescriptor(descriptor)

            self.notification_callback = None

    async def read_gatt_char(self, uuid):
        """Read from a characteristic.

        For bleekWare, you must pass the characteristic's 128 bit UUID
        as string.
        """
        characteristic = self._find_characteristic(uuid)
        if characteristic:
            self.gatt.readCharacteristic(characteristic)
            while not received_data:
                await asyncio.sleep(0.1)
            return bytearray(received_data.pop())
        else:
            raise bleekWareCharacteristicNotFoundError(uuid)

    async def write_gatt_char(self, uuid, data, response=None):
        """Write to a characteristic.

        For bleekWare, you must pass the characteristic's 128 bit UUID
        as string.
        """
        characteristic = self._find_characteristic(uuid)
        if characteristic:
            if response is None:
                if (
                    characteristic.getProperties()
                    and BluetoothGattCharacteristic.PROPERTY_WRITE
                ):
                    write_type = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
                elif (
                    characteristic.getProperties()
                    and BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE
                ):
                    write_type = (
                        BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                    )
            elif response:
                write_type = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
            else:
                write_type = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE

            if Build.VERSION.SDK_INT < 33:  # Android 12 and older
                characteristic.setWriteType(write_type)
                characteristic.setValue(data)
                self.gatt.writeCharacteristic(characteristic)
            else:
                self.gatt.writeCharacteristic(characteristic, data, write_type)
        else:
            raise bleekWareCharacteristicNotFoundError(uuid)

    @property
    def is_connected(self):
        return False if self.gatt is None else True

    @property
    def mtu_size(self):
        return self.mtu

    @property
    def address(self):
        return self._address

    def _find_characteristic(self, uuid):
        """Find and return characteristic object by UUID. PRIVATE."""
        for service in self.services:
            if uuid in service.characteristics:
                return service.service.getCharacteristic(UUID.fromString(uuid))
        return None
