"""
bleekWare.Scanner
"""

import asyncio
import time

from java import jclass, jint, jvoid, Override, static_proxy
from java.util import HashMap

# from android.bluetooth.le import BluetoothLeScanner
from android.bluetooth.le import ScanCallback, ScanResult, ScanSettings
from android.bluetooth import BluetoothAdapter

from . import BLEDevice, bleekWareError
from . import check_for_permissions


scan_result = {}


class _PythonScanCallback(static_proxy(ScanCallback)):
    """Callback class for LE Scan. PRIVATE.

    This class holds methods that receive and handle
    data from Android's BluetoothLeScanner methods.
    It is not intended to call this class directly.
    """

    def __init__(self, scanner):
        super(_PythonScanCallback, self).__init__()
        self.scanner = scanner

    @Override(jvoid, [jint, ScanResult])
    def onScanResult(self, callbackType, scanResult):
        """Receive and handle the scan result for BLE devices.

        This is the callback method for BluetoothLeScanner.startScan().
        """
        device = scanResult.getDevice()
        record = scanResult.getScanRecord()

        address = device.getAddress()

        new_device = BLEDevice(address, device.getName(), device)

        service_uuids = record.getServiceUuids()
        if service_uuids is not None:
            service_uuids = [
                service_uuid.toString()
                for service_uuid in service_uuids.toArray()  # was ArrayList
            ]

        manufacturer = record.getManufacturerSpecificData()
        manufacturer = {
            manufacturer.keyAt(index): bytes(manufacturer.valueAt(index))
            for index in range(manufacturer.size())
        }

        # Original code from Bleak:
        # service_data = {
        #     entry.getKey().toString(): bytes(entry.getValue())
        #     for entry in record.getServiceData().entrySet()
        # }
        # Need some workaround, as 'getServiceData().entrySet() is a Map
        # and is not iterable with Chaquopy. So we need to handle the
        # iteration by ourselves.
        # Also, MapCollection need to be converted to HashMap, otherwise
        # next() is not working.
        service_data = {}
        temp_map = HashMap(record.getServiceData())
        service_data_iterator = temp_map.entrySet().iterator()
        while service_data_iterator.hasNext():
            element = service_data_iterator.next()
            service_data[element.getKey().toString()] = bytes(
                element.getValue()
            )

        tx_power = (
            None
            if record.getTxPowerLevel() == -2147483648
            else record.getTxPowerLevel()
        )

        advertisement = AdvertisementData(
            local_name=record.getDeviceName(),
            manufacturer_data=manufacturer,
            service_data=service_data,
            service_uuids=service_uuids,
            tx_power=tx_power,
            rssi=scanResult.getRssi(),
            platform_data=(scanResult,),
        )

        scan_result[address] = (new_device, advertisement)
        if self.scanner.detection_callback:
            self.scanner.detection_callback(new_device, advertisement)


class AdvertisementData:
    """Class to hold advertisement data from a BLE device."""

    def __init__(
        self,
        local_name=None,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=0,
        platform_data=tuple(),
    ):
        self.local_name = local_name
        self.manufacturer_data = manufacturer_data
        self.service_data = service_data
        self.service_uuids = service_uuids
        self.tx_power = tx_power
        self.rssi = rssi
        self.platform_data = platform_data

    def __repr__(self):
        kwargs = []
        if self.local_name:
            kwargs.append(f"local_name={repr(self.local_name)}")
        if self.manufacturer_data:
            kwargs.append(f"manufacturer_data={repr(self.manufacturer_data)}")
        if self.service_data:
            kwargs.append(f"service_data={repr(self.service_data)}")
        if self.service_uuids:
            kwargs.append(f"service_uuids={repr(self.service_uuids)}")
        if self.tx_power is not None:
            kwargs.append(f"tx_power={repr(self.tx_power)}")
        kwargs.append(f"rssi={repr(self.rssi)}")
        return f"AdvertisementData({', '.join(kwargs)})"


class Scanner:
    """Class to scan for free (un-connected) Bluetooth LE devices."""

    scanner = None

    def __init__(
        self,
        detection_callback=None,
        service_uuids=None,
        scanning_mode='active',
        **kwargs,
    ):
        self.activity = self.context = jclass(
            'org.beeware.android.MainActivity'
        ).singletonThis
        self.detection_callback = detection_callback
        self.service_uuids = service_uuids
        if scanning_mode == 'passive':
            self.scan_mode = ScanSettings.SCAN_MODE_OPPORTUNISTIC
        else:
            self.scan_mode = ScanSettings.SCAN_MODE_LOW_LATENCY
        scan_result.clear()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Start a scan for BLE devices."""
        if Scanner.scanner is not None:
            raise bleekWareError(
                'A BleakScanner is already scanning on this adapter.'
            )

        check_for_permissions(self.activity)

        self.adapter = BluetoothAdapter.getDefaultAdapter()
        if self.adapter is None:
            raise bleekWareError(
                'Bluetooth is not supported on this hardware platform'
            )
        if self.adapter.getState() != BluetoothAdapter.STATE_ON:
            raise bleekWareError('Bluetooth is not turned on')

        self.leScanner = self.adapter.getBluetoothLeScanner()
        Scanner.scanner = self

        self.callback = _PythonScanCallback(Scanner.scanner)

        scan_result.clear()
        self.leScanner.startScan(self.callback)

    async def stop(self):
        """Stop a running scan."""
        if self.leScanner is not None:
            self.leScanner.stopScan(self.callback)
            Scanner.scanner = None
            self.leScanner = None

    async def advertisement_data(self):
        """Provide an asynchronous generator.

        Tuples of (BLEDevice, AdvertismentData are yielded upon
        detection.
        """
        devices = asyncio.Queue()
        self.detection_callback = lambda device, data: devices.put_nowait(
            (device, data)
        )
        try:
            while True:
                yield await devices.get()
        finally:
            self.detection_callback = None

    @property
    def discovered_devices(self):
        """Hold a list of found BLE devices."""
        return [device for device, _ in scan_result.values()]

    @property
    def discovered_devices_and_advertisement_data(self):
        """Store BLE devices and their advertisemend data in dictionary."""
        return scan_result

    @classmethod
    async def discover(cls, timeout=5.0, return_adv=False, **kwargs):
        """Search for BLE devices and return result.

        Returns a list of BLE devices of type BLEDevice (if
        'return_adv' is False) or a dictionary ('return_adv' = True),
        where the keys are the devices addresses (as MAC or UUID) and
        the values tuples of BLEDevice, AdvertisementData.
        """
        async with cls(**kwargs) as scanner:
            await asyncio.sleep(timeout)
            if return_adv:
                return scanner.discovered_devices_and_advertisement_data
            else:
                return scanner.discovered_devices

    @classmethod
    async def _find_device(
        cls, name=None, address=None, timeout=10.0, **kwargs
    ):
        """Scan for and find a certain device by name or address. PRIVATE."""
        async with cls(**kwargs):
            start_time = time.time()
            while time.time() < start_time + timeout:
                for device, _ in scan_result.values():
                    if name and device.name == name:
                        return device
                    elif address and device.address.lower() == address.lower():
                        return device
                await asyncio.sleep(0.1)
        return None

    @classmethod
    async def find_device_by_name(cls, name, timeout=10.0, **kwargs):
        """Search for and return a BLE device by its name."""
        return await cls._find_device(name, None, timeout, **kwargs)

    @classmethod
    async def find_device_by_address(cls, address, timeout=10.0, **kwargs):
        """Search for and return a BLE devce by its address."""
        return await cls._find_device(None, address, timeout, **kwargs)
