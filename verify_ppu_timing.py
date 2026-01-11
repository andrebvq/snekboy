"""
Verify PPU timing is correct (~70224 cycles/frame at 60 Hz)
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

def verify_timing():
    """Verify PPU frame timing"""
    print("="*70)
    print("PPU TIMING VERIFICATION")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Track VBlank interrupts and their cycles
    vblank_cycles = []

    last_if = cpu.memory._data[0xFF0F]

    # Run for 10 frames
    print("\nTracking VBlank interrupts for 10 frames...")

    frame_count = 0
    while frame_count < 10:
        cpu.step()

        # Detect VBlank interrupt
        current_if = cpu.memory._data[0xFF0F]
        if (current_if & 0x01) and not (last_if & 0x01):
            vblank_cycles.append(cpu.total_cycles)
            frame_count += 1
            print(f"  Frame {frame_count}: VBlank at cycle {cpu.total_cycles:,}")
        last_if = current_if

    # Calculate frame durations
    print(f"\nFrame Durations:")
    for i in range(1, len(vblank_cycles)):
        duration = vblank_cycles[i] - vblank_cycles[i-1]
        print(f"  Frame {i}: {duration} cycles")

    # Expected: ~70224 cycles/frame
    # Actual Game Boy: 154 scanlines * 456 cycles = 70224 cycles
    # At 4.194304 MHz: 70224 / 4194304 = 0.01675 seconds = 59.73 Hz

    if len(vblank_cycles) > 1:
        avg_duration = sum(vblank_cycles[i] - vblank_cycles[i-1]
                          for i in range(1, len(vblank_cycles))) / (len(vblank_cycles) - 1)

        print(f"\nAverage frame duration: {avg_duration:.1f} cycles")
        print(f"Expected: 70224 cycles (154 lines * 456 cycles/line)")

        diff = abs(avg_duration - 70224)
        if diff < 100:
            print(f"Timing: ACCURATE (within {diff:.1f} cycles)")
        else:
            print(f"Timing: OFF by {diff:.1f} cycles")

        # Calculate effective frame rate
        cpu_freq = 4_194_304  # Hz
        frame_rate = cpu_freq / avg_duration
        print(f"\nEffective frame rate: {frame_rate:.2f} Hz")
        print(f"Expected: 59.73 Hz")

    # Check LY register updates
    print(f"\nChecking LY register updates...")
    ly_values = []
    for _ in range(1000):
        ly = cpu.memory.read_byte(0xFF44)
        ly_values.append(ly)
        cpu.step()

    unique_ly = sorted(set(ly_values))
    print(f"  LY values seen: {len(unique_ly)} unique values")
    print(f"  Range: {min(ly_values)} to {max(ly_values)}")
    print(f"  Expected: 0 to 153")

    if max(ly_values) >= 153:
        print(f"  LY updates: CORRECT")
    else:
        print(f"  LY updates: INCOMPLETE (max LY = {max(ly_values)})")


if __name__ == '__main__':
    verify_timing()
