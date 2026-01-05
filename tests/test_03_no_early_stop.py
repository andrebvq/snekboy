"""
Run test 03 without stopping early on HALT
"""

from src.cpu import CPU

def run_test():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Running test with no early halt detection...")

    max_cycles = 30_000_000
    last_serial = ""

    try:
        cpu.run_until(max_cycles)

        print(f"Completed {cpu.total_cycles:,} cycles")
        print(f"Final PC: 0x{cpu.registers._pc:04X}")
        print(f"Halted: {cpu.halted}")

        serial = cpu.memory.get_serial_output()
        print(f"\n{'='*60}")
        print("SERIAL OUTPUT:")
        print(f"{'='*60}")
        print(serial)
        print(f"{'='*60}")

        # Check pass/fail
        if "Passed" in serial:
            print("\n[PASS]")
        elif "Failed" in serial:
            print("\n[FAIL]")
        elif ":ok" in serial:
            # Count how many tests passed
            import re
            oks = re.findall(r'\d+:ok', serial)
            numbers = re.findall(r'\d+:', serial)
            print(f"\n[PARTIAL] {len(oks)} test(s) passed out of {len(numbers)} started")
            print(f"  Passed: {oks}")
            print(f"  All results: {numbers}")
        else:
            print("\n[UNKNOWN]")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
