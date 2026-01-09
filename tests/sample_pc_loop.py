"""
Sample PC values to understand the loop that test 03 is stuck in
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def sample_pc_loop():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until test 03 starts...")

    # Run until test 03 starts (serial shows "03")
    last_serial_len = 0
    test_03_started = False

    while cpu.total_cycles < 30_000_000 and not test_03_started:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            # Check accumulated serial output for "03"
            full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if '03' in full_serial and '02:ok' in full_serial:
                test_03_started = True
                print(f"Test 03 started at cycle {cpu.total_cycles:,}")
                print()
                break
            last_serial_len = current_serial_len
        cpu.step()

    if not test_03_started:
        print("Test 03 did not start")
        return

    # Now sample PC values for the next 1000 instructions
    print("Sampling next 1000 PC values:")
    print("=" * 80)

    pc_counts = {}
    for i in range(1000):
        pc = cpu.registers._pc
        pc_counts[pc] = pc_counts.get(pc, 0) + 1
        cpu.step()

    print("PC frequency distribution (top 20):")
    sorted_pcs = sorted(pc_counts.items(), key=lambda x: x[1], reverse=True)
    for pc, count in sorted_pcs[:20]:
        pct = (count / 1000) * 100
        print(f"  0x{pc:04X}: {count:>4} times ({pct:>5.1f}%)")

    print("=" * 80)
    print()

    # Check for specific loop pattern
    print("Checking for loop pattern...")
    print("Next 30 PC values:")
    pcs = []
    for i in range(30):
        pc = cpu.registers._pc
        pcs.append(pc)
        cpu.step()

    for i, pc in enumerate(pcs):
        print(f"  [{i+1:>2}] 0x{pc:04X}")

    # Look for repeating pattern
    print()
    print("Looking for repeating pattern...")
    for pattern_len in [5, 10, 15, 20]:
        if len(pcs) >= pattern_len * 2:
            pattern1 = pcs[:pattern_len]
            pattern2 = pcs[pattern_len:pattern_len*2]
            if pattern1 == pattern2:
                print(f"Found repeating pattern of length {pattern_len}!")
                print(f"Pattern: {[f'0x{pc:04X}' for pc in pattern1]}")
                break

if __name__ == "__main__":
    sample_pc_loop()
