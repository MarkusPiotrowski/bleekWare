# bleekWare
A limited Bleak complement for accessing Bluetooth LE on Android in Python apps made with BeeWare.

## Introduction
**bleekWare** (a  portmanteau of "Bleak" and "BeeWare") is a limited complement for [Bleak](https://github.com/hbldh/bleak) to access Bluetooth LE on Android devices from Python apps made with [BeeWare](https://beeware.org/).

Bleak, the 'Bluetooth Low Energy platform Agnostic Klient', allows using Python to access Bluetooth LE cross-platform, but it's existing platform backend for Android requires [python-for-android (P4A)](https://python-for-android.readthedocs.io/en/latest/index.html). This can be used e.g. in [Kivy](https://kivy.org/) but not in BeeWare, because BeeWare uses [Chaquopy](https://chaquo.com/chaquopy/) as bridging tool between Python and Android.

> For discussion if the existing Android backend of Bleak can be modified for using it in BeeWare or to add another Android backend to Bleak, read [here](https://github.com/beeware/toga/issues/740), [here](https://github.com/beeware/beeware/issues/181) and [here](https://github.com/hbldh/bleak/blob/5e294f4fcdc3effac147d43e29697373e3209901/docs/backends/android.rst#L14).

bleekWare makes use of Chaquopy to access the native Android's Bluetooth LE APIs. bleekWare is 'usage compatible' to Bleak, meaning that it's methods have the same names and return (mostly) the same data as Bleak. Thus, using platform-dependent import switches, the same code can run on Linux, Mac and Windows using Bleak or on Android using bleekWare. However, bleekWare is _not_ dependent on Bleak; if your Python app should only run on Android you don't need to install or import Bleak in addition to bleekWare.

## Limitations
bleekWare is a _limited_ complement for Bleak. Not all functions are covered:
1. Deprecated parts of Bleak have not been replicated in bleekWare
2. bleekWare primarily serves me in my own small projects. Functionality that I don't require (e.g. bonding) is likely not implemented. However, pull requests to extend the functionality of bleekWare are welcome
3. bleekWare is work in progress
4. bleekWare is made for Android apps made with BeeWare and requires [Chaquopy](https://chaquo.com/chaquopy/) to access the Android API
5. bleekWare requires ~128-bit~ UUID _strings_ to address services and characteristics
6. ~~Callback functions (like `detection_callback` or `notify_callback`)in bleekWare can't be _asynchronous_~~

## How to use it
The current set-up procedure requires some manual intervention and puts the bleekWare code next to your app code. This may change in the future.

1. Set up a virtual environment to start a new BeeWare project as described in the [BeeWare tutorial](https://docs.beeware.org/en/latest/)
2. Write and test some code for a desktop computer (Linux, Mac or Window) using Bleak to access Bluetooth LE
3. Before setting up an Android project, copy the following lines into the `tool.briefcase.app.bluetooth.android` section of your `pyproject.toml` file, e.g. below the
`build_gradle_dependencies`:

   ```
   build_gradle_extra_content = "android.defaultConfig.python.staticProxy('your_project.bleekWare.Scanner',  'your_project.bleekWare.Client')"
   android_manifest_extra_content = """
   <uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />
   <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />
   <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" android:maxSdkVersion="30" />
   <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" android:maxSdkVersion="30" />
   <uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:usesPermissionFlags="neverForLocation" />
   <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
   """
   ```
   
   Replace `your_project` with the actual folder name of your project.
5. If your code runs fine on your desktop platform, set up an Android project as described in the [BeeWare tutorial](https://docs.beeware.org/en/latest/tutorial/tutorial-5/android.html>)
6. Now, download the [bleekWare module as zip file](https://github.com/MarkusPiotrowski/bleekWare/releases/download/0.2.0/bleekWare.zip) and place the unzipped bleekWare subfolder in your apps's folder:

   ```
   beeware_venv/
   |- your_project/
      |- build/
      |- logs/
      |- src/
      |  |- your_project/
      |  |  |- bleekWare/         <---
      |  |  |  |- __init__.py
      |  |  |  |- Client.py
      |  |  |  |- Scanner.py
      |  |  |- resources/
      |  |  |- __init__.py
      |  |  |- __main__.py
      |  |  |- app.py
      |  |- your_project.dist-info/
      |- tests/
    ...
   ```
   Note: If you use the 'Download ZIP' option from the `<> Code` button above, the download will contain the whole repository. Copy only the bleekWare subfolder to your project.
8. If your application should run cross-platform and you require both Bleak and bleekWare, you may want to use conditional imports like this:
   ```python
   import toga

   if toga.platform.current_platform == 'android':
      from .bleekWare import bleekWareError as BLEError
      from .bleekWare.Client import Client as Client
      from .bleekWare.Scanner import Scanner as Scanner  
   else:
      from bleak import BleakError as BLEError
      from bleak import BleakClient as Client
      from bleak import BleakScanner as Scanner
        
   ...
   ```

## Example code
### Scanner class
See [`android_ble_scanner.py`](Example/android_ble_scanner.py) in the Example folder for different BLE scanning examples. The code is tested to run on Windows (using Bleak) and Android devices (using bleekWare). It should be running on Mac and Linux as well (again using Bleak), but this hasn't been tested.

### Client class
Connecting to a BLE device and reading from or writing to it's characteristics is dependent on the device's capabilities; thus providing a general working example app isn't possible. But here is an outline for connecting to a BLE device and reading from a notifying service:

```python
"""
Connect to and read notifications from a BLE device
"""

import asyncio

import toga
from toga.style import Pack
from toga.style.pack import COLUMN
from toga import Button, MultilineTextInput

if toga.platform.current_platform == 'android':
    from .bleekWare import bleekWareError as BLEError
    from .bleekWare.Client import Client as Client
    from .bleekWare.Scanner import Scanner as Scanner
else:
    from bleak import BleakError as BLEError
    from bleak import BleakScanner as Scanner
    from bleak import BleakClient as Client


# Put here a notifying characteristic of your device:
NOTIFY_UUID = '0000fff1-0000-1000-8000-00805f9b34fb'

# Possibly not available or different UUID:
BATTERY_UUID = '00002a19-0000-1000-8000-00805f9b34fb'  

class bleekWareExample(toga.App):

    def startup(self):
        """Build a little GUI."""
        self.scan_button = Button(
            'Scan for BLE devices', on_press=self.search_device
        )
        self.message_box = MultilineTextInput(
            readonly=True,
            style=Pack(padding=(10, 5), height=200),
        )
        self.data_box = MultilineTextInput(
            readonly=True,
            style=Pack(padding=(10, 5), height=200),
        )
        box = toga.Box(
            children=[
                self.scan_button,
                self.message_box,
                self.data_box
            ],
            style=Pack(direction=COLUMN)
        )        
        self.main_window = toga.MainWindow(title='bleekWare Example')
        self.main_window.content = box
        self.main_window.show()

    async def search_device(self, widget):
        """Search for BLE device by name."""
        device = None
        self.message_box.value = 'Start BLE scan...\n'
        try:
            # Replace the name of your device here:
            device = await Scanner.find_device_by_name('your_device_by_name')

            # Alternatively, you may want to find your device by it's
            # MAC address or UUID (on Mac):
            # device = await Scanner.find_device_by_address('AA:BB:CC:DD:EE:FF'): 

        except (OSError, BLEError) as e:
            self.message_box.value += (
                f'Bluetooth not available. Error: {str(e)}\n'
            )

        if device:
            self.message_box.value += 'Found it!\n'
            await self.connect_to_device(device)
        else:
            self.message_box.value += "Sorry, couldn't find it...\n"

    async def connect_to_device(self, device):
        """Connect to BLE device."""
        self.message_box.value += 'Connecting to device...\n'
        async with Client(device, self.disconnect_callback) as client:
            self.message_box.value += (
                f'Client is connected: {client.is_connected}\n'
            )
            
            # You device probably hasn't a battery level characteristic 
            battery_level = await client.read_gatt_char(BATTERY_UUID)  # if available
            self.message_box.value += (
                'Battery level: '
                f'{int.from_bytes(battery_level, "big")}%\n'
            )
            await client.start_notify(
                NOTIFY_UUID, self.show_data
            )
            await asyncio.Future()

    def disconnect_callback(self, client):
        """Handle disconnection."""
        self.message_box.value += f'DEVICE WAS DISCONNECTED from {client}\n'

    def show_data(self, char, data):
        """Show notifications."""
        self.data_box.value += str(data.hex()) + '\n'


def main():
    return bleekWareExample()

```
