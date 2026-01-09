"""
Trace the first few thousand instructions of test 03 to see where it diverges
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def trace_test03():
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

    def get_f_register(flags):
        f = 0
        if flags.zero: f |= 0x80
        if flags.subtract: f |= 0x40
        if flags.half_carry: f |= 0x20
        if flags.carry: f |= 0x10
        return f

    print(f"Current state:")
    print(f"  PC=0x{cpu.registers._pc:04X}")
    print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
    print()

    # Trace next 500 instructions with register changes
    print("Tracing next 500 instructions (showing register changes)...")
    print("=" * 80)

    for i in range(500):
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
        else:
            instr_name = OPCODES.get(opcode, ["??"])[0]

        # Save state
        a_before = cpu.registers._a
        f_before = cpu.registers.f
        bc_before = cpu.registers.bc
        de_before = cpu.registers.de
        hl_before = cpu.registers.hl
        sp_before = cpu.registers._sp

        # Execute
        cpu.step()

        # Check changes
        pc_after = cpu.registers._pc
        changes = []

        if cpu.registers._a != a_before:
            changes.append(f"A:0x{a_before:02X}->0x{cpu.registers._a:02X}")
        if cpu.registers.f != f_before:
            changes.append(f"F:0x{f_before:02X}->0x{cpu.registers.f:02X}")
        if cpu.registers.bc != bc_before:
            changes.append(f"BC:0x{bc_before:04X}->0x{cpu.registers.bc:04X}")
        if cpu.registers.de != de_before:
            changes.append(f"DE:0x{de_before:04X}->0x{cpu.registers.de:04X}")
        if cpu.registers.hl != hl_before:
            changes.append(f"HL:0x{hl_before:04X}->0x{cpu.registers.hl:04X}")
        if cpu.registers._sp != sp_before:
            changes.append(f"SP:0x{sp_before:04X}->0x{cpu.registers._sp:04X}")

        # Only print if there are changes or control flow
        if changes or opcode in [0xC3, 0xCD, 0xC9, 0xC0, 0xC8, 0xD0, 0xD8, 0xE8, 0xF8]:
            changes_str = " ".join(changes) if changes else ""
            print(f"[{i+1:>3}] 0x{pc:04X}: {instr_name:20} -> 0x{pc_after:04X}  {changes_str}")

        # Check for ADD SP,e or LD HL,SP+e to verify Z preservation
        if opcode == 0xE8 or opcode == 0xF8:
            z_before = (f_before >> 7) & 1
            z_after = (cpu.registers.f >> 7) & 1
            if z_before != z_after:
                print(f"    *** Z FLAG CHANGED: {z_before} -> {z_after} (BUG!) ***")

        # Check for getting stuck
        if i > 200 and pc == 0xC304:
            print(f"\n*** Stuck at 0xC304, stopping trace ***")
            print(f"Final state:")
            print(f"  A=0x{cpu.registers._a:02X} F=0x{cpu.registers.f:02X}")
            print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
            break

if __name__ == "__main__":
    trace_test03()
