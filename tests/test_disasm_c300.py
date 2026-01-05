"""
Disassemble around 0xC300 where test 03 halts
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

    # Run until test 03 starts
    print("Running until test 03 starts...")
    last_serial = ""
    while cpu.total_cycles < 15_000_000:
        cpu.step()
        serial = cpu.memory.get_serial_output()
        if serial != last_serial and "03" in serial:
            print(f"Test 03 started at cycle {cpu.total_cycles}")
            last_serial = serial
            break

    print("\nDisassembling around 0xC300:")
    print("=" * 70)

    # Disassemble from 0xC2F0 to 0xC320
    addr = 0xC2F0
    while addr < 0xC320:
        opcode = cpu.memory.read_byte(addr)

        marker = " <--" if addr == 0xC304 else ""

        if opcode in OPCODES:
            name, length, cycles, flags = OPCODES[opcode]
            hex_bytes = " ".join([f"{cpu.memory.read_byte(addr+i):02X}" for i in range(length)])
            operands = [cpu.memory.read_byte(addr + i) for i in range(1, length)]
            operand_str = ",".join([f"0x{op:02X}" for op in operands]) if operands else ""
            print(f"0x{addr:04X}:  {hex_bytes:12s}  {name:20s} {operand_str}{marker}")
            addr += length
        elif opcode == 0x10:  # STOP
            print(f"0x{addr:04X}:  10 00         STOP{marker}")
            addr += 2
        elif opcode == 0xCB:  # CB prefix
            cb_opcode = cpu.memory.read_byte(addr + 1)
            print(f"0x{addr:04X}:  CB {cb_opcode:02X}         CB PREFIX{marker}")
            addr += 2
        else:
            print(f"0x{addr:04X}:  {opcode:02X}            [UNKNOWN]{marker}")
            addr += 1

    print("=" * 70)

if __name__ == '__main__':
    disassemble()
