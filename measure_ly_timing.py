"""
Measure frame timing using LY register wraps (0->153->0)
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

def measure_ly_timing():
    """Measure frame timing using LY wraps"""
    print("="*70)
    print("LY-BASED FRAME TIMING MEASUREMENT")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to stable state (1M cycles)...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    # Wait for LY=0
    while cpu.memory.read_byte(0xFF44) != 0:
        cpu.step()

    # Measure 10 frames
    frame_cycles = []

    print(f"\nMeasuring 10 frames (LY 0->153->0 transitions)...")

    for frame_num in range(10):
        frame_start = cpu.total_cycles
        start_ly = cpu.memory.read_byte(0xFF44)

        # Run until LY wraps back to 0
        steps = 0
        while True:
            cpu.step()
            steps += 1
            ly = cpu.memory.read_byte(0xFF44)

            # Check if we've wrapped (went through 153 and back to 0)
            if ly == 0 and steps > 100:  # Ensure we're not at the same 0
                break

            # Safety check
            if steps > 100_000:
                print(f"ERROR: Frame {frame_num+1} didn't complete in 100k steps!")
                break

        frame_end = cpu.total_cycles
        duration = frame_end - frame_start
        frame_cycles.append(duration)

        print(f"  Frame {frame_num+1}: {duration} cycles ({steps} steps)")

    # Analysis
    print(f"\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    if len(frame_cycles) > 0:
        avg = sum(frame_cycles) / len(frame_cycles)
        min_cycles = min(frame_cycles)
        max_cycles = max(frame_cycles)

        print(f"\nFrame duration statistics:")
        print(f"  Average: {avg:.1f} cycles")
        print(f"  Min: {min_cycles} cycles")
        print(f"  Max: {max_cycles} cycles")
        print(f"  Expected: 70224 cycles (154 lines * 456 cycles/line)")

        diff = avg - 70224
        percent_diff = (diff / 70224) * 100

        if abs(diff) < 100:
            print(f"\n  TIMING: PERFECT (within {abs(diff):.1f} cycles)")
        elif diff > 0:
            print(f"\n  TIMING: TOO SLOW by {diff:.1f} cycles ({percent_diff:+.2f}%)")
        else:
            print(f"\n  TIMING: TOO FAST by {abs(diff):.1f} cycles ({percent_diff:+.2f}%)")

        # Frame rate
        cpu_freq = 4_194_304
        fps = cpu_freq / avg
        print(f"\n  Effective FPS: {fps:.2f} (expected 59.73)")


if __name__ == '__main__':
    measure_ly_timing()
