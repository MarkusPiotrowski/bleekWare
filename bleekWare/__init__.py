"""
bleekWare, a limited replacement for Bleak to use BLE on Android
within the BeeWare framework.

The code is heavily inspired by Bleak (https://github.com/hbldh/bleak).
Some parts may virtually be identical for the sake of compatibility to
Bleak.

(c) 2024 by Markus Piotrowski

MIT license
"""

from java import jclass
from android.os import Build


class BLEDevice:
    """Class to hold data of a BLE device.

    Note: 'details' is the OS native device.
    """

    def __init__(self, address, name, details):
        self.address = address
        self.name = name
        self.details = details

    def __str__(self):
        return f'{self.address}: {self.name}'

    def __repr__(self):
        return f'BLEDevice({self.address}, {self.name})'


class bleekWareError(Exception):
    """Base Exception for bleekWare."""

    pass


class bleekWareCharacteristicNotFoundError(bleekWareError):
    """A characteristic is not supported by a device."""
    
    def __init__(self, uuid):
        """
        uuid (str): UUID of the characteristic which was not found
        """
        super().__init__(f"Characteristic {uuid} was not found!")
        self.char_specifier = uuid


class bleekWareDeviceNotFoundError(bleekWareError):
    """A device couldn't be found."""
    
    def __init__(self, identifier, *args):
        """
        Args:
            identifier (str): device identifier (Bluetooth address or UUID)
            of the device which was not found
        """
        super().__init__(*args)
        self.identifier = identifier


class BLEGattService:

    def __init__(self, service):
        self.service = service
        self.characteristics = []
        self.descriptors = []


def check_for_permissions(activity):
    """Check for and request neccessary BLE permissions.

    This was a hard one. Hard to find which permissions are really
    neccessary and especially WHICH ONE ARE NOT ALLOWED TO ASK FOR
    AT THE SAME TIME.
    BLUETOOTH and BLUETOOTH_ADMIN don't require runtime permission,
    ACCESS_FINE_LOCATION does contain ACCESS_COARSE_LOCATION and
    ACCESS_BACKGROUND_LOCATION (?).
    """
    api_level = Build.VERSION.SDK_INT
    if api_level >= 23 and api_level <= 30:
        permissions = [
            jclass("android.Manifest$permission").ACCESS_FINE_LOCATION,
        ]
    elif api_level > 30:
        permissions = [
            jclass("android.Manifest$permission").BLUETOOTH_SCAN,
            jclass("android.Manifest$permission").BLUETOOTH_CONNECT,
        ]
    permissions_granted = all(
        activity.checkSelfPermission(permission)
        == jclass("android.content.pm.PackageManager").PERMISSION_GRANTED
        for permission in permissions
    )
    if not permissions_granted:
        activity.requestPermissions(permissions, 101)
