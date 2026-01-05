"""
Disassemble around 0x0208 where 0xC300 writes happen
"""

from src.cpu import CPU
from src.opcodes import OPCODES

def disassemble():
    cpu = CPU()

    # Load ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Disassembling around 0x0200:")
    print("=" * 70)

    addr = 0x01F0
    while addr < 0x0220:
        opcode = cpu.memory.read_byte(addr)

        marker = " <--" if addr == 0x0208 else ""

        if opcode in OPCODES:
            name, length, cycles, flags = OPCODES[opcode]
            hex_bytes = " ".join([f"{cpu.memory.read_byte(addr+i):02X}" for i in range(length)])
            operands = [cpu.memory.read_byte(addr + i) for i in range(1, length)]
            operand_str = ",".join([f"0x{op:02X}" for op in operands]) if operands else ""
            print(f"0x{addr:04X}:  {hex_bytes:12s}  {name:20s} {operand_str}{marker}")
            addr += length
        elif opcode == 0xCB:
            cb_op = cpu.memory.read_byte(addr + 1)
            print(f"0x{addr:04X}:  CB {cb_op:02X}         CB PREFIX{marker}")
            addr += 2
        else:
            print(f"0x{addr:04X}:  {opcode:02X}            [UNKNOWN]{marker}")
            addr += 1

    print("=" * 70)

if __name__ == '__main__':
    disassemble()
