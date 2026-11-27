import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
from src.display import Display
from src.version import __version__


def _lightness(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def test_default_green_palette_has_evenly_spaced_shades():
    """Shade 1 used to be almost equal to shade 0, hiding light-grey detail."""
    shades = [_lightness(c) for c in Display.PALETTES["green"]]
    steps = [a - b for a, b in zip(shades, shades[1:])]
    assert all(s > 0 for s in steps)
    assert max(steps) < 1.5 * min(steps)


def test_title_shows_version_and_palette_and_p_cycles():
    d = Display()
    assert pygame.display.get_caption()[0] == f"SnekBoy v{__version__} - green"
    for name in ("classic", "grey", "green"):
        d.next_palette()
        assert d.palette_name == name and d.COLORS == Display.PALETTES[name]
