"""
Detailed execution trace around when test 03 fails
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def get_f_register(flags):
    f = 0
    if flags.zero: f |= 0x80
    if flags.subtract: f |= 0x40
    if flags.half_carry: f |= 0x20
    if flags.carry: f |= 0x10
    return f

def trace_detail():
    cpu = CPU()

    rom_path = "test_roms/03-op_sp_hl.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Run until after "E8 E8 F8 F8" is printed
    print("Running until 'E8 E8 F8 F8' is printed...")
    last_serial_len = 0
    while cpu.total_cycles < 20_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            current_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if 'F8' in current_serial and current_serial.count('F8') >= 2:
                print(f"Found 'F8' twice at cycle {cpu.total_cycles:,}")
                print(f"Serial so far: {current_serial}")
                break
            last_serial_len = current_serial_len
        cpu.step()

    # Now trace the next 1000 instructions in detail
    print(f"\nTracing next 1000 instructions from cycle {cpu.total_cycles:,}:")
    print("=" * 80)

    for i in range(1000):
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
        else:
            op_info = OPCODES.get(opcode, ["??", 0, 0])
            instr_name = op_info[0]

        a = cpu.registers._a
        f = get_f_register(cpu.registers.flags)
        bc = cpu.registers.bc
        de = cpu.registers.de
        hl = cpu.registers.hl
        sp = cpu.registers._sp

        # Check serial output
        current_serial_len = len(cpu.memory._serial_output)
        serial_change = ""
        if current_serial_len > last_serial_len:
            new_bytes = cpu.memory._serial_output[last_serial_len:current_serial_len]
            new_chars = ''.join(chr(b) if 32 <= b < 127 else f'<{b:02X}>' for b in new_bytes)
            serial_change = f"  SERIAL: '{new_chars}'"
            last_serial_len = current_serial_len

        # Execute
        cpu.step()

        pc_after = cpu.registers._pc
        a_after = cpu.registers._a
        f_after = get_f_register(cpu.registers.flags)

        # Only print interesting instructions or serial changes
        if serial_change or opcode in [0xE8, 0xF8, 0x33, 0x3B, 0x08, 0xCD, 0xC3, 0xC9] or pc >= 0xC000:
            print(f"[{i:>3}] PC=0x{pc:04X}: {opcode:02X} {instr_name:15} A=0x{a:02X}->0x{a_after:02X} F=0x{f:02X}->0x{f_after:02X} SP=0x{sp:04X}{serial_change}")

        # Stop if we see "Failed"
        if last_serial_len > 0:
            current_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if 'Failed' in current_serial:
                print(f"\n'Failed' detected at instruction {i}")
                print(f"Current state:")
                print(f"  PC=0x{cpu.registers._pc:04X}")
                print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
                print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
                break

if __name__ == "__main__":
    trace_detail()
