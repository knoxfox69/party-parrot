from typing import Optional, List
from beartype import beartype

from parrot.fixtures.base import GoboWheelEntry, ColorWheelEntry
from parrot.fixtures.moving_head import MovingHead
from parrot.utils.dmx_utils import Universe, dmx_clamp
from parrot.utils.colour import Color
from parrot.utils.color_extra import color_distance


dmx_layout = {
    "pan": 0,
    "tilt": 1,
    "color_wheel": 2,
    "gobo_wheel": 3,
    "strobe": 4,
    "dimmer": 5,
    "speed": 6,
    "auto_mode": 7,
    "auto_swivel": 8,
    "led_ring": 9,
}

# Full 10-channel class consistent with ChauvetMoverBase
@beartype
class GenericChineseMovingHead10ch(MovingHead):

    COLOR_WHEEL_ENTRIES: List[ColorWheelEntry] = [
        ColorWheelEntry(Color("white"), 0),
        ColorWheelEntry(Color("red"), 10),
        ColorWheelEntry(Color("green"), 20),
        ColorWheelEntry(Color("blue"), 30),
        ColorWheelEntry(Color("yellow"), 40),
        ColorWheelEntry(Color("orange"), 50),
        ColorWheelEntry(Color("cyan"), 60),
        ColorWheelEntry(Color("purple"), 70),
        ColorWheelEntry(Color("magenta"), 80),
    ]

    GOBO_WHEEL_ENTRIES: List[GoboWheelEntry] = [
        GoboWheelEntry("open", 65),
        GoboWheelEntry("dots", 72),
        GoboWheelEntry("spiral", 80),
        GoboWheelEntry("spiral2", 88),
        GoboWheelEntry("starburst", 96),
        GoboWheelEntry("four", 104),
        GoboWheelEntry("waves", 112),
        GoboWheelEntry("biohazard", 120),
        GoboWheelEntry("ring", 128),
        GoboWheelEntry("flower", 136),
    ]

    def __init__(
        self,
        address: int,
        name: str = "Generic Chinese MH 10ch",
        universe: Optional[Universe] = None,
        pan_lower=270,
        pan_upper=450,
        tilt_lower=0,
        tilt_upper=90,
        pan_range_deg: float = 540,
        tilt_range_deg: float = 270,
    ):
        if universe is None:
            universe = Universe.default

        super().__init__(
            address=address,
            name=name,
            width=10,
            gobo_wheel=self.GOBO_WHEEL_ENTRIES,
            universe=universe,
        )

        # Same behavior as ChauvetMoverBase
        self.pan_lower = pan_lower / 540 * 255
        self.pan_upper = pan_upper / 540 * 255
        self.pan_range = self.pan_upper - self.pan_lower
        self.tilt_lower = tilt_lower / 270 * 255
        self.tilt_upper = tilt_upper / 270 * 255
        self.tilt_range = self.tilt_upper - self.tilt_lower
        self.dmx_layout = dmx_layout

    def _set(self, name: str, value: int):
        """Chauvet-style DMX writer."""
        if name in self.dmx_layout:
            self.values[self.dmx_layout[name]] = int(dmx_clamp(value))

    #
    # PAN/TILT exactly like ChauvetMoverBase
    #
    def set_pan(self, value):
        projected = self.pan_lower + (self.pan_range * value / 255)
        super().set_pan_angle(projected / 255 * 540)


    def set_tilt(self, value):
        projected = self.tilt_lower + (self.tilt_range * value / 255)
        super().set_tilt_angle(projected / 255 * 270)


    #
    # COLOR exactly like ChauvetMoverBase
    #
    def set_color(self, color: Color):
        super().set_color(color)

        closest = None
        closest_dist = float("inf")

        for entry in self.COLOR_WHEEL_ENTRIES:
            d = color_distance(entry.color, color)
            if d < closest_dist:
                closest = entry
                closest_dist = d

        if closest is None:
            self._set("color_wheel", 0)
        else:
            self._set("color_wheel", closest.dmx_value)

    #
    # GOBO exactly like ChauvetMoverBase
    #
    def set_gobo(self, name: str):
        matches = [g for g in self.GOBO_WHEEL_ENTRIES if g.name == name]
        if not matches:
            raise ValueError(f"Unknown gobo {name}")

        self._set("gobo_wheel", matches[0].dmx_value)

    #
    # Other channels
    #
    def set_strobe(self, value: int):
        super().set_strobe(value)
        self._set("strobe", value)

    def set_speed(self, value: int):
        super().set_speed(value)
        self._set("speed", value)

    def set_auto_mode(self, value: int):
        self._set("auto_mode", value)

    def set_auto_swivel(self, value: int):
        self._set("auto_swivel", value)

    def set_led_ring(self, value: int):
        self._set("led_ring", value)
