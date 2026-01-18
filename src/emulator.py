"""
Main emulator loop with display
"""

from src.cpu import CPU
from src.display import Display
from src.tracer import Tracer
import time

class Emulator:
    """Game Boy Emulator with display"""

    # CPU cycles per frame at 60 FPS
    # CPU runs at 4194304 Hz, display at ~59.7 FPS
    # 4194304 / 59.7 ≈ 70224 cycles per frame
    CYCLES_PER_FRAME = 70224

    def __init__(self, rom_path=None, enable_tracing=True, trace_file="tracing/tracing.txt"):
        """
        Initialize emulator

        Args:
            rom_path: Optional path to ROM file to load
            enable_tracing: Enable execution tracing to tracing.txt
            trace_file: Path to trace file (default: tracing.txt in current directory)
        """
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        trace_path = os.path.join(project_root, trace_file)
        self.tracer = Tracer(trace_path, enabled=enable_tracing)
        self.enable_tracing = enable_tracing
        self.trace_file = trace_path

        # Tracing state
        self.vram_write_count = 0
        self.ly_read_count = 0
        self.last_lcdc = 0x00

        # Now initialize CPU and display
        self.cpu = CPU()
        self.display = Display()
        self.running = False

        if self.enable_tracing:
            self._setup_tracing()

        if rom_path:
            self.load_rom(rom_path)

    def _setup_tracing(self):
        """Setup memory tracing hooks"""
        # Save original methods
        self.original_read = self.cpu.memory.read_byte
        self.original_write = self.cpu.memory.write_byte

        # Create traced versions
        def traced_read(address):
            result = self.original_read(address)

            if address == 0xFF44:
                self.ly_read_count += 1
                if self.ly_read_count % 1000 == 0:
                    self.tracer.log_ly_read(self.cpu.total_cycles, self.cpu.registers._pc, result)

            return result

        def traced_write(address, value):
            if address == 0xFF40:
                if value != self.last_lcdc:
                    self.tracer.log_lcdc_write(self.cpu.total_cycles, self.cpu.registers._pc, value)
                    self.last_lcdc = value

            if 0x8000 <= address <= 0x9FFF and value != 0x00:
                self.vram_write_count += 1
                if self.vram_write_count <= 100 or self.vram_write_count % 100 == 0:
                    self.tracer.log_vram_write(self.cpu.total_cycles, self.cpu.registers._pc, address, value)

            if address == 0xFF46:
                self.tracer.log_dma_trigger(self.cpu.total_cycles, self.cpu.registers._pc, value)

            return self.original_write(address, value)

        # Replace methods
        self.cpu.memory.read_byte = traced_read
        self.cpu.memory.write_byte = traced_write

    def load_rom(self, rom_path):
        """Load a ROM file"""
        print(f"Loading ROM: {rom_path}")
        self.cpu.memory.load_rom_file(rom_path)

        # Simulate boot ROM
        self.cpu.simulate_boot()

        if self.enable_tracing:
            self.tracer.log_section("ROM LOADED AND BOOT ROM SIMULATED")
            self.tracer.log_state(self.cpu.total_cycles,
                                self.cpu.memory.read_byte(0xFF44),
                                self.cpu.memory.read_byte(0xFF40),
                                self.cpu.registers._pc)

        print("ROM loaded successfully")

    def run(self):
        """Main emulator loop"""
        self.running = True
        frame_count = 0
        start_time = time.time()

        print("Starting emulator...")
        if self.enable_tracing:
            print(f"Tracing enabled - logging to: {self.trace_file}")
            # Immediately log startup info to ensure file has content
            self.tracer.log_section("EMULATOR STARTED")
            self.tracer.log(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.tracer.log(f"Trace file: {self.trace_file}")
            self.tracer.log("")

        print("Controls:")
        print("  A/B/Start/Select: A, S, Z, X")
        print("  D-Pad (Up/Down/Left/Right): I, K, J, L")
        print("  Quit: ESC")
        print()

        # Track VBlank for logging
        last_if = self.cpu.memory._data[0xFF0F] if hasattr(self.cpu.memory, '_data') else 0

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

            # Track VBlank for logging
            if self.enable_tracing and hasattr(self.cpu.memory, '_data'):
                current_if = self.cpu.memory._data[0xFF0F]
                if (current_if & 0x01) and not (last_if & 0x01):
                    # VBlank just fired, log every 60th (once per second)
                    if frame_count % 60 == 0:
                        self.tracer.log_vblank(self.cpu.total_cycles)
                last_if = current_if

            # Debug info every second
            frame_count += 1
            if frame_count % 60 == 0:
                elapsed = time.time() - start_time
                fps = self.display.get_fps()
                ly = self.cpu.memory.read_byte(0xFF44)
                lcdc = self.cpu.memory.read_byte(0xFF40)

                print(f"FPS: {fps:.1f} | Cycles: {self.cpu.total_cycles:,} | "
                      f"LY: {ly} | LCDC: 0x{lcdc:02X}")

                # Log state to trace file
                if self.enable_tracing:
                    self.tracer.log_state(self.cpu.total_cycles, ly, lcdc, self.cpu.registers._pc)

        print("\nEmulator stopped")

        # Close tracer
        if self.enable_tracing:
            self.tracer.log_section("EMULATOR STOPPED")
            self.tracer.log(f"Total cycles: {self.cpu.total_cycles:,}")
            self.tracer.log(f"Total VRAM writes: {self.vram_write_count}")
            self.tracer.log(f"Total LY reads: {self.ly_read_count}")
            self.tracer.close()
            print(f"Trace file closed: {self.trace_file}")

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

        # Check for --no-trace flag
        enable_tracing = True
        if '--no-trace' in sys.argv:
            enable_tracing = False
            print("Tracing disabled")

        emu = Emulator(rom_path, enable_tracing=enable_tracing)
        emu.run()
    else:
        print("Usage: python -m src.emulator <rom_file> [--no-trace]")
        print("  --no-trace: Disable execution tracing")
        print("\nNo ROM specified, running test...")

        # Create test ROM with simple tile data
        emu = Emulator(enable_tracing=True)

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
