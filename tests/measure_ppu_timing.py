"""
Measure actual PPU timing to verify if it matches expected 456 cycles per scanline
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def measure_ppu_timing():
    cpu = CPU()

    # Initialize minimal ROM
    for i in range(0x100):
        cpu.memory.write_byte(i, 0x00)  # Fill with NOPs

    # Make sure LCD is enabled
    cpu.memory.write_byte(0xFF40, 0x91)  # LCDC

    print("Measuring PPU timing...")
    print("Expected: 456 T-cycles per scanline")
    print()

    # Measure cycles for LY to increment from 0 to 1
    ly_increments = []

    for test_num in range(5):
        # Wait for LY to be 0
        while cpu.memory.read_byte(0xFF44) != 0:
            cpu.step()

        start_cycles = cpu.total_cycles
        start_ly = cpu.memory.read_byte(0xFF44)

        # Wait for LY to increment
        while cpu.memory.read_byte(0xFF44) == start_ly:
            cpu.step()

        end_cycles = cpu.total_cycles
        end_ly = cpu.memory.read_byte(0xFF44)

        cycles_elapsed = end_cycles - start_cycles

        ly_increments.append({
            'from': start_ly,
            'to': end_ly,
            'cycles': cycles_elapsed
        })

        print(f"Test {test_num+1}: LY {start_ly}->{end_ly} took {cycles_elapsed} cycles")

    print()
    print("=" * 80)
    avg_cycles = sum(inc['cycles'] for inc in ly_increments) / len(ly_increments)
    print(f"Average cycles per LY increment: {avg_cycles:.1f}")
    print(f"Expected: 456")
    print(f"Ratio (actual/expected): {avg_cycles/456:.4f}")
    print("=" * 80)

    if abs(avg_cycles - 456) > 10:
        print(f"\n*** BUG DETECTED: PPU timing is off by {avg_cycles - 456:.1f} cycles! ***")
    else:
        print("\nPPU timing looks correct!")

if __name__ == "__main__":
    measure_ppu_timing()
