"""
Main emulator loop with display
"""

from src.cpu import CPU
from src.display import Display
import time

class Emulator:
    """Game Boy Emulator with display"""

    # CPU cycles per frame at 60 FPS
    # CPU runs at 4194304 Hz, display at ~59.7 FPS
    # 4194304 / 59.7 ≈ 70224 cycles per frame
    CYCLES_PER_FRAME = 70224

    def __init__(self, rom_path=r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"):
        """
        Initialize emulator

        Args:
            rom_path: Optional path to ROM file to load
        """
        self.cpu = CPU()
        self.display = Display()
        self.running = False

        if rom_path:
            self.load_rom(rom_path)

    def load_rom(self, rom_path):
        """Load a ROM file"""
        print(f"Loading ROM: {rom_path}")
        self.cpu.memory.load_rom_file(rom_path)
        print("ROM loaded successfully")

    def run(self):
        """Main emulator loop"""
        self.running = True
        frame_count = 0
        start_time = time.time()

        print("Starting emulator...")
        print("Controls:")
        print("  A/B/Start/Select: A, S, Z, X")
        print("  D-Pad (Up/Down/Left/Right): I, K, J, L")
        print("  Quit: ESC")
        print()

        while self.running:
            # Handle events (keyboard, quit, etc.) and update joypad
            if not self.display.handle_events(self.cpu.memory.joypad):
                self.running = False
                break

            # Run CPU for one frame worth of cycles
            cycles_this_frame = 0
            while cycles_this_frame < self.CYCLES_PER_FRAME:
                try:
                    cycles = self.cpu.step()
                    cycles_this_frame += cycles
                except NotImplementedError as e:
                    print(f"\nError: Unimplemented instruction: {e}")
                    print(f"PC: 0x{self.cpu.registers._pc:04X}")
                    print(f"Total cycles: {self.cpu.total_cycles:,}")
                    self.running = False
                    break
                except Exception as e:
                    print(f"\nError: {e}")
                    import traceback
                    traceback.print_exc()
                    self.running = False
                    break

            # Render frame
            screen_buffer = self.cpu.ppu.get_screen_buffer()
            self.display.render(screen_buffer)

            # Limit to 60 FPS
            self.display.limit_fps()

            # Debug info every second
            frame_count += 1
            if frame_count % 60 == 0:
                elapsed = time.time() - start_time
                fps = self.display.get_fps()
                print(f"FPS: {fps:.1f} | Cycles: {self.cpu.total_cycles:,} | "
                      f"LY: {self.cpu.memory.read_byte(0xFF44)} | "
                      f"LCDC: 0x{self.cpu.memory.read_byte(0xFF40):02X}")

        print("\nEmulator stopped")
        self.display.close()

    def run_headless(self, max_cycles=1_000_000):
        """
        Run emulator without display (for testing)

        Args:
            max_cycles: Maximum cycles to run
        """
        print(f"Running headless for {max_cycles:,} cycles...")

        cycles_run = 0
        while cycles_run < max_cycles:
            try:
                cycles = self.cpu.step()
                cycles_run += cycles
            except NotImplementedError as e:
                print(f"\nError: Unimplemented instruction: {e}")
                print(f"PC: 0x{self.cpu.registers._pc:04X}")
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()
                break

        print(f"Completed {cycles_run:,} cycles")
        print(f"LY: {self.cpu.memory.read_byte(0xFF44)}")
        print(f"LCDC: 0x{self.cpu.memory.read_byte(0xFF40):02X}")

        # Get screen buffer stats
        screen = self.cpu.ppu.get_screen_buffer()
        colors_used = set()
        for row in screen:
            colors_used.update(row)
        print(f"Colors used in screen buffer: {sorted(colors_used)}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        rom_path = sys.argv[1]
        emu = Emulator(rom_path)
        emu.run()
    else:
        print("Usage: python -m src.emulator <rom_file>")
        print("\nNo ROM specified, running test...")

        # Create test ROM with simple tile data
        emu = Emulator()

        # Write some test tile data to VRAM
        # Tile 0: Checkerboard pattern
        tile_data = [
            0xAA, 0x55,  # Line 0: 10101010, 01010101
            0x55, 0xAA,  # Line 1: 01010101, 10101010
            0xAA, 0x55,  # Line 2
            0x55, 0xAA,  # Line 3
            0xAA, 0x55,  # Line 4
            0x55, 0xAA,  # Line 5
            0xAA, 0x55,  # Line 6
            0x55, 0xAA,  # Line 7
        ]

        # Write tile to VRAM (tile 1 at 0x8000)
        for i, byte in enumerate(tile_data):
            emu.cpu.memory.write_byte(0x8010 + i, byte)

        # Fill tile map with tile 1
        for i in range(32 * 32):
            emu.cpu.memory.write_byte(0x9800 + i, 1)

        # Enable LCD
        emu.cpu.memory.write_byte(0xFF40, 0x91)  # LCD on, BG on

        print("Test pattern created. Starting emulator...")
        emu.run()
