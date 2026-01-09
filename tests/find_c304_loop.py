"""
Find when we start looping at 0xC304
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

def find_loop():
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

    # Count how many times we hit 0xC304
    c304_count = 0
    last_20_pcs = []

    for _ in range(500000):
        pc = cpu.registers._pc
        last_20_pcs.append(pc)
        if len(last_20_pcs) > 20:
            last_20_pcs.pop(0)

        if pc == 0xC304:
            c304_count += 1
            if c304_count == 1:
                print(f"First time at 0xC304 at cycle {cpu.total_cycles:,}")
                print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
                print(f"  Previous 20 PCs:")
                for i, p in enumerate(last_20_pcs[:-1]):
                    opcode = cpu.memory.read_byte(p)
                    op_name = OPCODES.get(opcode, ["??"])[0]
                    print(f"    [{i:>2}] 0x{p:04X}: {op_name}")
                print()

            elif c304_count >= 5:
                print(f"Hit 0xC304 {c304_count} times - appears to be looping")
                print(f"  Current state:")
                print(f"    A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
                print(f"    BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")

                # Trace the loop
                print(f"\n  Tracing 10 instructions from 0xC304:")
                for i in range(10):
                    pc = cpu.registers._pc
                    opcode = cpu.memory.read_byte(pc)
                    op_name = OPCODES.get(opcode, ["??"])[0]
                    a = cpu.registers._a
                    f = get_f_register(cpu.registers.flags)

                    cpu.step()

                    pc_after = cpu.registers._pc
                    a_after = cpu.registers._a
                    f_after = get_f_register(cpu.registers.flags)

                    print(f"    [{i}] 0x{pc:04X}: {opcode:02X} {op_name:15} A:0x{a:02X}->0x{a_after:02X} F:0x{f:02X}->0x{f_after:02X} -> 0x{pc_after:04X}")

                break

        cpu.step()

    if c304_count == 0:
        print("Never reached 0xC304")

if __name__ == "__main__":
    find_loop()
