import enum

from parrot.fixtures.base import FixtureGroup, ManualGroup
from parrot.fixtures.chauvet.intimidator110 import ChauvetSpot110_12Ch
from parrot.fixtures.chauvet.intimidator160 import ChauvetSpot160_12Ch
from parrot.fixtures.led_par import ParRGB, ParRGBAWU
from parrot.fixtures.motionstrip import Motionstrip38
from parrot.fixtures.oultia.laser import TwoBeamLaser
from parrot.fixtures.shenzhen.generic_chinese_mh import GenericChineseMovingHead10ch
from parrot.utils.dmx_utils import Universe


class ChauvetSpot120_12Ch(ChauvetSpot110_12Ch):
    """Alias class so legacy patches still expose a Spot120 type."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


venues = enum.Enum(
    "Venues",
    ["dmack", "mtn_lotus", "truckee_theatre", "crux_test", "two_heads_only"],
)


def _two_heads_only():
    return [
        GenericChineseMovingHead10ch(
            patch=1, name="Front Spot 1", universe=Universe.default
        ),
    ]


def _dmack_patch():
    return [
        ChauvetSpot160_12Ch(patch=1),
        ChauvetSpot120_12Ch(patch=30),
        ParRGB(patch=60),
        Motionstrip38(patch=80),
    ]


def _mtn_lotus_patch():
    return [
        ParRGBAWU(patch=1),
        ParRGBAWU(patch=12),
        Motionstrip38(patch=40),
        TwoBeamLaser(address=90),
    ]


def _truckee_patch():
    mover_group = FixtureGroup(
        [
            ChauvetSpot160_12Ch(patch=1),
            ChauvetSpot160_12Ch(patch=25),
        ],
        name="Truckee Movers",
    )
    return [mover_group, ParRGB(patch=70), ParRGB(patch=80)]


def _crux_patch():
    return [
        ChauvetSpot120_12Ch(patch=1),
        ParRGB(patch=30),
    ]


venue_patches = {
    venues.dmack: _dmack_patch(),
    venues.mtn_lotus: _mtn_lotus_patch(),
    venues.truckee_theatre: _truckee_patch(),
    venues.crux_test: _crux_patch(),
    venues.two_heads_only: _two_heads_only(),
}

manual_groups = {
    venues.dmack: None,
    venues.mtn_lotus: ManualGroup(
        [ParRGBAWU(patch=200), ParRGB(patch=220)], name="Mountain Lotus Manual"
    ),
    venues.truckee_theatre: ManualGroup(
        [ParRGB(patch=240), ParRGB(patch=260)], name="Truckee Manual"
    ),
    venues.crux_test: None,
    venues.two_heads_only: None,
}


def get_manual_group(venue):
    return manual_groups.get(venue)


def has_manual_dimmer(venue):
    manual_group = manual_groups.get(venue)
    return manual_group is not None and len(manual_group.fixtures) > 0
