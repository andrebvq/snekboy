"""
Trace to address 0xDEF8 where test 03 SP/HL instructions are tested

According to Reddit post, test 03 tests opcodes at 0xDEF8
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

    print("Searching for PC=0xDEF8 (where test 03 tests SP/HL instructions)...")
    print()

    last_serial_len = 0

    while cpu.total_cycles < 20_000_000:
        pc_before = cpu.registers._pc

        # Check if we reached the test address
        if pc_before == 0xDEF8:
            print(f"\n{'='*80}")
            print(f"FOUND: PC=0xDEF8 at cycle {cpu.total_cycles:,}")
            print(f"{'='*80}\n")

            # Trace next 50 instructions
            for i in range(50):
                pc = cpu.registers._pc
                opcode = cpu.memory.read_byte(pc)

                from src.opcodes import OPCODES
                instr_info = OPCODES.get(opcode, ["UNKNOWN", 1, 4, (0,0,0,0)])
                instr_name = instr_info[0]

                print(f"[{cpu.total_cycles:>12,}] PC=0x{pc:04X}: 0x{opcode:02X} {instr_name}")

                cpu.step()

            return

        cpu.step()

        # Check serial
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:]
            serial_str = ''.join(chr(b) if 32 <= b < 127 else '' for b in new_bytes)
            if serial_str.strip():
                print(f"[{cpu.total_cycles:>12,}] SERIAL: {repr(serial_str)}")
            last_serial_len = current_serial_len

    print("\nDid not reach PC=0xDEF8 within 20M cycles")
    print(f"Final PC: 0x{cpu.registers._pc:04X}")
    serial_output = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
    print(f"Final output: {repr(serial_output)}")

if __name__ == "__main__":
    trace()
