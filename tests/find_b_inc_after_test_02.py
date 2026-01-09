"""Find where B should be incremented after test 02"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def find_inc_after_test_02():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print("Running to test 02 completion...")

    # Run to just after test 02 completes
    while cpu.total_cycles < 12_300_000:
        cpu.step()

    print(f"At cycle {cpu.total_cycles:,}")
    print(f"B register: 0x{cpu.registers._b:02X}")
    print()
    print("=" * 80)
    print("TRACKING B REGISTER AFTER TEST 02")
    print("=" * 80)
    print()

    last_serial_len = len(cpu.memory._serial_output)

    try:
        while cpu.total_cycles < 13_000_000:
            pc_before = cpu.registers._pc
            b_before = cpu.registers._b

            cpu.step()

            b_after = cpu.registers._b

            # Track B changes, especially INC B at PC=0x067D
            if b_before != b_after:
                from src.opcodes import OPCODES
                opcode = cpu.memory.read_byte(pc_before)
                instr_name = OPCODES.get(opcode, ["UNKNOWN"])[0] if opcode in OPCODES else f"0x{opcode:02X}"

                entry = f"[{cpu.total_cycles:>12,}] PC=0x{pc_before:04X}: {instr_name:20} | B: 0x{b_before:02X} -> 0x{b_after:02X}"
                print(entry)

                # Highlight INC B at 0x067D (the test counter increment)
                if pc_before == 0x067D and opcode == 0x04:  # INC B
                    print(f"    ^^^ TEST COUNTER INCREMENT!")

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

if __name__ == "__main__":
    find_inc_after_test_02()
