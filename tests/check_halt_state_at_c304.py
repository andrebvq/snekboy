"""
Check if CPU is halted when at 0xC304 and what the interrupt state is
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def get_f_register(flags):
    f = 0
    if flags.zero: f |= 0x80
    if flags.subtract: f |= 0x40
    if flags.half_carry: f |= 0x20
    if flags.carry: f |= 0x10
    return f

def check_halt():
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
                break
            last_serial_len = current_serial_len
        cpu.step()

    # Run until we hit 0xC304
    while cpu.total_cycles < 30_000_000:
        if cpu.registers._pc == 0xC304:
            break
        cpu.step()

    if cpu.registers._pc == 0xC304:
        print(f"At PC=0xC304:")
        print(f"  Halted: {cpu.halted}")
        print(f"  IME: {cpu.ime}")
        print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
        print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
        print(f"  IE (0xFFFF) = 0x{cpu.memory.read_byte(0xFFFF):02X}")
        print(f"  IF (0xFF0F) = 0x{cpu.memory.read_byte(0xFF0F):02X}")

        # Check what's on the stack
        print(f"\n  Stack values:")
        sp = cpu.registers._sp
        for i in range(10):
            addr = sp + i
            val = cpu.memory.read_byte(addr)
            print(f"    [SP+{i}] (0x{addr:04X}) = 0x{val:02X}")

        # Execute POP AF and see what happens
        print(f"\n  Executing POP AF:")
        sp_before = cpu.registers._sp
        pc_before = cpu.registers._pc
        a_before = cpu.registers._a
        f_before = get_f_register(cpu.registers.flags)

        cpu.step()

        sp_after = cpu.registers._sp
        pc_after = cpu.registers._pc
        a_after = cpu.registers._a
        f_after = get_f_register(cpu.registers.flags)

        print(f"    SP: 0x{sp_before:04X} -> 0x{sp_after:04X}")
        print(f"    PC: 0x{pc_before:04X} -> 0x{pc_after:04X}")
        print(f"    A:  0x{a_before:02X} -> 0x{a_after:02X}")
        print(f"    F:  0x{f_before:02X} -> 0x{f_after:02X}")

        # Check if halted after POP
        print(f"    Halted after: {cpu.halted}")

        # Try executing again
        print(f"\n  Executing next instruction:")
        pc_before2 = cpu.registers._pc
        cpu.step()
        pc_after2 = cpu.registers._pc
        print(f"    PC: 0x{pc_before2:04X} -> 0x{pc_after2:04X}")

if __name__ == "__main__":
    check_halt()
