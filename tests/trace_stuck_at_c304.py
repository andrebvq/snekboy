"""
Trace execution when stuck at 0xC304 to understand what's happening
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

def trace_stuck():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Run until test 03 serial output
    last_serial_len = 0
    while cpu.total_cycles < 30_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if '03' in full_serial:
                print(f"Test 03 started at cycle {cpu.total_cycles:,}")
                break
            last_serial_len = current_serial_len
        cpu.step()

    print(f"\nCurrent state:")
    print(f"  PC=0x{cpu.registers._pc:04X}")
    print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
    print()

    # Trace until we hit 0xC304 or loop
    print("Tracing until PC=0xC304 or loop detected...")
    print("=" * 80)

    pc_history = []
    iteration = 0

    while iteration < 2000:
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
        else:
            instr_name = OPCODES.get(opcode, ["??"])[0]

        # Print every instruction
        a = cpu.registers._a
        f = get_f_register(cpu.registers.flags)
        bc = cpu.registers.bc
        de = cpu.registers.de
        hl = cpu.registers.hl
        sp = cpu.registers._sp

        if pc == 0xC304 or iteration < 50 or (iteration % 100 == 0):
            print(f"[{iteration:>4}] PC=0x{pc:04X}: {instr_name:20} A=0x{a:02X} F=0x{f:02X} BC=0x{bc:04X} DE=0x{de:04X} HL=0x{hl:04X} SP=0x{sp:04X}")

        # Check if we're stuck in a loop
        if pc == 0xC304:
            if iteration > 100:
                print(f"\n*** STUCK at 0xC304 for {iteration - 100} iterations ***")
                # Disassemble around 0xC304
                print("\nDisassembly around 0xC304:")
                for addr in range(0xC300, 0xC310):
                    op = cpu.memory.read_byte(addr)
                    op_name = OPCODES.get(op, ["??"])[0]
                    byte1 = cpu.memory.read_byte(addr + 1)
                    byte2 = cpu.memory.read_byte(addr + 2)
                    print(f"  0x{addr:04X}: {op:02X} {byte1:02X} {byte2:02X}  {op_name}")
                break

        pc_history.append(pc)
        if len(pc_history) > 100:
            pc_history.pop(0)

        # Detect tight loop
        if pc_history.count(pc) > 10:
            print(f"\n*** Tight loop detected at 0x{pc:04X} ***")
            break

        cpu.step()
        iteration += 1

    print(f"\nFinal state after {iteration} instructions:")
    print(f"  PC=0x{cpu.registers._pc:04X}")
    print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")

    # Check what value is being compared
    print(f"\nMemory at key addresses:")
    print(f"  [0xC304] = 0x{cpu.memory.read_byte(0xC304):02X}")
    print(f"  [0xC305] = 0x{cpu.memory.read_byte(0xC305):02X}")
    print(f"  [0xC306] = 0x{cpu.memory.read_byte(0xC306):02X}")
    print(f"  [0xC307] = 0x{cpu.memory.read_byte(0xC307):02X}")

    # Check CRC result area
    print(f"\nCRC result area (0xFF83-0xFF86):")
    for addr in range(0xFF83, 0xFF87):
        print(f"  [0x{addr:04X}] = 0x{cpu.memory.read_byte(addr):02X}")

if __name__ == "__main__":
    trace_stuck()
