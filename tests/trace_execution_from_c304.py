"""
Trace execution starting from when PC reaches 0xC304

This will show us what actually happens after the JP (HL) to 0xC304
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def trace_from_c304():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until PC=0xC304...")

    # Run until we hit 0xC304
    while cpu.total_cycles < 30_000_000 and cpu.registers._pc != 0xC304:
        cpu.step()

    if cpu.registers._pc != 0xC304:
        print("Did not reach 0xC304")
        return

    print(f"Reached 0xC304 at cycle {cpu.total_cycles:,}")
    print(f"Registers: A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
    print(f"Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
    print()
    print("Tracing next 50 instructions...")
    print("=" * 80)

    for i in range(50):
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        # Get instruction name
        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
        else:
            instr_name = OPCODES.get(opcode, ["??"])[0]

        # Get state before
        a_before = cpu.registers._a
        flags_before = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                      cpu.registers.flags.half_carry, cpu.registers.flags.carry)

        # Execute
        cpu.step()

        # Get state after
        a_after = cpu.registers._a
        pc_after = cpu.registers._pc
        flags_after = (cpu.registers.flags.zero, cpu.registers.flags.subtract,
                     cpu.registers.flags.half_carry, cpu.registers.flags.carry)

        # Log
        changes = []
        if a_before != a_after:
            changes.append(f"A:0x{a_before:02X}->0x{a_after:02X}")
        if flags_before != flags_after:
            changes.append(f"F:{int(flags_before[0])}{int(flags_before[1])}{int(flags_before[2])}{int(flags_before[3])}->{int(flags_after[0])}{int(flags_after[1])}{int(flags_after[2])}{int(flags_after[3])}")

        changes_str = " ".join(changes) if changes else ""
        print(f"[{i+1:>2}] 0x{pc:04X}: {instr_name:20} -> PC=0x{pc_after:04X}  {changes_str}")

        # Check for loops
        if i > 10 and pc == 0xC304 and opcode == 0x00:
            print(f"\n*** PC stuck at 0xC304 executing NOPs (infinite loop) ***")
            break
        if i > 10 and pc_after == pc:
            print(f"\n*** Infinite loop detected at 0x{pc:04X} ***")
            break

    print("=" * 80)

if __name__ == "__main__":
    trace_from_c304()
