"""
Analyze and test the CRC routine used in Blargg tests

The fast CRC routine is likely the culprit. Let's:
1. Find the CRC routine in the ROM
2. Trace its execution
3. Test the exact instruction sequence
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def find_crc_patterns():
    """Look for CRC-like patterns in the ROM"""

    with open('test_roms/cpu_instrs.gb', 'rb') as f:
        rom = f.read()

    print("Searching for CRC-like patterns in ROM...")
    print()

    # CRC routines typically have:
    # - XOR operations
    # - Rotations (RR, RL)
    # - Loops
    # Look for sequences like: XOR, RR, conditional branch

    # Common CRC pattern: XOR then RR in a loop
    # XOR A,B = 0xA8
    # RR A = CB 1F
    # JR NC,... = 0x30

    patterns = [
        # Pattern 1: XOR followed by CB prefix (rotation)
        (b'\xA8\xCB', "XOR B, then rotation"),
        (b'\xAF\xCB', "XOR A, then rotation"),
        (b'\xEE..\xCB', "XOR n, then rotation"),
        # Pattern 2: RR in sequence
        (b'\xCB\x1F\xCB\x1F', "Double RR A"),
        (b'\xCB\x1F\x30', "RR A, JR NC (CRC loop pattern)"),
    ]

    for pattern_bytes, description in patterns:
        # Simple search
        pos = 0
        matches = []
        while True:
            idx = rom.find(pattern_bytes, pos)
            if idx == -1:
                break
            if idx < 0x8000:  # Only in ROM area
                matches.append(idx)
            pos = idx + 1

        if matches:
            print(f"Pattern '{description}': {len(matches)} matches")
            for addr in matches[:5]:  # Show first 5
                print(f"  Address: 0x{addr:04X}")

    print()
    print("=" * 80)
    print("Looking for potential CRC routine entry points...")
    print("=" * 80)
    print()

    # CRC routines often start with LD E or LD D (for counter)
    # followed by XOR A (clear accumulator)
    # Let's find common CRC init patterns

    crc_starts = []
    for i in range(0x100, 0x7F00):
        # Pattern: XOR A (AF), followed by some register loads, then a loop
        if rom[i] == 0xAF:  # XOR A
            # Check if there's a loop nearby (within 20 bytes)
            has_loop = False
            for j in range(i+1, min(i+20, len(rom))):
                if rom[j] in [0x20, 0x28, 0x30, 0x38, 0x18]:  # JR instructions
                    has_loop = True
                    break

            if has_loop:
                # This might be a CRC routine
                crc_starts.append(i)

    print(f"Found {len(crc_starts)} potential CRC routine starts")

    # Show most likely candidates (those with XOR + RR patterns nearby)
    likely_crc = []
    for start in crc_starts:
        # Check if CB (rotation prefix) appears within 30 bytes
        has_rotation = False
        for j in range(start, min(start + 30, len(rom))):
            if rom[j] == 0xCB:
                has_rotation = True
                break

        if has_rotation:
            likely_crc.append(start)

    print(f"Likely CRC routines (with rotations): {len(likely_crc)}")
    print()

    # Disassemble the most promising ones
    for addr in likely_crc[:3]:
        print(f"Disassembling potential CRC at 0x{addr:04X}:")
        print("-" * 60)

        pc = addr
        for _ in range(15):  # Show first 15 instructions
            opcode = rom[pc]

            if opcode in OPCODES:
                info = OPCODES[opcode]
                name = info[0]
                length = info[1]

                # Get instruction bytes
                instr_bytes = [rom[pc + i] for i in range(min(length, len(rom) - pc))]
                instr_hex = ' '.join([f'{b:02X}' for b in instr_bytes])

                print(f"  0x{pc:04X}: {instr_hex:12} {name}")

                pc += length
            else:
                print(f"  0x{pc:04X}: {rom[pc]:02X}           (unknown)")
                pc += 1

            if pc >= len(rom):
                break

        print()

def test_crc_like_sequence():
    """Test a typical CRC sequence based on common patterns"""
    print("=" * 80)
    print("TESTING CRC-LIKE INSTRUCTION SEQUENCE")
    print("=" * 80)
    print()

    cpu = CPU()

    # Simulate a typical CRC loop:
    # XOR A,B
    # RR A
    # RR A
    # DEC counter
    # JR NZ, loop

    # Initial state
    cpu.registers._a = 0x5A
    cpu.registers._b = 0xA5
    cpu.registers._c = 3  # Loop counter
    cpu.registers.flags.carry = False

    # Write the CRC-like code
    addr = 0x0000

    # Loop start:
    cpu.memory.write_byte(addr, 0xA8)       # XOR B
    addr += 1
    cpu.memory.write_byte(addr, 0xCB)       # CB prefix
    addr += 1
    cpu.memory.write_byte(addr, 0x1F)       # RR A
    addr += 1
    cpu.memory.write_byte(addr, 0xCB)       # CB prefix
    addr += 1
    cpu.memory.write_byte(addr, 0x1F)       # RR A
    addr += 1
    cpu.memory.write_byte(addr, 0x0D)       # DEC C
    addr += 1
    cpu.memory.write_byte(addr, 0x20)       # JR NZ, back to start
    cpu.memory.write_byte(addr + 1, 0xF9)   # offset = -7
    addr += 2

    cpu.registers._pc = 0x0000

    print("Initial state:")
    print(f"  A=0x{cpu.registers._a:02X}, B=0x{cpu.registers._b:02X}, C={cpu.registers._c}")
    print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
    print()

    # Execute the loop 3 times
    max_steps = 100
    step_count = 0

    print("Executing CRC-like loop:")
    while step_count < max_steps and cpu.registers._c > 0:
        pc_before = cpu.registers._pc
        a_before = cpu.registers._a
        c_before = cpu.registers._c
        carry_before = cpu.registers.flags.carry

        cpu.step()
        step_count += 1

        # Log significant changes
        if a_before != cpu.registers._a or c_before != cpu.registers._c:
            print(f"  [{step_count:2d}] PC=0x{pc_before:04X}: A=0x{a_before:02X}->0x{cpu.registers._a:02X} C={c_before}->{cpu.registers._c} Carry={int(carry_before)}->{int(cpu.registers.flags.carry)}")

    print()
    print("Final state:")
    print(f"  A=0x{cpu.registers._a:02X}, B=0x{cpu.registers._b:02X}, C={cpu.registers._c}")
    print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
    print(f"  Steps executed: {step_count}")

    if step_count >= max_steps:
        print()
        print("WARNING: Loop did not terminate within expected steps!")
        print("This suggests a flag handling bug in the CRC sequence.")
        return False
    else:
        print()
        print("Loop completed successfully")
        return True

if __name__ == "__main__":
    find_crc_patterns()
    print()
    success = test_crc_like_sequence()
    sys.exit(0 if success else 1)
