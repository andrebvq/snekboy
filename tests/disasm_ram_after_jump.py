"""
Disassemble RAM after the test jumps to 0xC000 to look for CRC-like code
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def disasm_ram():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until JP 0xC000...")

    # Run until we jump to 0xC000
    while cpu.total_cycles < 30_000_000:
        if cpu.registers._pc == 0xC000:
            print(f"Jumped to RAM at cycle {cpu.total_cycles:,}")
            break
        cpu.step()

    # Execute a few more instructions to let setup complete
    for _ in range(100):
        cpu.step()

    print()
    print("=" * 80)
    print("Disassembling RAM 0xC000-0xC0FF (looking for CRC patterns)")
    print("=" * 80)

    pc = 0xC000
    while pc < 0xC100:
        opcode = cpu.memory.read_byte(pc)

        if opcode == 0xCB:
            cb_opcode = cpu.memory.read_byte(pc + 1)
            cb_names = {
                0x1F: "RR A", 0x1E: "RR (HL)", 0x19: "RR C",
                0x17: "RL A", 0x16: "RL (HL)", 0x11: "RL C",
                0x07: "RLC A", 0x0F: "RRC A",
            }
            instr_name = cb_names.get(cb_opcode, f"CB {cb_opcode:02X}")
            length = 2
        else:
            instr_info = OPCODES.get(opcode, ["??", 1])
            instr_name = instr_info[0]
            length = instr_info[1]

        # Get operand bytes
        operands = []
        for i in range(1, length):
            operands.append(cpu.memory.read_byte(pc + i))

        # Format
        bytes_str = f"{opcode:02X}"
        for op in operands:
            bytes_str += f" {op:02X}"
        bytes_str = bytes_str.ljust(12)

        operands_str = " ".join(f"0x{op:02X}" for op in operands) if operands else ""

        # Highlight CRC-like patterns
        marker = ""
        if opcode == 0xAF:  # XOR A (common CRC init)
            marker = " <-- XOR A (CRC init?)"
        elif opcode == 0xCB and cb_opcode in [0x1F, 0x19, 0x1A, 0x1B]:  # RR ops
            marker = " <-- Rotation (CRC?)"
        elif opcode in [0xA8, 0xA9, 0xAA, 0xAB, 0xAC, 0xAD, 0xAE, 0xAF]:  # XOR
            marker = " <-- XOR (CRC?)"
        elif opcode == 0xEE:  # XOR n
            marker = " <-- XOR n (CRC?)"

        print(f"  0x{pc:04X}: {bytes_str} {instr_name:20} {operands_str}{marker}")

        pc += length

        if pc >= 0xC100:
            break

    print()
    print("=" * 80)
    print("Looking for CRC-like loop patterns...")
    print("=" * 80)

    # Look for specific patterns
    ram_bytes = [cpu.memory.read_byte(addr) for addr in range(0xC000, 0xC100)]

    # Pattern: AF (XOR A) followed by rotation/XOR loop
    for i, byte in enumerate(ram_bytes):
        if byte == 0xAF:  # XOR A
            # Check next few bytes for CRC pattern
            next_10 = ram_bytes[i:min(i+15, len(ram_bytes))]
            if 0xCB in next_10 and 0xEE in next_10:
                print(f"  Possible CRC at 0x{0xC000+i:04X}: XOR A followed by CB and XOR n within 15 bytes")

if __name__ == "__main__":
    disasm_ram()
