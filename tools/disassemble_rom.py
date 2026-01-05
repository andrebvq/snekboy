"""
Disassemble Game Boy ROM to see what instructions it uses

This helps identify which opcodes you need to implement.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.opcodes import OPCODES, CB_OPCODES

def disassemble_rom(rom_path, start=0x0100, count=50):
    """
    Disassemble first N instructions from ROM

    Args:
        rom_path: Path to ROM file
        start: Starting address (default 0x0100 - cartridge entry point)
        count: Number of instructions to disassemble
    """
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    print(f"\n{'='*70}")
    print(f"Disassembling: {rom_path}")
    print(f"Starting at: 0x{start:04X}")
    print(f"{'='*70}\n")
    print(f"{'Address':<8} {'Opcode':<8} {'Bytes':<15} {'Instruction':<20} {'Len':<5} {'Cycles'}")
    print("-" * 70)

    pc = start
    instructions_shown = 0
    unknown_opcodes = set()

    while instructions_shown < count and pc < len(rom_data):
        opcode = rom_data[pc]

        # Check if opcode exists
        if opcode == 0xCB:
            # CB-prefixed instruction
            if pc + 1 < len(rom_data):
                cb_opcode = rom_data[pc + 1]
                if cb_opcode in CB_OPCODES:
                    info = CB_OPCODES[cb_opcode]
                    name, length, cycles = info[0], info[1], info[2]
                    bytes_str = f"{opcode:02X} {cb_opcode:02X}"
                    print(f"0x{pc:04X}   0x{opcode:02X}CB   {bytes_str:<15} {name:<20} {length:<5} {cycles}")
                    pc += length
                else:
                    print(f"0x{pc:04X}   0x{opcode:02X}CB   {opcode:02X} {cb_opcode:02X}     UNKNOWN CB:{cb_opcode:02X}        ?     ?")
                    unknown_opcodes.add(f"CB_{cb_opcode:02X}")
                    pc += 2
            else:
                pc += 1

        elif opcode in OPCODES:
            info = OPCODES[opcode]
            name, length, cycles = info[0], info[1], info[2]

            # Read operand bytes
            operand_bytes = []
            for i in range(1, length):
                if pc + i < len(rom_data):
                    operand_bytes.append(rom_data[pc + i])

            # Format bytes
            bytes_str = f"{opcode:02X}"
            if operand_bytes:
                bytes_str += " " + " ".join(f"{b:02X}" for b in operand_bytes)

            # Format instruction with operands
            instruction_str = name
            if length == 2 and operand_bytes:
                instruction_str = name.replace('n', f"${operand_bytes[0]:02X}")
            elif length == 3 and len(operand_bytes) >= 2:
                word = operand_bytes[0] | (operand_bytes[1] << 8)
                instruction_str = name.replace('nn', f"${word:04X}")

            print(f"0x{pc:04X}   0x{opcode:02X}     {bytes_str:<15} {instruction_str:<20} {length:<5} {cycles}")
            pc += length

        else:
            # Unknown opcode
            print(f"0x{pc:04X}   0x{opcode:02X}     {opcode:02X}             ❌ UNKNOWN: 0x{opcode:02X}  ?     ?")
            unknown_opcodes.add(f"0x{opcode:02X}")
            pc += 1

        instructions_shown += 1

    # Summary
    print("\n" + "="*70)
    if unknown_opcodes:
        print(f"\n❌ UNKNOWN OPCODES FOUND: {len(unknown_opcodes)}")
        print("You need to implement these:\n")
        for op in sorted(unknown_opcodes):
            print(f"  - {op}")
        print("\nUse this to look them up: https://gbdev.io/gb-opcodes/optables/")
    else:
        print("✅ All opcodes in this range are implemented!")
    print()

if __name__ == '__main__':
    rom_path = 'test_roms/cpu_instrs.gb'

    if len(sys.argv) > 1:
        rom_path = sys.argv[1]

    if not os.path.exists(rom_path):
        print(f"Error: ROM file not found: {rom_path}")
        print("Usage: python disassemble_rom.py [rom_path]")
        sys.exit(1)

    disassemble_rom(rom_path, start=0x0100, count=50)
