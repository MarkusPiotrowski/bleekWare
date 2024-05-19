# API Documentation
As **bleekWare** was especially developed to be 'usage compatible' to code using
Bleak, please also check the [Bleak documentation](https://bleak.readthedocs.io/en/latest/index.html).

## bleekWare `Scanner`
A class to search for free Bluetooth LE peripherals (BLE devices). Like
Bleak's `BleakScanner`, you can manually start and stop the scanning process or use
`Scanner` as an asynchronous context manager.
Also see the [`android_ble_scanner`](https://github.com/MarkusPiotrowski/bleekWare/blob/main/Example/android_ble_scanner.py)
example, which demonstrates some use cases.

#### Properties and methods of `BleakScanner` that are _not_ available in bleekWare's `Scanner`
- *find_device_by_filter()*
- *register_detection_callback()* (deprecated in Bleak)
- *set_scanning_filter()* (deprecated in Bleak)
- *get_discovered_devices()* (deprecated in Bleak)

### `Scanner` constructor

#### **Scanner(*detection_callback=None, service_uuids=None, scanning_mode='active', \*\*kwargs*)**
*Class to scan for free (un-connected) Bluetooth LE devices*

- **detection_callback**: Regular or asynchronous method to call when a device
is detected or advertising data of a detected device changes
- **service_uuids**: Not implemented (yet)
- **scanning_mode**: The scan mode (`'active'` or `'passive'`), usually set to `'passive'`
- **Additional keyword argument**: Without function

The detection_callback must receive a `BLEDevice` object and an `AdvertisementData`
object. 

#### Differences to `BleakScanner`
Filtering by service UUIDs is not supported yet. A number of optional keyword arguments are
not handled.

### `Scanner` properties

#### *discovered_devices*
A `list` of discovered devices as `BLEDevice` objects.

#### *discovered_devices_and_advertisement_data*
Dictionary with MAC addresses (`string`) of the BLE devices as key and `tuple`s of
(`BLEDevice`, `AdvertisementData`) as values.


### `Scanner` classmethods

#### **Scanner.discover(*timeout=5.0, return_adv=False, \*\*kwargs*)**
*Async classmethod to scan for Bluetooth LE devices and return the result*

- **timeout**: Duration of the scan period in seconds (`float`)
- **return_adv**: If advertisement data should be included in the returned data
(`bool`)
- **Additional keyword arguments**: Without function

The method either returns a `list` of detected `BLEDevice` objects (if **return_adv** is
`False`) or a `dict` of MAC addresses as key and `tuple`s of (`BLEDevice`, `AdvertisementData`)
as values (if **return_adv** is `True`).
 
##### Differences to 'BleakScanner.discover()`
Additional keyword arguments are not passed to the `Scanner`'s constructor.


#### **Scanner.find_device_by_name(*name, timeout=10.0, \*\*kwargs*)**
*Async classmethod to find a device by its name and return it as `BLEDEvice`object*

- **name**: The name of the BLE device (`string`)
- **timeout**: Duration of the scan period in seconds (`float`)
- **Additional keyword parameters**: Without function

##### Differences to 'BleakScanner.find_device_by_name()`
Additional keyword arguments are not passed to the `Scanner`'s constructor.


#### **Scanner.find_device_by_address(*address, timeout=10.0, \*\*kwargs*)**
*Async classmethod to find a device by its address and return it as `BLEDEvice`object*

- **address**: The MAC address of the BLE device (`string`)
- **timeout**: Duration of the scan period in seconds (`float`)
- **Additional keyword parameters**: Without function

##### Differences to 'BleakScanner.find_device_by_address()`
Additional keyword arguments are not passed to the `Scanner`'s constructor.


### `Scanner` methods


#### **start()**
*Async method to start the scan with a `Scanner`*

Scan results are optionally send to the **detection_callback** method defined in the 
`Scanner`'s constructor, can be read from the `Scanner`'s properties (`discovered_devices`
and `discovered_devices_and_advertisement_data`) or yielded from the asynchronous
generator `advertisement_data`.

#### **stop()**
*Async method to stop the running scan of a `Scanner`*

#### **advertisement_data()**
*Async generator that returns an async iterator to iterate over the scan results*

E.g. to use in `async for` loops to handle the data while they're coming in. Scan results
are yielded as `tuple` of (`BLEDevice`, `AdvertisementData`).



## bleekWare `Client`
Like Bleak's `BleakClient` you can use the `Client` class with an asynchronous context
manager or manually connect and disconnect to and from a BLE device.

#### Properties and methods of `BleakClient` that are _not_ available in bleekWare's `Client`
- *read_gatt_descriptor()*
- *write_gatt_descriptor()*
- *pair()*
- *unpair()* (there is no *unpair* functionality in Android anyway)
- *set_disconnected_callback()* (deprecated in Bleak)
- *get_services()* (deprecated in Bleak)

### `Client` constructor

#### **Client(*address, disconnected_callback=None, services=None, \*\*kwargs*)**
*Class to connect to a Bluetooth LE GATT server (a BLE device) and communicate with it.*

- **address**: `bleekWare.BLEDevice` object or device address (MAC as `string`)
- **disconnected_callback**: A synchronous method to call when the client is disconnected
- **services**: Not implemented yet
- **Additional keyword arguments**: Without function

##### Differences to `BleakClient`
The Client will not actively search for the device if only the MAC address is given.
Thus, the optional *timeout* keyword argument from `BleakClient` is without function
here. Also, additional keyword arguments are not handled.

The services filter has not been implemented.


### `Client` properties

#### *address*
*Property that holds the address of the connected BLEDevice*

address is a MAC address (`string`)


#### *is_connected*
*Property to show the connection status of the client*

`True` or `False`


#### *mtu_size*
*Property that holds the MTU size*

While the client tries to negotiate the highest possible MTU size (517) with the
device during connection, this size is not granted.

Returns an `integer`


#### *services*
*Property that holds data about the services of the connected device*

The services are stored as a `list` of `BLEGattService` objects. Each `BLEGattService`
object has a `service` attribute and a `characteristics` attribute (`list` of characteristics
UUIDs (`string`)). _Note: This is different to Bleak's `BLEGattService` objects!_

##### Differences to `BleakClient.services`
At the moment, this is a major difference to Bleak. Bleak returns a `BLEGattServiceCollection`. This type of object is not available in bleekWare. bleekWare returns a list of `BLEGattService` object, which are, however, different to Bleak's `BLEGattService` objects. bleekware's `BLEGattService` objects have a `service` attribute, containing the native Android GATT service object and a `characteristics` list (containing the characteristics UUIDs as strings). It does not contain data about the characteristics descriptors.


### `Client` methods

#### **connect(*\*\*kwargs*)**
*Async method to connect the client to the BLE device*

- **Additional keyword argument**: Not handled. Only for backward compatibility in Bleak


#### **disconnect()**
*Async method to disconnect the client from the BLE device*


#### **start_notify(*uuid, callback, \*\*kwargs*)**
*Async method to initiate a notifying characteristic*

- **uuid**: The notifying characteristic, adressed as UUID (`string`)
- **callback**: Regular or async method to receive the notification. The callback
method must have two parameters: the characteristic (`BluetoothGattCharacteristic`) and the received data (`bytearray`)
- **Additional keyword argument`**: Without function

Like in the Bleak's Python4Android backend, this method does not support indications
(which are notifications that must be acknowledged by the client).


##### Differences to `BleakClient.start_notify()`
The characteristic _must_ be identified as UUID string. Additional keyword arguments
are not handled.


#### **stop_notify(*uuid*)**
*Async method to stop a notifying characteristic and stop reading from it*

- **uuid**: The notifying characteristic, addressed as UUID (`string`)

##### Differences to `BleakClient.stop_notify()`
The characteristic _must_ be identified as UUID string.


#### **read_gatt_char(*uuid*)**
*Async method to read a value from a characteristic*

- **uuid**: The characteristic to read from, as UUID string

Returns the data as `bytearray`

##### Differences to `BleakClient.read_gatt_char()`
The characteristic _must_ be identified as UUID string. bleekWare's `Client.read_gatt_char()` supports both the new Android *readCharacteristic*
method for Android version 13 and above and the now deprecated *readCharacteristic*
method for Android version 12 and below.


#### **write_gatt_char(*uuid, data, response=None*)**
*Async method to write to a GATT characteristic with or without response*

- **uuid**: The characteristic to write to, as UUID (`string`)
- **data**: The data to write as `byte`
- **response**: If the BLE device should acknowledge the write operation (succeeded or
failed).

Not all characteristics support 'write with response'. If response is left as *None*,
the method checks if the characteristic allows 'write with response' and uses this,
otherwise 'write without response' is used.

##### Differences to `BleakClient.write_gatt_char()`
The characteristic _must_ be identified as UUID string.
bleekWare's `Client.write_gatt_char()` supports both the new Android *writeCharacteristic*
method for Android version 13 and above and the now deprecated *writeCharacteristic*
method for Android version 12 and below.
