"""
Trace what happens when L wraps from 0xFF to 0x00
"""

from src.cpu import CPU

cpu = CPU()
cpu.memory.load_rom_file('test_roms/halt_bug.gb')

# Run until we hit the loop
target_cycles = 289_464

while cpu.total_cycles < target_cycles:
    cpu.step()

print(f"At the loop, HL=0x{cpu.registers.hl:04X}")
print("="*80)

# Now step until L is near 0xFF
while cpu.registers._l < 0xF8:
    cpu.step()

print(f"L is now 0x{cpu.registers._l:02X}, approaching wrap point")
print("="*80)

# Trace in detail
for i in range(30):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)
    l_before = cpu.registers._l
    z_before = cpu.registers.flags.zero

    cpu.step()

    l_after = cpu.registers._l
    z_after = cpu.registers.flags.zero

    print(f"[{i:2d}] PC=0x{pc:04X} Op=0x{opcode:02X} | L: 0x{l_before:02X}->0x{l_after:02X} | Z: {z_before}->{z_after}")

    if l_before == 0xFF and l_after == 0x00:
        print(f"\n{'='*80}")
        print(f"L WRAPPED! Zero flag should be {z_after}")
        print(f"Next instruction at PC=0x{cpu.registers._pc:04X}")
        next_op = cpu.memory.read_byte(cpu.registers._pc)
        print(f"Next opcode: 0x{next_op:02X} (should be JR NZ)")
        print(f"{'='*80}\n")

        # Execute the JR NZ and see what happens
        pc_before = cpu.registers._pc
        cpu.step()
        pc_after = cpu.registers._pc

        if pc_before == pc_after - 2:  # Normal 2-byte instruction
            print("JR NZ did NOT jump (correct if Z=1)")
        else:
            print(f"JR NZ jumped from 0x{pc_before:04X} to 0x{pc_after:04X}")

        break
