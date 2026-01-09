"""
Find the REAL test number encoding that happens between tests

We now know:
- PC=0x0652 happens BEFORE test 01 starts (at cycle 1.5M, test starts at 1.51M)
- Tests 01 and 02 complete successfully
- So there must be ANOTHER encoding routine that runs between tests

Let's find where B register is used to encode test numbers BETWEEN test completions.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def find_real_encoding():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print("Finding real test encoding routine...")
    print()

    # Run to just after test 01 completes
    print("Running to test 01 completion...")
    while cpu.total_cycles < 10_950_000:
        cpu.step()

    print(f"At cycle {cpu.total_cycles:,}")
    print(f"B register: 0x{cpu.registers._b:02X}")
    print(f"BC register: 0x{cpu.registers.bc:04X}")
    print()
    print("=" * 80)
    print("TRACKING B REGISTER AFTER TEST 01, BEFORE TEST 02")
    print("=" * 80)
    print()

    last_serial_len = len(cpu.memory._serial_output)
    b_changes = []

    try:
        while cpu.total_cycles < 12_400_000:  # Up to just after test 02 starts
            pc_before = cpu.registers._pc
            b_before = cpu.registers._b

            cpu.step()

            b_after = cpu.registers._b

            # Track B changes
            if b_before != b_after:
                from src.opcodes import OPCODES
                opcode = cpu.memory.read_byte(pc_before)
                instr_name = OPCODES.get(opcode, ["UNKNOWN"])[0] if opcode in OPCODES else f"0x{opcode:02X}"

                entry = f"[{cpu.total_cycles:>12,}] PC=0x{pc_before:04X}: {instr_name:20} | B: 0x{b_before:02X} -> 0x{b_after:02X}"
                b_changes.append(entry)
                print(entry)

            # Check serial
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                new_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in new_bytes)
                print()
                print(f"[{cpu.total_cycles:>12,}] >>> SERIAL: {repr(new_str)}")
                print()
                last_serial_len = current_serial_len

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print(f"Total B changes: {len(b_changes)}")
    print("=" * 80)

if __name__ == "__main__":
    find_real_encoding()
