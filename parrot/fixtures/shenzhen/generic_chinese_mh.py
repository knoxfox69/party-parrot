from typing import Optional
from beartype import beartype

from parrot.fixtures.base import GoboWheelEntry, ColorWheelEntry
from parrot.fixtures.moving_head import MovingHead
from parrot.utils.dmx_utils import Universe, dmx_clamp
from parrot.utils.colour import Color
from parrot.utils.color_extra import color_distance


@beartype
class GenericChineseMovingHead10ch(MovingHead):
    """
    Generic Chinese moving head (10-channel mode) with LED ring.
    Channels:
        CH1: Pan (0-255)
        CH2: Tilt (0-255)
        CH3: Color wheel (0-255: colors 0-127, split mode 128-255)
        CH4: Gobo wheel / pattern (0-255: patterns 0-127, swivel motion 128-255)
        CH5: Strobe (0-255)
        CH6: Dimmer (0-255)
        CH7: Pan/Tilt speed (0-255)
        CH8: Automatic (0-255)
        CH9: Automatic swivel (0-255)
        CH10: LED ring (0-255)
    """

    # Color wheel DMX values for each color
    # Upper range (128-255) enables split mode between adjacent colors
    COLOR_WHEEL_ENTRIES = [
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

    # Gobo wheel: patterns are selected in 0-127 range
    # Each pattern has a base DMX value in the 0-127 range
    # When DMX value is 128-255, it enables swivel motion for the currently selected pattern
    # The pattern ranges define where each pattern is selected
    GOBO_PATTERN_RANGES = {
        "Backgammon 1": (0, 31),
        "Backgammon 2": (32, 63),
        "Backgammon 3": (64, 95),
        "Backgammon 4": (96, 127),
        "Backgammon 5": (128, 159),
        "Backgammon 6": (160, 191),
        "Backgammon 7": (192, 223),
        "Open": (224, 231),
        "Backgammon Flow": (232, 247),
        "5-Ball Shake": (248, 255),
    }

    # Gobo wheel entries for pattern selection
    # These are the base DMX values for each pattern (within 0-127 range for static display)
    GOBO_WHEEL_ENTRIES = [
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

    # Split mode starts at this DMX value
    COLOR_SPLIT_MODE_START = 128

    # Swivel motion starts at this DMX value
    GOBO_SWIVEL_MODE_START = 128

    def __init__(
        self,
        address: int,
        name: str,
        universe: Optional[Universe] = None,
    ):
        if universe is None:
            universe = Universe.default

        # Initialize as a generic moving head so Director groups it correctly
        super().__init__(
            address=address,
            name=name,
            width=10,
            gobo_wheel=self.GOBO_WHEEL_ENTRIES,
            universe=universe,
        )

        # Internal state for DMX channels
        self._pan_dmx = 0
        self._tilt_dmx = 0
        self._color_wheel_dmx = 0
        self._gobo_wheel_dmx = 0
        self._strobe_dmx = 0
        self._dimmer_dmx = 0
        self._speed_dmx = 0
        self._auto_mode_dmx = 0
        self._auto_swivel_dmx = 0
        self._led_ring_dmx = 0

        # Track current gobo for swivel mode
        self._current_gobo_index = 0

    #def set_pan_angle(self, value):
    #    """Set pan position (0-255) and update virtual pan angle."""
    #    v = dmx_clamp(value)
    #    self._pan_dmx = v
    #    # Assume 540° total pan range, like many small movers
    #    self.set_pan_angle(v / 255 * 540.0)

    #def set_tilt_angle(self, value):
    #    """Set tilt position (0-255) and update virtual tilt angle."""
    #    v = dmx_clamp(value)
    #    self._tilt_dmx = v
    #    # Assume 270° total tilt range
    #    self.set_tilt_angle(v / 255 * 270.0)

    def set_color(self, color: Color):
        """
        Translate Color object to color wheel DMX value.
        Finds closest color in wheel, or uses split mode for intermediate colors.
        """
        super().set_color(color)
        
        # Find the closest color in the color wheel
        closest_entry = None
        closest_distance = float("inf")
        
        for entry in self.COLOR_WHEEL_ENTRIES:
            dist = color_distance(entry.color, color)
            if dist < closest_distance:
                closest_distance = dist
                closest_entry = entry
        
        if closest_entry is None:
            # Fallback to white
            self._color_wheel_dmx = 0
            return
        
        # If the color is very close to a wheel color, use that directly
        if closest_distance < 0.1:
            self._color_wheel_dmx = closest_entry.dmx_value
            return
        
        # For intermediate colors, use split mode (128-255 range)
        # Find the two closest colors and interpolate between them
        distances = [
            (entry, color_distance(entry.color, color))
            for entry in self.COLOR_WHEEL_ENTRIES
        ]
        distances.sort(key=lambda x: x[1])
        
        if len(distances) >= 2:
            # Get two closest colors
            first_entry, first_dist = distances[0]
            second_entry, second_dist = distances[1]
            
            # Calculate split position (128-255)
            # Map the color distance ratio to split mode range
            total_dist = first_dist + second_dist
            if total_dist > 0:
                ratio = first_dist / total_dist
                # Split mode: 128 is first color, 255 is second color
                split_value = int(128 + (255 - 128) * ratio)
                self._color_wheel_dmx = split_value
            else:
                self._color_wheel_dmx = closest_entry.dmx_value
        else:
            self._color_wheel_dmx = closest_entry.dmx_value

    def set_dimmer(self, value):
        """Set dimmer value (0-255)"""
        super().set_dimmer(value)
        self._dimmer_dmx = dmx_clamp(value)

    def set_strobe(self, value):
        """Set strobe value (0-255)"""
        super().set_strobe(value)
        self._strobe_dmx = dmx_clamp(value)

    def set_speed(self, value):
        """Set pan/tilt speed (0-255)"""
        super().set_speed(value)
        self._speed_dmx = dmx_clamp(value)

    def set_gobo(self, gobo_name: str, speed: float = 0.0):
        """
        Set gobo wheel channel.
        
        The gobo wheel works as follows:
        - Patterns are selected in the 0-127 range (each pattern has a base DMX value)
        - When DMX value is 128-255, it enables swivel motion for the currently selected pattern
        - The pattern ranges define where each pattern is active
        
        Args:
            gobo_name: Name of the gobo pattern
            speed: Speed for swivel motion (0.0-1.0). 
                   If 0.0, uses static pattern at its base value.
                   If > 0.0, enables swivel motion (128-255) for the selected pattern.
        """
        # Find the gobo entry and its pattern range
        gobo_entry = None
        pattern_range = None
        
        for entry in self.GOBO_WHEEL_ENTRIES:
            if entry.name == gobo_name:
                gobo_entry = entry
                pattern_range = self.GOBO_PATTERN_RANGES.get(gobo_name)
                break
        
        if gobo_entry is None:
            raise ValueError(f"Gobo '{gobo_name}' not found")
        
        self._current_gobo_index = self.GOBO_WHEEL_ENTRIES.index(gobo_entry)
        
        if speed <= 0.0:
            # Static pattern - use the base DMX value from the pattern range
            # Use the start of the pattern range as the base value
            if pattern_range:
                self._gobo_wheel_dmx = pattern_range[0]
            else:
                self._gobo_wheel_dmx = gobo_entry.dmx_value
        else:
            # Swivel motion mode (128-255)
            # The swivel motion applies to whichever pattern is currently selected
            # Map speed (0.0-1.0) to swivel range (128-255)
            speed_clamped = max(0.0, min(1.0, speed))
            swivel_value = int(128 + (255 - 128) * speed_clamped)
            self._gobo_wheel_dmx = swivel_value

    def set_auto_mode(self, value: int):
        """Set automatic mode (0-255)"""
        self._auto_mode_dmx = dmx_clamp(value)

    def set_auto_swivel(self, value: int):
        """Set automatic swivel (0-255)"""
        self._auto_swivel_dmx = dmx_clamp(value)

    def set_led_ring(self, value: int):
        """Set LED ring (0-255)"""
        self._led_ring_dmx = dmx_clamp(value)

    @property
    def color_wheel(self):
        """Get color wheel entries"""
        return self.COLOR_WHEEL_ENTRIES

    @property
    def gobo_wheel(self):
        """Get gobo wheel entries"""
        return self.GOBO_WHEEL_ENTRIES

    def render(self, dmx):
        """
        Write all internal state to DMX values array and render.
        """
        # Map all channels to values array
        self.values[0] = self._pan_dmx
        self.values[1] = self._tilt_dmx
        self.values[2] = self._color_wheel_dmx
        self.values[3] = self._gobo_wheel_dmx
        self.values[4] = self._strobe_dmx
        self.values[5] = self._dimmer_dmx
        self.values[6] = self._speed_dmx
        self.values[7] = self._auto_mode_dmx
        self.values[8] = self._auto_swivel_dmx
        self.values[9] = self._led_ring_dmx
        
        # Call parent render to write to DMX
        super().render(dmx)
