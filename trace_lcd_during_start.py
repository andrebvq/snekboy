"""
Trace LCD state during START button press
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def trace_lcd():
    """Trace LCD during START press"""
    print("="*70)
    print("TRACING LCD STATE DURING START PRESS")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    print(f"At 2M cycles:")
    print(f"  LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
    print(f"  LY: {cpu.memory.read_byte(0xFF44)}")
    print(f"  Screen pixels: {sum(1 for row in cpu.ppu.get_screen_buffer() for pixel in row if pixel != 0):,}")

    # Track LCDC and VRAM writes during START
    lcdc_changes = []
    vram_writes = []
    ly_samples = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if address == 0xFF40:
            lcdc_changes.append((cpu.total_cycles, value, cpu.registers._pc))
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            vram_writes.append((cpu.total_cycles, address, value))
        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Press START
    print("\n  Pressing START...")
    cpu.memory.joypad.press_button('start')

    for i in range(500_000):
        if i % 10_000 == 0:
            ly_samples.append((cpu.total_cycles, cpu.memory.read_byte(0xFF44)))
        cpu.step()

    cpu.memory.joypad.release_button('start')

    for i in range(500_000):
        if i % 10_000 == 0:
            ly_samples.append((cpu.total_cycles, cpu.memory.read_byte(0xFF44)))
        cpu.step()

    # Results
    print(f"\nResults:")
    print(f"  LCDC changes: {len(lcdc_changes)}")
    print(f"  VRAM writes (non-zero): {len(vram_writes)}")

    if lcdc_changes:
        print(f"\n  LCDC changes during/after START:")
        for cycle, value, pc in lcdc_changes:
            lcd_on = "ON" if (value & 0x80) else "OFF"
            print(f"    Cycle {cycle:8d}: PC=0x{pc:04X} LCDC=0x{value:02X} LCD={lcd_on}")

    if vram_writes:
        print(f"\n  First 10 VRAM writes:")
        for cycle, addr, value in vram_writes[:10]:
            print(f"    Cycle {cycle:8d}: [0x{addr:04X}]=0x{value:02X}")
    else:
        print(f"\n  NO VRAM writes detected")

    # Check LY progression
    print(f"\n  LY samples (every 10k steps):")
    for i, (cycle, ly) in enumerate(ly_samples[:20]):
        print(f"    Sample {i:2d}: Cycle {cycle:8d} LY={ly:3d}")

    if len(ly_samples) > 1:
        ly_advancing = any(ly_samples[i][1] != ly_samples[i-1][1]
                          for i in range(1, len(ly_samples)))
        if ly_advancing:
            print(f"\n  LY is advancing correctly")
        else:
            print(f"\n  LY is STUCK")

    # Final screen check
    screen = cpu.ppu.get_screen_buffer()
    pixels = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\n  Final screen pixels: {pixels:,}")


if __name__ == '__main__':
    trace_lcd()
