"""
Detailed trace of the JR NZ instruction when B=0
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we're in the loop
while cpu.total_cycles < 148_000:
    cpu.step()

# Now step until B is small (around 5 or less)
while cpu.registers._b > 5:
    cpu.step()

print(f"Starting trace near where B becomes 0...")
print(f"Current PC: 0x{cpu.registers._pc:04X}")
print(f"Current B: {cpu.registers._b}")
print()

# Step through until we see B=0 and the JR NZ instruction
for i in range(100):
    pc_before = cpu.registers._pc
    b_before = cpu.registers._b
    z_before = cpu.registers.flags.zero

    # Read the opcode at current PC
    opcode = cpu.memory.read_byte(pc_before)

    # Execute instruction
    cpu.step()

    pc_after = cpu.registers._pc
    b_after = cpu.registers._b
    z_after = cpu.registers.flags.zero

    # Print if this is DEC B or JR NZ
    if opcode == 0x05:  # DEC B
        print(f"[{i:2d}] 0x{pc_before:04X}: DEC B")
        print(f"      B: {b_before} -> {b_after}, Zero: {z_before} -> {z_after}")

        if b_after == 0:
            print(f"      >>> B REACHED 0! Zero flag is now {z_after}")

    elif opcode == 0x20:  # JR NZ
        offset = cpu.memory.read_byte(pc_before + 1)
        if offset > 127:
            offset_signed = offset - 256
        else:
            offset_signed = offset

        print(f"[{i:2d}] 0x{pc_before:04X}: JR NZ,${offset:02X} (offset: {offset_signed})")
        print(f"      Zero flag BEFORE jump check: {z_before}")
        print(f"      Should jump? {not z_before}")
        print(f"      PC: 0x{pc_before:04X} -> 0x{pc_after:04X}")

        if z_before and pc_after != pc_before + 2:
            print(f"      >>> [BUG] Zero flag is True but jumped anyway!")
            print(f"      >>> Expected PC: 0x{pc_before + 2:04X}, got 0x{pc_after:04X}")
            break
        elif z_before and pc_after == pc_before + 2:
            print(f"      >>> [OK] Zero flag is True, correctly did NOT jump")
            print(f"      >>> Loop should exit now!")

            # Print next few instructions to confirm exit
            print(f"\n      Next 5 instructions:")
            for j in range(5):
                next_pc = cpu.registers._pc
                next_opcode = cpu.memory.read_byte(next_pc)
                cpu.step()
                print(f"          0x{next_pc:04X}: opcode 0x{next_opcode:02X}")
            break
