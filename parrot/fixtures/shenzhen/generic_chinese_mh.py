from typing import List
from beartype import beartype
from parrot.fixtures.base import ColorWheelEntry, GoboWheelEntry
from parrot.fixtures.chauvet.mover_base import ChauvetMoverBase
from parrot.utils.colour import Color
from parrot.utils.dmx_utils import Universe


dmx_layout = {
    "pan_coarse": 0,
    "tilt_coarse": 1,
    "color_wheel": 2,
    "gobo_wheel": 3,
    "strobe": 4,
    "dimmer": 5,
    "speed": 6,
    "auto_mode": 7,
    "auto_swivel": 8,
    "led_ring": 9,
}

color_wheel: List[ColorWheelEntry] = [
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

gobo_wheel: List[GoboWheelEntry] = [
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

@beartype
class GenericChineseMovingHead10ch(ChauvetMoverBase):

    SUPPORTS_PAN_FINE = False
    SUPPORTS_TILT_FINE = False

    CHANNELS = dmx_layout
    PAN_RANGE = (0, 255)
    TILT_RANGE = (0, 255)


    def __init__(self, patch, universe=Universe.default, name="Generic Chinese 10ch"):
        super().__init__(
            patch,
            name=name,
            width=10,
            gobo_wheel=gobo_wheel,
            dmx_layout=dmx_layout,
            color_wheel=color_wheel,
            universe=universe,
            disable_fine=True,
        )

    def set_strobe(self, value):
        self.set("strobe", value)
