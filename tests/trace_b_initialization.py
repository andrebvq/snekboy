"""
Trace B register initialization for test 03

Find where B=0x30 comes from
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Tracing B register changes...")
    print()

    last_serial_len = 0
    b_changes = []

    while cpu.total_cycles < 13_000_000:
        pc_before = cpu.registers._pc
        b_before = cpu.registers._b

        cpu.step()

        b_after = cpu.registers._b

        # Track B register changes
        if b_before != b_after:
            from src.opcodes import OPCODES
            opcode = cpu.memory.read_byte(pc_before)
            instr = OPCODES.get(opcode, ["??"])[0]

            b_changes.append((cpu.total_cycles, pc_before, instr, b_before, b_after))

            # Print significant B changes
            if len(b_changes) <= 50 or b_after == 0x30:
                print(f"[{cpu.total_cycles:>12,}] PC=0x{pc_before:04X}: {instr:20} | B: 0x{b_before:02X} -> 0x{b_after:02X}")

                if b_after == 0x30:
                    print("    ^^^ B became 0x30!")

        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            print(f"\n[{cpu.total_cycles:>12,}] SERIAL: {repr(serial_str)}")
            print()
            last_serial_len = current_serial_len

            # Stop after test 03 starts
            if '03' in serial_str:
                print(f"Test 03 started. B register is now: 0x{cpu.registers._b:02X}")
                break

    print()
    print("=" * 80)
    print(f"Total B changes: {len(b_changes)}")
    print(f"Final B value: 0x{cpu.registers._b:02X}")
    print("=" * 80)

if __name__ == "__main__":
    trace()
