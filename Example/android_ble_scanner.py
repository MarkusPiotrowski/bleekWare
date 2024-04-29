"""
Run Bluetooth LE on Android
"""

import asyncio

import toga
from toga import Button, MultilineTextInput
from toga.style import Pack
from toga.style.pack import COLUMN

if toga.platform.current_platform == 'android':
    from .bleekWare.Scanner import Scanner as Scanner
else:
    from bleak import BleakScanner as Scanner


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
        self.manual_button_gen = Button(
            'Manual start/stop scan (with generator)',
            on_press=self.manual_scan_with_generator,
        )
        self.device_list = MultilineTextInput(
            readonly=True,
            style=Pack(padding=(10, 5), height=200),
        )
        self.data_list = MultilineTextInput(
            readonly=True,
            style=Pack(padding=(10, 5), height=200),
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
            style=Pack(direction=COLUMN),
        )

        self.main_window = toga.MainWindow(
            title='Android BLE Scanner Demo App'
        )
        self.main_window.content = box
        self.main_window.show()
        self.scan_on = False

    async def start_scan(self, widget):
        """Use scanner with 'with' container.

        The scan result in scanner.discovered_devices and
        scanner.discovered_devices_and_advertisement_data
        contains each discovered device only once.
        """
        self.print_device('Start BLE scan...', clear=True)
        self.print_data(clear=True)

        async with Scanner() as scanner:
            await asyncio.sleep(10)
            self.print_device('...scanning stopped.')
            self.show_scan_result(
                scanner.discovered_devices_and_advertisement_data
            )

    async def start_discover(self, widget):
        """Use class method Scanner.discover().

        'return_adv=True' returns a dic.
        'return_adv=False' would just return a list of discovered devices.
        """
        self.print_device('Start BLE scan...', clear=True)
        self.print_data(clear=True)

        result = await Scanner.discover(return_adv=True)
        self.print_device('...scanning stopped.')
        self.show_scan_result(result)

    async def manual_scan_with_callback(self, widget):
        """Start and stop a scan manually and display results via callback."""
        if not self.scan_on:
            self.scanner = Scanner(self.scan_callback)
            await self.scanner.start()
            self.scan_on = True
            self.print_device('Start BLE scan...', clear=True)
            self.print_data('Device data:', clear=True)
        else:
            await self.scanner.stop()
            self.scan_on = False
            self.print_device('...scanning stopped.')

    async def manual_scan_with_generator(self, widget):
        """Start and stop a scan manually and display results via generator.

        Scanner.advertisement_data() returns an async generator.
        Requires bleak 0.21 or bleekWare.
        """
        if not self.scan_on:
            self.scan_on = True
            self.scanner = Scanner()
            await self.scanner.start()
            self.print_device('Start BLE scan...', clear=True)
            self.print_data('Device data:', clear=True)
            async for device, data in self.scanner.advertisement_data():
                self.print_device(self.get_name(device))
                self.print_data(str(device))
                self.print_data(str(data))
                self.print_data()
                if not self.scan_on:
                    await self.scanner.stop()
                    self.print_device('...scanning stopped.')
                    break
        else:
            self.scan_on = False

    def scan_callback(self, device, advertisement_data):
        """Receive data from scanner each time a device is found.

        The callback is called on each detection event, so the same
        device can pop up several times during the scan.

        This callback can be a normal or an async function.
        """
        self.print_device(self.get_name(device))
        self.print_data(str(device))
        self.print_data(str(advertisement_data))
        self.print_data()

    def show_scan_result(self, data):
        """Show names of found devices and attached advertisment data.

        'data' is a dictionary, where the keys are the BLE addresses
        and the values are tuples of BLE device, advertisement data.
        """
        self.print_device('Found devices:')
        self.print_data('Device data:', clear=True)
        for key in data:
            device, adv_data = data[key]
            self.print_device(self.get_name(device))
            self.print_data(f'{device}\n{adv_data}')
            self.print_data()

    def get_name(self, device):
        """Return name or address of BLE device."""
        if device.name:
            return device.name
        else:
            return f'No name ({device.address})'

    def print_device(self, device='', clear=False):
        """Write device name to MultilineTextInput for devices."""
        if clear:
            self.device_list.value = ''
        self.device_list.value += device + '\n'
        self.device_list.scroll_to_bottom()

    def print_data(self, data='', clear=False):
        """Write device data to MultilineTextInput for device data."""
        if clear:
            self.data_list.value = ''
        self.data_list.value += data + '\n'
        self.data_list.scroll_to_bottom()


def main():
    return BleScannerApp()
