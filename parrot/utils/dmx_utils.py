from DMXEnttecPro import Controller
import math
import os
import enum

from beartype import beartype
from parrot.utils.mock_controller import MockDmxController
from .math import clamp
from stupidArtnet import StupidArtnet


class Universe(enum.Enum):
    """DMX Universe enumeration"""

    default = "art1"  # Maps to Entec controller


@beartype
def dmx_clamp(n):
    if math.isnan(n):
        return 0
    return int(clamp(n, 0, 255))


@beartype
def dmx_clamp_list(items):
    return [int(clamp(item, 0, 255)) for item in items]


usb_path = "/dev/cu.usbserial-EN419206"


@beartype
def find_entec_port():
    import os
    import glob
    import serial.tools.list_ports
    import sys

    # First, try the hardcoded path
    if os.path.exists(usb_path):
        print(f"Found Entec port at hardcoded path: {usb_path}")
        return usb_path

    # macOS-specific tty fallback
    if sys.platform == "darwin":
        tty_path = usb_path.replace("/dev/cu.", "/dev/tty.")
        if os.path.exists(tty_path):
            print(f"Found Entec port at tty variant: {tty_path}")
            return tty_path

    ports = serial.tools.list_ports.comports()
    print(f"Scanning {len(ports)} serial ports for Entec DMX controller...")

    for port in ports:
        desc = str(port.description).lower()
        hwid = str(port.hwid).lower()
        manufacturer = str(getattr(port, "manufacturer", "")).lower()
        product = str(getattr(port, "product", "")).lower()

        if "0403" in hwid and "6001" in hwid:
            print(f"✅ Found FTDI device at {port.device}")
            return port.device

        if any(
            keyword in desc
            or keyword in hwid
            or keyword in manufacturer
            or keyword in product
            for keyword in ["enttec", "entec", "dmx", "ftdi"]
        ):
            print(f"✅ Found potential Entec device at {port.device}")
            return port.device

    # OS-specific /dev scanning
    if sys.platform == "darwin":
        scan_patterns = [
            "/dev/cu.usbserial*",
            "/dev/cu.usbmodem*",
            "/dev/tty.usbserial*",
            "/dev/tty.usbmodem*",
        ]
    else:  # Linux + others
        scan_patterns = [
            "/dev/ttyUSB*",
            "/dev/ttyACM*",
        ]

    print(f"Scanning /dev using patterns: {scan_patterns}")
    for pattern in scan_patterns:
        for path in glob.glob(pattern):
            if os.path.exists(path):
                print(f"✅ Found device at {path}")
                return path

    print("❌ No Entec DMX controller port found")
    return None


class ArtNetController:
    """Standalone Art-Net controller with DMX controller interface"""

    def __init__(self, artnet_ip="127.0.0.1", artnet_universe=0):
        self.artnet = StupidArtnet(artnet_ip, artnet_universe, 512, 30, True, True)
        self.dmx_data = [0] * 512

    def set_channel(self, channel, value, universe=None):
        # Channels are 1-indexed for DMX, 0-indexed for Art-Net
        # universe parameter is accepted for compatibility but not used (single universe controller)
        if 1 <= channel <= 512:
            self.dmx_data[channel - 1] = int(value)

    def submit(self):
        self.artnet.set(self.dmx_data)
        self.artnet.show()
        print(f"Setting channel {self.dmx_data}")

class SwitchController:
    def __init__(self, controller_map):
        self.controller_map = controller_map

    def set_channel(self, channel, value, universe=Universe.default):
        controller = self.controller_map.get(universe)
        if controller:
            controller.set_channel(channel, value)

    def submit(self):
        for controller in self.controller_map.values():
            controller.submit()

# Per-venue Art-Net configuration
# Format: {venue: {"ip": "x.x.x.x", "universe": 0}}
artnet_config = {
    "two_heads_only": {"ip": "127.0.0.1", "universe": 0},
}


@beartype
def get_entec_controller():
    """Get Entec controller or mock if not available"""
    if os.environ.get("MOCK_DMX", False) != False:
        return MockDmxController()

    # Try to find the Entec port
    port_path = find_entec_port()
    if port_path is None:
        print("⚠️  Could not find Entec DMX controller port")
        print("   Troubleshooting steps:")
        print("   1. Make sure the Entec DMX USB PRO is plugged in")
        print("   2. Check System Information > USB to see if the device appears")
        print("   3. Try unplugging and replugging the device")
        print(
            "   4. Install FTDI drivers if needed: https://ftdichip.com/drivers/vcp-drivers/"
        )
        print("   5. Check if the device appears under a different name")
        print("   Using mock DMX controller")
        return MockDmxController()

    # Try to connect with the found port
    try:
        return Controller(port_path)
    except Exception as e:
        # If cu.* fails, try tty.* variant (macOS specific)
        if port_path.startswith("/dev/cu."):
            tty_path = port_path.replace("/dev/cu.", "/dev/tty.")
            if os.path.exists(tty_path):
                try:
                    return Controller(tty_path)
                except Exception as e2:
                    print(
                        f"Could not connect to Entec DMX controller at {port_path}: {e}"
                    )
                    print(
                        f"Could not connect to Entec DMX controller at {tty_path}: {e2}"
                    )
        else:
            print(f"Could not connect to Entec DMX controller at {port_path}: {e}")
        print("Using mock DMX controller")
        return MockDmxController()


@beartype
@beartype
def get_controller(venue=None):
    controller_map = {}
    switch_controller = SwitchController(controller_map)

    # Always create Art-Net as the default universe
    if venue is not None:
        venue_name = venue.name if hasattr(venue, "name") else str(venue)
        config = artnet_config.get(venue_name)
        if config:
            print(f"Art-Net enabled for {venue_name}: {config['ip']} Universe {config['universe']}")
            artnet = ArtNetController(config["ip"], config["universe"])
        else:
            print(f"No Art-Net config for venue {venue_name}, using localhost Art-Net")
            artnet = ArtNetController("127.0.0.1", 0)
    else:
        artnet = ArtNetController("127.0.0.1", 0)

    controller_map[Universe.default] = artnet

    return switch_controller

