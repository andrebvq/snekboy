"""
Trace execution before reaching STOP at 0xC302
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

def trace_before_stop():
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

    # Run until PC is close to 0xC302
    pc_history = []
    while cpu.total_cycles < 30_000_000:
        pc = cpu.registers._pc
        pc_history.append(pc)
        if len(pc_history) > 100:
            pc_history.pop(0)

        if pc == 0xC302:  # STOP
            print("Reached STOP at 0xC302")
            print(f"Last 50 instructions before STOP:")
            print("=" * 80)

            for i, p in enumerate(pc_history[-50:]):
                opcode = cpu.memory.read_byte(p)
                op_name = OPCODES.get(opcode, ["??"])[0]
                print(f"  [{i:>2}] 0x{p:04X}: {opcode:02X} {op_name}")

            print()
            print(f"State at STOP:")
            print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
            print(f"  BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
            print(f"  Halted: {cpu.halted}")
            print()

            # Check what STOP does
            print("Executing STOP:")
            cpu.step()

            print(f"  After STOP:")
            print(f"    PC=0x{cpu.registers._pc:04X}")
            print(f"    Halted: {cpu.halted}")

            # Check memory around the STOP
            print()
            print(f"Memory around STOP:")
            for addr in range(0xC2F8, 0xC308):
                val = cpu.memory.read_byte(addr)
                if addr == 0xC302:
                    print(f"  [0x{addr:04X}] = 0x{val:02X} <<< STOP HERE")
                else:
                    print(f"  [0x{addr:04X}] = 0x{val:02X}")

            break

        cpu.step()

if __name__ == "__main__":
    trace_before_stop()
