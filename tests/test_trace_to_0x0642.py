"""
Trace execution from after " 03" is printed to PC=0x0642
to see the exact path taken
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run until " 03" is printed
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        print(f"Test 03 started, B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X}")
        break

# Now trace the next 200 instructions showing PC and instruction
print("\nTracing to PC=0x0642...")
print("="*80)

for i in range(200):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    b = cpu.registers._b
    c = cpu.registers._c

    if opcode in OPCODES:
        name = OPCODES[opcode][0]
        length = OPCODES[opcode][1]
        operands = [cpu.memory.read_byte(pc + j + 1) for j in range(length - 1)]
        op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
        instr = f"{name}{op_str}"
    else:
        instr = f"[0x{opcode:02X}]"

    # Highlight key instructions
    highlight = ""
    if opcode == 0x41:  # LD B,C
        highlight = " <<<< LD B,C"
    elif opcode == 0x04:  # INC B
        highlight = " <<<< INC B"
    elif pc == 0x0642:
        highlight = " <<<< TARGET: LD A,B"
    elif pc == 0x067D:
        highlight = " <<<< AT INC B location"

    print(f"[{i:3d}] PC=0x{pc:04X} {instr:30s} | B=0x{b:02X} C=0x{c:02X}{highlight}")

    cpu.step()

    if pc == 0x0642:
        print(f"\n{'='*80}")
        print(f"Reached target!")
        print(f"Final B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X}")
        print(f"{'='*80}")
        break

