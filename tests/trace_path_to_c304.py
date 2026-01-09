"""
Trace execution path to see how we get to 0xC304 and what actually executes there
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

def trace_to_c304():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Run until test 03 starts
    last_serial_len = 0
    while cpu.total_cycles < 30_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if '03' in full_serial:
                print(f"Test 03 started at cycle {cpu.total_cycles:,}\n")
                break
            last_serial_len = current_serial_len
        cpu.step()

    # Now trace execution until we reach 0xC304, recording the path
    print("Tracing execution until PC=0xC304...")
    print("=" * 80)

    pc_history = []
    iterations = 0
    max_iterations = 50000

    while iterations < max_iterations and cpu.registers._pc != 0xC304:
        pc = cpu.registers._pc

        # Record PC in high RAM area (0xC000+)
        if pc >= 0xC000:
            pc_history.append(pc)
            if len(pc_history) > 100:
                pc_history.pop(0)

        cpu.step()
        iterations += 1

    if cpu.registers._pc == 0xC304:
        print(f"Reached 0xC304 after {iterations:,} instructions")
        print(f"\nLast 50 PCs before reaching 0xC304:")
        for i, pc in enumerate(pc_history[-50:]):
            opcode = cpu.memory.read_byte(pc)
            op_name = OPCODES.get(opcode, ["??"])[0]
            print(f"  [{i:>2}] 0x{pc:04X}: {opcode:02X} {op_name}")

        print(f"\nCurrent state at 0xC304:")
        print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
        print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")

        # Now trace what happens AT 0xC304
        print(f"\nExecuting at 0xC304...")
        opcode = cpu.memory.read_byte(0xC304)
        byte1 = cpu.memory.read_byte(0xC305)
        byte2 = cpu.memory.read_byte(0xC306)
        op_name = OPCODES.get(opcode, ["??"])[0]
        print(f"  Opcode: 0x{opcode:02X} ({op_name}), bytes: {opcode:02X} {byte1:02X} {byte2:02X}")

        # Execute it
        cpu.step()

        print(f"  After execution:")
        print(f"    PC=0x{cpu.registers._pc:04X}")
        print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")

        # Trace next 20 instructions
        print(f"\nNext 20 instructions:")
        for i in range(20):
            pc = cpu.registers._pc
            opcode = cpu.memory.read_byte(pc)
            op_name = OPCODES.get(opcode, ["??"])[0]
            a = cpu.registers._a
            f = get_f_register(cpu.registers.flags)

            cpu.step()

            pc_after = cpu.registers._pc
            a_after = cpu.registers._a
            f_after = get_f_register(cpu.registers.flags)

            print(f"  [{i:>2}] 0x{pc:04X}: {opcode:02X} {op_name:15} A:0x{a:02X}->0x{a_after:02X} F:0x{f:02X}->0x{f_after:02X} -> PC=0x{pc_after:04X}")

            # Check if we're stuck in a loop
            if pc_after == pc or pc_after == 0xC304:
                print(f"  *** Looping back to 0x{pc_after:04X} ***")
                break

    else:
        print(f"Did not reach 0xC304 after {max_iterations:,} instructions")

if __name__ == "__main__":
    trace_to_c304()
