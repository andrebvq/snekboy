"""
Find when game loads graphics data (non-zero VRAM writes)
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

def find_graphics_load():
    """Find when graphics are loaded"""
    print("="*70)
    print("FINDING GRAPHICS LOAD")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    vram_nonzero_writes = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            vram_nonzero_writes.append({
                'cycle': cpu.total_cycles,
                'pc': cpu.registers._pc,
                'address': address,
                'value': value
            })

        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Run to 2M cycles
    print("\nRunning to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    print(f"\nNon-zero VRAM writes: {len(vram_nonzero_writes)}")

    if vram_nonzero_writes:
        print(f"\n  First 50 non-zero VRAM writes:")
        for i, write in enumerate(vram_nonzero_writes[:50]):
            print(f"    {i+1:3d}. Cycle {write['cycle']:8d}: PC=0x{write['pc']:04X} [0x{write['address']:04X}]=0x{write['value']:02X}")

        print(f"\n  Last 20 non-zero VRAM writes:")
        for i, write in enumerate(vram_nonzero_writes[-20:]):
            idx = len(vram_nonzero_writes) - 20 + i
            print(f"    {idx+1:3d}. Cycle {write['cycle']:8d}: PC=0x{write['pc']:04X} [0x{write['address']:04X}]=0x{write['value']:02X}")

        # Check if writes stop after boot
        first_cycle = vram_nonzero_writes[0]['cycle']
        last_cycle = vram_nonzero_writes[-1]['cycle']

        print(f"\n  First write at cycle: {first_cycle:,}")
        print(f"  Last write at cycle: {last_cycle:,}")

        if last_cycle < 1_000_000:
            print(f"\n  All graphics loaded during boot (before 1M cycles)")
        else:
            print(f"\n  Graphics continue to be written after boot")

        # Count writes per 100k cycle window
        windows = {}
        for write in vram_nonzero_writes:
            window = write['cycle'] // 100_000
            windows[window] = windows.get(window, 0) + 1

        print(f"\n  Writes per 100k cycle window:")
        for window in sorted(windows.keys()):
            count = windows[window]
            start = window * 100_000
            end = (window + 1) * 100_000
            print(f"    {start:8d}-{end:8d}: {count:5d} writes")

    # Check screen at various points
    screen = cpu.ppu.get_screen_buffer()
    pixels = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"\n  Final screen pixels: {pixels:,}")


if __name__ == '__main__':
    find_graphics_load()
