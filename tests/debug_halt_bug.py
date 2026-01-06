"""
Debug the halt_bug.gb test to see why it's hanging at PC=0xC41F
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()
cpu.memory.load_rom_file('test_roms/halt_bug.gb')

print("Running halt_bug.gb with instruction trace...")
print("="*80)

# Run for first 1000 instructions to see what's happening
for i in range(1000):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Decode instruction
    if opcode == 0xCB:
        cb_opcode = cpu.memory.read_byte(pc + 1)
        if cb_opcode in OPCODES:
            name = OPCODES[cb_opcode][0]
            instr = f"CB {name}"
        else:
            instr = f"CB [0x{cb_opcode:02X}]"
    elif opcode in OPCODES:
        name = OPCODES[opcode][0]
        length = OPCODES[opcode][1]
        operands = [cpu.memory.read_byte(pc + j + 1) for j in range(length - 1)]
        op_str = " " + ",".join(f"0x{op:02X}" for op in operands) if operands else ""
        instr = f"{name}{op_str}"
    else:
        instr = f"[0x{opcode:02X}] UNKNOWN"

    # Show state
    a = cpu.registers._a
    bc = cpu.registers.bc
    de = cpu.registers.de
    hl = cpu.registers.hl
    sp = cpu.registers._sp

    print(f"[{i:3d}] PC=0x{pc:04X} {instr:30s} | A=0x{a:02X} BC=0x{bc:04X} DE=0x{de:04X} HL=0x{hl:04X} SP=0x{sp:04X}")

    # Check for loops
    if i > 50 and pc == 0xC41F:
        print(f"\n{'='*80}")
        print(f"Detected loop at PC=0x{pc:04X}")
        print(f"Let's see what's around this address:")
        print(f"{'='*80}")

        # Disassemble nearby
        for addr in range(0xC410, 0xC430):
            op = cpu.memory.read_byte(addr)
            if op in OPCODES:
                name = OPCODES[op][0]
                print(f"  0x{addr:04X}: {name}")
            else:
                print(f"  0x{addr:04X}: [0x{op:02X}]")

        break

    try:
        cpu.step()
    except NotImplementedError as e:
        print(f"\n{'='*80}")
        print(f"[ERROR] Unimplemented instruction: {e}")
        print(f"  PC: 0x{pc:04X}")
        print(f"  Opcode: 0x{opcode:02X}")
        print(f"{'='*80}")
        break

print(f"\n\nSerial output: {cpu.memory.get_serial_output()}")
