"""
Trace the code at 0x0228 that keeps calling the delay loop
to understand what it's waiting for
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def trace_caller():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Disassemble around 0x0228
    print("=" * 80)
    print("Disassembly around 0x0220-0x0250 (caller of delay loop)")
    print("=" * 80)

    pc = 0x0220
    while pc < 0x0250:
        opcode = cpu.memory.read_byte(pc)
        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
            length = 2
        else:
            instr_info = OPCODES.get(opcode, ["??", 1])
            instr_name = instr_info[0]
            length = instr_info[1]

        operands = []
        for i in range(1, length):
            operands.append(cpu.memory.read_byte(pc + i))

        bytes_str = f"{opcode:02X}"
        for op in operands:
            bytes_str += f" {op:02X}"
        bytes_str = bytes_str.ljust(12)

        operands_str = " ".join(f"0x{op:02X}" for op in operands) if operands else ""

        marker = " <-- Return from delay" if pc == 0x0228 else ""
        print(f"  0x{pc:04X}: {bytes_str} {instr_name:20} {operands_str}{marker}")

        pc += length

    print()
    print("=" * 80)
    print("Running until 0x0228 and tracing execution...")
    print("=" * 80)

    # Run until we hit 0x0228
    while cpu.total_cycles < 30_000_000 and cpu.registers._pc != 0x0228:
        cpu.step()

    print(f"\nReached 0x0228 at cycle {cpu.total_cycles:,}")
    print(f"Registers: A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
    print()

    # Trace next 100 instructions to see the loop pattern
    print("Tracing next 100 instructions:")
    for i in range(100):
        pc_trace = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc_trace)

        # Get instruction name
        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc_trace + 1)
            instr_name = f"CB {cb_opcode:02X}"
        else:
            instr_name = OPCODES.get(opcode, ["??"])[0]

        # Get state
        a_before = cpu.registers._a

        cpu.step()

        pc_after = cpu.registers._pc
        a_after = cpu.registers._a

        # Only print non-delay-loop instructions or state changes
        if pc_trace < 0x0213 or pc_trace > 0x0215 or a_before != a_after:
            a_change = f" A:0x{a_before:02X}->0x{a_after:02X}" if a_before != a_after else ""
            print(f"  [{i+1:>3}] 0x{pc_trace:04X}: {instr_name:20} -> PC=0x{pc_after:04X}{a_change}")

        # Check for interesting conditions
        if pc_trace == 0x0228:  # Back at the caller
            print(f"    >>> Returned to 0x0228 (iteration complete)")

if __name__ == "__main__":
    trace_caller()
