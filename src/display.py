"""
Display module for Game Boy emulator using pygame

Renders the PPU screen buffer to a window
"""

import pygame
import sys
from src.version import __version__
from itertools import chain

class Display:
    """Display window for Game Boy emulator"""

    # Game Boy screen dimensions
    GB_WIDTH = 160
    GB_HEIGHT = 144

    # Display scale factor
    SCALE = 3  # 3x scale = 480x432 window

    # Colour palettes for the 4 DMG shades (0 = lightest). The DMG screen is a
    # reflective LCD with no backlight, so there is no single "true" colour.
    # "green":   classic look with evenly spaced shades (default)
    # "classic": the widespread #9BBC0F palette; shades 0 and 1 are almost equal
    # "grey":    neutral greys, as many emulators and the Game Boy Pocket use
    PALETTES = {
        "green": [(155, 188, 15), (101, 143, 31), (48, 98, 48), (15, 56, 15)],
        "classic": [(155, 188, 15), (139, 172, 15), (48, 98, 48), (15, 56, 15)],
        "grey": [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)],
    }
    PALETTE_KEY = pygame.K_p            # cycles through PALETTES

    def __init__(self, title=f"SnekBoy v{__version__}", palette="green"):
        """
        Initialize pygame display

        Args:
            title: Window title
            palette: Name of the starting entry in PALETTES
        """
        pygame.init()
        self.title = title

        self.width = self.GB_WIDTH * self.SCALE
        self.height = self.GB_HEIGHT * self.SCALE

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(title)
        self.set_palette(palette)

        # Create surface for Game Boy screen (will be scaled up)
        self.gb_screen = pygame.Surface((self.GB_WIDTH, self.GB_HEIGHT))

        # Frame timing
        self.clock = pygame.time.Clock()
        self.target_fps = 60  # Game Boy runs at ~59.7 FPS

    def set_palette(self, name):
        """Switch to the named palette."""
        self.palette_name = name
        self.COLORS = self.PALETTES[name]

    def next_palette(self):
        names = list(self.PALETTES)
        self.set_palette(names[(names.index(self.palette_name) + 1) % len(names)])

    def render(self, screen_buffer):
        """
        Render PPU screen buffer to window

        Args:
            screen_buffer: 144x160 array of color values (0-3)
        """
        # Hand pygame the whole frame at once: one byte per pixel (colour
        # number 0-3) on an 8-bit surface whose palette holds the 4 colours.
        pixels = bytes(chain.from_iterable(screen_buffer))
        frame = pygame.image.frombuffer(pixels, (self.GB_WIDTH, self.GB_HEIGHT), "P")
        frame.set_palette(self.COLORS)

        # Scale up to window size
        scaled_screen = pygame.transform.scale(
            frame,
            (self.width, self.height)
        )

        # Draw to window
        self.screen.blit(scaled_screen, (0, 0))
        pygame.display.flip()

    def handle_events(self, joypad=None):
        """
        Handle pygame events (quit, keyboard, etc.)

        Args:
            joypad: Optional Joypad instance to update with key presses

        Returns:
            bool: False if quit event detected, True otherwise
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == self.PALETTE_KEY:
                    self.next_palette()

                # Handle joypad input
                if joypad:
                    # A, B, Start, Select: A, S, Z, X
                    if event.key == pygame.K_a:
                        joypad.press_button('a')
                    elif event.key == pygame.K_s:
                        joypad.press_button('b')
                    elif event.key == pygame.K_z:
                        joypad.press_button('start')
                    elif event.key == pygame.K_x:
                        joypad.press_button('select')
                    # D-Pad: J, K, I, L (Left, Down, Up, Right)
                    elif event.key == pygame.K_j:
                        joypad.press_button('left')
                    elif event.key == pygame.K_k:
                        joypad.press_button('down')
                    elif event.key == pygame.K_i:
                        joypad.press_button('up')
                    elif event.key == pygame.K_l:
                        joypad.press_button('right')

            elif event.type == pygame.KEYUP:
                # Release buttons when keys are released
                if joypad:
                    if event.key == pygame.K_a:
                        joypad.release_button('a')
                    elif event.key == pygame.K_s:
                        joypad.release_button('b')
                    elif event.key == pygame.K_z:
                        joypad.release_button('start')
                    elif event.key == pygame.K_x:
                        joypad.release_button('select')
                    elif event.key == pygame.K_j:
                        joypad.release_button('left')
                    elif event.key == pygame.K_k:
                        joypad.release_button('down')
                    elif event.key == pygame.K_i:
                        joypad.release_button('up')
                    elif event.key == pygame.K_l:
                        joypad.release_button('right')

        return True

    def limit_fps(self):
        """Limit frame rate to target FPS"""
        self.clock.tick(self.target_fps)

    def get_fps(self):
        """Get current FPS"""
        return self.clock.get_fps()

    def close(self):
        """Close display and quit pygame"""
        pygame.quit()
