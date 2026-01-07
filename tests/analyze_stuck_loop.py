"""
Analyze what the game is doing when it gets stuck
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until it gets stuck
print("Running until LCD turns off...")
while cpu.total_cycles < 150_000:
    cpu.step()

print(f"\nReached stuck point at PC=0x{cpu.registers._pc:04X}")
print(f"Cycle: {cpu.total_cycles:,}")
print(f"LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
print()

# Disassemble the loop
print("Disassembling stuck loop:")
print("="*80)

for addr in range(0x0260, 0x0280):
    opcode = cpu.memory.read_byte(addr)

    if opcode in OPCODES:
        name, length, cycles, flags = OPCODES[opcode]

        # Get operands
        operands = []
        for i in range(1, length):
            operands.append(cpu.memory.read_byte(addr + i))

        op_str = ""
        if operands:
            if length == 2:
                op_str = f" 0x{operands[0]:02X}"
            elif length == 3:
                op_str = f" 0x{operands[1]:02X}{operands[0]:02X}"

        marker = " <-- STUCK HERE" if addr in [0x026B, 0x026C] else ""
        print(f"  0x{addr:04X}: {name:15s}{op_str:10s} ; {cycles:2d} cycles{marker}")

# Trace the loop in detail
print("\n" + "="*80)
print("Tracing execution:")
print("="*80)

for i in range(20):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    if opcode in OPCODES:
        name = OPCODES[opcode][0]
    else:
        name = f"[0x{opcode:02X}]"

    a = cpu.registers._a
    hl = cpu.registers.hl

    # Check what memory HL points to
    mem_val = cpu.memory.read_byte(hl) if hl < 0x10000 else 0

    print(f"[{i:2d}] PC=0x{pc:04X} {name:15s} | A=0x{a:02X} HL=0x{hl:04X} (HL)=0x{mem_val:02X}")

    cpu.step()

# What is this loop waiting for?
print("\n" + "="*80)
print("Analysis:")
print("="*80)

# The loop is probably: LDI A,(HL) or something waiting for a value
# Let's check what address HL is reading from
hl = cpu.registers.hl
print(f"HL register: 0x{hl:04X}")

if hl >= 0xFF00:
    print(f"  -> This is an I/O register!")

    io_registers = {
        0xFF00: "P1 (Joypad)",
        0xFF01: "SB (Serial data)",
        0xFF02: "SC (Serial control)",
        0xFF04: "DIV",
        0xFF05: "TIMA",
        0xFF06: "TMA",
        0xFF07: "TAC",
        0xFF0F: "IF (Interrupt flags)",
        0xFF40: "LCDC",
        0xFF41: "STAT",
        0xFF42: "SCY",
        0xFF43: "SCX",
        0xFF44: "LY",
        0xFF45: "LYC",
    }

    if hl in io_registers:
        print(f"  -> Reading from {io_registers[hl]}")
        print(f"  -> Current value: 0x{cpu.memory.read_byte(hl):02X}")
