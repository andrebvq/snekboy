"""
Run test 03 with extended cycle limit

Test 03 might just require many more cycles than tests 01 & 02.
Let's try with 100M cycles (vs the default 30M).
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def run_test():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Load ROM correctly
    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print(f"Loaded {rom_size} bytes of ROM")
    print()

    max_cycles = 100_000_000  # 100M cycles
    last_serial_len = 0

    print("Running emulation with 100M cycle limit...")
    print()

    try:
        while cpu.total_cycles < max_cycles:
            cpu.step()

            # Check serial output
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                for b in new_bytes:
                    if b == 0x0A:
                        print()
                    elif 32 <= b < 127:
                        print(chr(b), end='', flush=True)
                last_serial_len = current_serial_len

            # Progress indicator every 10M cycles
            if cpu.total_cycles % 10_000_000 == 0:
                serial_output = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
                print(f"\n[{cpu.total_cycles // 1_000_000}M cycles] Current output: {repr(serial_output[-50:])}")

    except KeyboardInterrupt:
        print("\nInterrupted")

    print()
    print("=" * 80)

    # Get full output
    serial_output = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)

    if "01:ok  02:ok  03:ok" in serial_output:
        print("SUCCESS: All tests (01, 02, 03) PASSED!")
        return True
    elif "01:ok  02:ok" in serial_output:
        print(f"PARTIAL: Tests 01 and 02 passed")
        print(f"Final cycle count: {cpu.total_cycles:,}")
        print(f"Final output: {repr(serial_output)}")
        return False
    else:
        print("FAILED: Tests did not complete successfully")
        print(f"Final cycle count: {cpu.total_cycles:,}")
        print(f"Final output: {repr(serial_output)}")
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
