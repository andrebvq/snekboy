"""
Measure LY increment rate during actual test 03 execution
Count CYCLES, not instructions!
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def measure_ly_during_test():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until test 03 starts...")

    # Run until test 03 is in VBlank wait loop
    target_count = 0
    while cpu.total_cycles < 30_000_000:
        if cpu.registers._pc == 0x0743:  # LDH A,(0x44) in VBlank wait
            target_count += 1
            if target_count >= 10:
                break
        cpu.step()

    print(f"In VBlank wait loop at cycle {cpu.total_cycles:,}")
    print()

    # Now measure LY increments by CYCLES
    print("Measuring LY increments by actual T-cycles...")

    for test_num in range(5):
        start_ly = cpu.memory.read_byte(0xFF44)
        start_cycles = cpu.total_cycles

        # Run until LY increments
        while cpu.memory.read_byte(0xFF44) == start_ly and cpu.total_cycles < start_cycles + 10000:
            cpu.step()

        end_ly = cpu.memory.read_byte(0xFF44)
        end_cycles = cpu.total_cycles
        cycles_elapsed = end_cycles - start_cycles

        print(f"Test {test_num+1}: LY {start_ly}->{end_ly} took {cycles_elapsed} T-cycles")

    print()
    print("Expected: 456 T-cycles per LY increment")

if __name__ == "__main__":
    measure_ly_during_test()
