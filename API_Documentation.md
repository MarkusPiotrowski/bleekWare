# API Documentation
As **bleekWare** was especially developed to be 'usage compatible' to code using
Bleak, please also check the [Bleak documentation](https://bleak.readthedocs.io/en/latest/index.html).

## bleekWare `Scanner`
Documentation not yet available.


## bleekWare `Client`
Like Bleak's `BleakClient` you can use the `Client` class with an asynchronous context
manager or manually connect and disconnect to and from a BLE device.

#### Properties and methods of `BleakClient` that are not available in bleekWare's `Client`
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
The characteristic _must_ be identified as UUID string.


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
