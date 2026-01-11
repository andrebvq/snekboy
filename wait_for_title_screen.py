"""
Wait longer to see if copyright screen automatically transitions
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

def wait_for_title():
    """Wait for automatic transition to title screen"""
    print("="*70)
    print("WAITING FOR TITLE SCREEN TRANSITION")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    vram_writes = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            vram_writes.append((cpu.total_cycles, address, value))
        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Check screen at intervals
    checkpoints = [1_000_000, 2_000_000, 3_000_000, 4_000_000, 5_000_000]

    last_pixels = 0
    last_writes = 0

    for checkpoint in checkpoints:
        print(f"\nRunning to {checkpoint/1_000_000:.1f}M cycles...")

        while cpu.total_cycles < checkpoint:
            cpu.step()

        screen = cpu.ppu.get_screen_buffer()
        pixels = sum(1 for row in screen for pixel in row if pixel != 0)

        new_writes = len(vram_writes) - last_writes

        print(f"  Pixels: {pixels:,}")
        print(f"  VRAM writes since last check: {new_writes}")
        print(f"  Total VRAM writes: {len(vram_writes)}")

        if pixels != last_pixels:
            print(f"  SCREEN CHANGED! ({last_pixels} -> {pixels})")

        if new_writes > 0:
            print(f"  First 5 new writes:")
            for cycle, addr, value in vram_writes[last_writes:last_writes+5]:
                print(f"    Cycle {cycle:8d}: [0x{addr:04X}]=0x{value:02X}")

        last_pixels = pixels
        last_writes = len(vram_writes)

    # Final summary
    print(f"\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    if len(vram_writes) > 5009:  # More than boot writes
        print(f"\nVRAM writes detected after boot!")
        print(f"  Total writes: {len(vram_writes)}")
        print(f"  Boot writes: 5009")
        print(f"  Post-boot writes: {len(vram_writes) - 5009}")
    else:
        print(f"\nNo VRAM writes after boot")
        print(f"  Game is stuck on copyright screen")

    print(f"\nFinal screen: {last_pixels:,} pixels")


if __name__ == '__main__':
    wait_for_title()
