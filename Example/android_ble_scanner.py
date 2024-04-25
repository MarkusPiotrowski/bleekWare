"""
Run Bluetooth LE on Android
"""
import asyncio

import toga
from toga import Button, MultilineTextInput
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

if toga.platform.current_platform == 'android':
    from .bleekWare.Scanner import Scanner as Scanner
    from .bleekWare.Client import Client as Client
else:
    from bleak import BleakScanner as Scanner
    from bleak import BleakClient as Client


class BleScannerApp(toga.App):
    """A small App to demonstrate Bluetooth LE functionality with bleekWare.

    bleekWare replaces Bleak on the Android platform when working with
    Toga and BeeWare (see the conditional import above).

    This app demonstrates several possibilities to perform a scan and
    read the advertised data.
    """

    def startup(self):
        """Set up the GUI."""
        self.scan_button = Button(
            'Scan for BLE devices (using async "with" container)',
            on_press=self.start_scan,
        )
        self.discover_button = Button(
            'Discover BLE devices (classmethod)',
            on_press=self.start_discover,
        )
        self.manual_button = Button(
            'Manual start/stop scan (with callback)',
            on_press=self.manual_scan_with_callback,
        )
        self.manual_button_gen = Button (
            'Manual start/stop scan (with generator)',
            on_press=self.manual_scan_with_generator,
        )
        self.device_list = MultilineTextInput(
            readonly=True,
            style=Pack(padding=(10,5), height=200),
        )
        self.data_list = MultilineTextInput(
            readonly=True,
            style=Pack(padding=(10,5), height=200),
        )
        box = toga.Box(
            children=[
                self.scan_button,
                self.discover_button,
                self.manual_button,
                self.manual_button_gen,
                self.device_list,
                self.data_list,
            ],
            style=Pack(direction=COLUMN)
        )
        
        self.main_window = toga.MainWindow(title='Android BLE Scanner Demo App')
        self.main_window.content = box
        self.main_window.show()
        self.scan_on = False

    async def start_scan(self, widget):
        """Use scanner with 'with' container.

        The scan result in scanner.discovered_devices and
        scanner.discovered_devices_and_advertisement_data
        contains each discovered device only once.
        """
        self.device_list.value = 'Start BLE scan...\n'
        self.data_list.value = ''

        async with Scanner() as scanner:
            await asyncio.sleep(10)
            self.device_list.value += '...scanning stopped.\n'
            self.show_scan_result(
                scanner.discovered_devices_and_advertisement_data
            )

    async def start_discover(self, widget):
        """Use class method Scanner.discover().

        'return_adv=True' returns a dic.
        'return_adv=False' would just return a list of discovered devices.
        """
        self.device_list.value = 'Start BLE scan...\n'
        self.data_list.value = ''

        result = await Scanner.discover(return_adv=True)
        self.device_list.value += '...scanning stopped.\n'
        self.show_scan_result(result)
    
    async def manual_scan_with_callback(self, widget):
        """Start and stop a scan manually and display results via callback.

        Callback must be synchronous (for bleekWare).
        """

        if not self.scan_on:
            self.scanner = Scanner(self.scan_callback)
            await self.scanner.start()
            self.scan_on = True
            self.device_list.value = 'Start BLE scan...\n'
            self.data_list.value = 'Device data: \n'
        else:
            await self.scanner.stop()
            self.scan_on = False
            self.device_list.value += '...scanning stopped.\n'

    async def manual_scan_with_generator(self, widget):
        """Start and stop a scan manually and display results via generator.

        Scanner.advertisement_data() returns an async generator.
        Requires bleak 0.21 or bleekWare.
        """
        if not self.scan_on:
            self.scan_on = True
            self.scanner = Scanner()
            await self.scanner.start()
            self.device_list.value = 'Start BLE scan...\n'
            self.data_list.value = 'Device data: \n'
            async for device, data in self.scanner.advertisement_data():
                self.device_list.value += self.get_name(device) + '\n'
                self.data_list.value += str(device) + '\n'
                self.data_list.value += str(data) + '\n\n'
                if not self.scan_on:
                    await self.scanner.stop()
                    self.device_list.value += '...scanning stopped.\n'
                    break
        else:
            self.scan_on = False            

    def scan_callback(self, device, advertisement_data):
        """Receive data from scanner each time a device is found.

        The callback is called on each detection event, so the same
        device can pop up several times during the scan.

        For the moment, the callback function in bleekWare must be
        synchronous.
        """
        self.device_list.value += self.get_name(device) + '\n'
        self.data_list.value += str(device) + '\n'
        self.data_list.value += str(advertisement_data) + '\n\n'

    def show_scan_result(self, data):
        """Show names of found devices and attached advertisment data.

        'data' is a dictionary, where the keys are the BLE addresses
        and the values are tuples of BLE device, advertisement data.
        """
        self.device_list.value += 'Found devices: \n'
        self.data_list.value += 'Device data: \n'
        for key in data:
            device, adv_data = data[key]
            self.device_list.value += self.get_name(device) + '\n'
            self.data_list.value += f'{device}\n{adv_data}\n\n'

    def get_name(self, device):
        """Return name or address of BLE device."""
        if device.name:
            return device.name
        else:
            return f'No name ({device.address})'


def main():
    return BleScannerApp()
