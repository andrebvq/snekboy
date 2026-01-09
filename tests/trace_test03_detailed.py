"""
Detailed trace of test 03 to find which instruction fails
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_test03():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until test 03 starts...")
    last_serial = ""
    while cpu.total_cycles < 50_000_000:
        current_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)

        if current_serial != last_serial:
            print(f"[Cycle {cpu.total_cycles:,}] {current_serial}")
            last_serial = current_serial

            # Check if test 03 output anything beyond just "03"
            if '03:' in current_serial:
                print(f"\n*** Test 03 completed with output: {current_serial.split('03')[1].split()[0]} ***")
                break

        cpu.step()

    print(f"\nTest stopped at cycle {cpu.total_cycles:,}")
    print(f"Final output: {last_serial}")

if __name__ == "__main__":
    trace_test03()
