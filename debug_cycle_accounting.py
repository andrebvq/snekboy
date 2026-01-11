"""
Debug cycle accounting to find timing issue
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

def debug_cycles():
    """Debug cycle accounting"""
    print("="*70)
    print("CYCLE ACCOUNTING DEBUG")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    # Now carefully track cycles for next 100k
    print(f"\nTracking detailed cycle accounting for 100k cycles...")

    start_cycles = cpu.total_cycles
    start_ppu_cycles = cpu.ppu.cycle_counter
    instruction_count = 0

    target = start_cycles + 100_000

    while cpu.total_cycles < target:
        before_cycles = cpu.total_cycles
        cpu.step()
        after_cycles = cpu.total_cycles

        cycles_this_instr = after_cycles - before_cycles
        instruction_count += 1

    end_cycles = cpu.total_cycles
    actual_cycles = end_cycles - start_cycles

    print(f"\nResults:")
    print(f"  Target cycles: 100,000")
    print(f"  Actual cycles: {actual_cycles:,}")
    print(f"  Instructions executed: {instruction_count:,}")
    print(f"  Avg cycles/instruction: {actual_cycles / instruction_count:.2f}")

    # Check PPU state
    print(f"\nPPU State:")
    print(f"  Current mode: {cpu.ppu.current_mode}")
    print(f"  Cycle counter: {cpu.ppu.cycle_counter}")
    print(f"  LY: {cpu.memory.read_byte(0xFF44)}")

    # Count how many scanlines in 70224 cycles
    print(f"\nScanning for full frame...")
    ly_start = cpu.memory.read_byte(0xFF44)
    frame_start = cpu.total_cycles

    # Wait for LY to go from 153 -> 0 (start of new frame)
    while cpu.memory.read_byte(0xFF44) != 0:
        cpu.step()

    while True:
        cpu.step()
        ly = cpu.memory.read_byte(0xFF44)
        if ly == 0 and cpu.total_cycles > frame_start + 10000:
            # We've wrapped around to 0 again
            break

    frame_end = cpu.total_cycles
    frame_duration = frame_end - frame_start

    print(f"  Full frame duration: {frame_duration} cycles")
    print(f"  Expected: 70224 cycles")
    print(f"  Difference: {frame_duration - 70224} cycles")


if __name__ == '__main__':
    debug_cycles()
