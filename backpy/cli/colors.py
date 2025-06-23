from enum import Enum

from catppuccin.palette import PALETTE as _PALETTE

from backpy import VariableLibrary


# RGB to ANSI guide from
# https://jakob-bagterp.github.io/colorist-for-python/ansi-escape-codes/rgb-colors/
def rgb_to_ansi(r: int, g: int, b: int, foreground: bool = True) -> str:
    fg_bg_str = "38;2;" if foreground else "48;2;"
    return f"\x1b[{fg_bg_str}{r};{g};{b}m"


def _get_value(self, instance, owner):
    return self.value


PALETTE = dict()

for val in _PALETTE.__iter__():
    palette = val.identifier

    PALETTE[palette] = dict()

    for key, color in _PALETTE.__dict__[palette].colors.__dict__.items():
        PALETTE[palette][key] = rgb_to_ansi(r=color.rgb.r, g=color.rgb.g, b=color.rgb.b)

    PALETTE[palette] = Enum(palette, PALETTE[palette])
    PALETTE[palette].__get__ = _get_value


_palette_dict = PALETTE.copy()

PALETTE = Enum("PALETTE", _palette_dict.copy())
"""
A variant of the catppuccin color palette, which returns ANSI color codes instead
of rgb / hex colors.
The PALETTE and the flavors can be called as enum values.

The order of calls is always:

``PALETTE.<flavor>.<color>``

Examples
--------

>>> PALETTE.latte.blue
'\x1b[38;2;30;102;245m'

"""

PALETTE._member_names_ = list(_palette_dict.keys())
PALETTE._member_map_ = _palette_dict
PALETTE.__get__ = _get_value


# special ANSI characters taken from
# https://jakob-bagterp.github.io/colorist-for-python/ansi-escape-codes/effects/#cheat-sheet

RESET = "\x1b[0m"
"""
Resets all styling of the text.
"""

EFFECTS = Enum(
    "EFFECTS",
    {
        "bold": Enum("bold", {"on": "\x1b[1m", "off": "\x1b[21m"}),
        "dim": Enum("bold", {"on": "\x1b[2m", "off": "\x1b[22m"}),
        "underline": Enum("bold", {"on": "\x1b[4m", "off": "\x1b[24m"}),
        "blink": Enum("bold", {"on": "\x1b[5m", "off": "\x1b[25m"}),
        "reverse": Enum("bold", {"on": "\x1b[7m", "off": "\x1b[27m"}),
        "hide": Enum("bold", {"on": "\x1b[8m", "off": "\x1b[28m"}),
    },
)
"""
An enum containing ANSI effects for the text
The EFFECTS and the effects itself can be called as enum values.

The order of calls is always:

``EFFECTS.<effect>.<on/off>``

Examples
--------

>>> EFFECTS.bold.on
'\x1b[1m'

"""

EFFECTS.__get__ = _get_value

for effect in EFFECTS:
    effect.value.__get__ = _get_value


def get_default_palette():
    return PALETTE[VariableLibrary().get_variable("cli.color_palette")]
