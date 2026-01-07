"""
Trace both B and C registers to understand the nested loop structure
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we're in the loop
while cpu.total_cycles < 148_000:
    cpu.step()

# Step until both B and C are small
while cpu.registers._b > 3 or cpu.registers._c > 3:
    cpu.step()

print(f"Starting detailed trace of nested loops...")
print(f"PC: 0x{cpu.registers._pc:04X}")
print(f"B: {cpu.registers._b}, C: {cpu.registers._c}")
print()

# Trace execution showing both B and C
for i in range(100):
    pc_before = cpu.registers._pc
    b_before = cpu.registers._b
    c_before = cpu.registers._c
    z_before = cpu.registers.flags.zero

    opcode = cpu.memory.read_byte(pc_before)

    cpu.step()

    b_after = cpu.registers._b
    c_after = cpu.registers._c
    z_after = cpu.registers.flags.zero
    pc_after = cpu.registers._pc

    # Build instruction name
    if opcode == 0x32:
        instr = "LDD (HL),A"
    elif opcode == 0x05:
        instr = "DEC B"
    elif opcode == 0x0D:
        instr = "DEC C"
    elif opcode == 0x20:
        offset = cpu.memory.read_byte(pc_before + 1)
        if offset > 127:
            offset_signed = offset - 256
        else:
            offset_signed = offset
        instr = f"JR NZ,${offset:02X} ({offset_signed:+d})"
    else:
        instr = f"[0x{opcode:02X}]"

    # Print interesting instructions
    if opcode in [0x05, 0x0D, 0x20]:  # DEC B, DEC C, JR NZ
        print(f"[{i:3d}] 0x{pc_before:04X}: {instr:20s} | B:{b_before:2d}->{b_after:2d} C:{c_before:2d}->{c_after:2d} Z:{int(z_before)}->{int(z_after)} | PC->0x{pc_after:04X}")

        if opcode == 0x05 and b_after == 0:
            print(f"       >>> B reached 0!")
        elif opcode == 0x0D and c_after == 0:
            print(f"       >>> C reached 0! Outer loop should exit now")

        # If both B and C are 0, check if we exit
        if b_after == 0 and c_after == 0 and opcode == 0x20:
            print(f"       >>> Both B and C are 0, checking if loop exits...")
            if z_after and pc_after != pc_before + 2 + offset_signed:
                print(f"       >>> [BUG] Should not jump when Z=True!")
            elif z_after and pc_after == pc_before + 2:
                print(f"       >>> [OK] Loop exited!")
                # Print next few instructions
                print(f"\nNext instructions after exit:")
                for j in range(10):
                    next_pc = cpu.registers._pc
                    next_opcode = cpu.memory.read_byte(next_pc)
                    cpu.step()
                    print(f"    0x{next_pc:04X}: 0x{next_opcode:02X}")
                break
