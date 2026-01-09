"""
Disassemble the busy-wait loops where test 03 gets stuck
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def disassemble_range(memory, start, end):
    """Disassemble a range of memory"""
    pc = start
    while pc < end:
        opcode = memory.read_byte(pc)
        if opcode == 0xCB:
            cb_opcode = memory.read_byte(pc + 1)
            instr_name = f"CB {cb_opcode:02X}"
            length = 2
        else:
            instr_info = OPCODES.get(opcode, ["??", 1])
            instr_name = instr_info[0]
            length = instr_info[1]

        # Get operand bytes
        operands = []
        for i in range(1, length):
            operands.append(memory.read_byte(pc + i))

        # Format output
        bytes_str = f"{opcode:02X}"
        for op in operands:
            bytes_str += f" {op:02X}"
        bytes_str = bytes_str.ljust(12)

        operands_str = " ".join(f"0x{op:02X}" for op in operands) if operands else ""
        print(f"  0x{pc:04X}: {bytes_str} {instr_name:20} {operands_str}")

        pc += length

def main():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("=" * 80)
    print("Disassembly of busy-wait loop #1 (0x073E-0x0747)")
    print("=" * 80)
    disassemble_range(cpu.memory, 0x073E, 0x0748)

    print()
    print("=" * 80)
    print("Disassembly of busy-wait loop #2 (0x0213-0x021C)")
    print("=" * 80)
    disassemble_range(cpu.memory, 0x0213, 0x021D)

    print()
    print("=" * 80)
    print("Context around 0x0213 (0x0210-0x0220)")
    print("=" * 80)
    disassemble_range(cpu.memory, 0x0210, 0x0220)

    print()
    print("=" * 80)
    print("Context around 0x073E (0x0738-0x0750)")
    print("=" * 80)
    disassemble_range(cpu.memory, 0x0738, 0x0750)

if __name__ == "__main__":
    main()
