"""
Disassemble the area around the halt instruction
"""

from src.cpu import CPU
from src.opcodes import OPCODES

def disassemble_area():
    cpu = CPU()

    # Load ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Disassembling area around 0xC36F (HALT location):")
    print("=" * 70)

    # Disassemble from 0xC360 to 0xC380
    addr = 0xC360
    while addr < 0xC380:
        opcode = cpu.memory.read_byte(addr)

        if opcode in OPCODES:
            name, length, cycles, flags = OPCODES[opcode]

            # Get operands
            operands = []
            for i in range(1, length):
                operands.append(cpu.memory.read_byte(addr + i))

            # Format instruction
            hex_bytes = " ".join([f"{cpu.memory.read_byte(addr+i):02X}" for i in range(length)])
            operand_str = ",".join([f"0x{op:02X}" for op in operands]) if operands else ""

            print(f"0x{addr:04X}:  {hex_bytes:12s}  {name:20s} {operand_str}")

            addr += length
        else:
            print(f"0x{addr:04X}:  {opcode:02X}           [UNKNOWN OPCODE]")
            addr += 1

    print("=" * 70)

    # Also check what's at some key addresses
    print("\nKey memory locations:")
    print(f"  0xFF01 (SB - Serial Data): 0x{cpu.memory.read_byte(0xFF01):02X}")
    print(f"  0xFF02 (SC - Serial Ctrl): 0x{cpu.memory.read_byte(0xFF02):02X}")
    print(f"  0xFF0F (IF - Int Flags):   0x{cpu.memory.read_byte(0xFF0F):02X}")
    print(f"  0xFFFF (IE - Int Enable):  0x{cpu.memory.read_byte(0xFFFF):02X}")

if __name__ == '__main__':
    disassemble_area()
