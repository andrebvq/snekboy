"""
Wait for C to reach 0 in the nested loop and see if it exits
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we're in the loop
while cpu.total_cycles < 148_000:
    cpu.step()

print(f"Entered loop at cycle {cpu.total_cycles}")
print(f"Initial B: {cpu.registers._b}, C: {cpu.registers._c}")
print()

# Monitor until C becomes 0
iterations = 0
max_iterations = 100_000  # Safety limit

while iterations < max_iterations:
    pc_before = cpu.registers._pc
    c_before = cpu.registers._c
    opcode = cpu.memory.read_byte(pc_before)

    cpu.step()
    iterations += 1

    c_after = cpu.registers._c

    # Check if DEC C happened
    if opcode == 0x0D:  # DEC C
        if c_after == 0:
            print(f"C reached 0! (iteration {iterations})")
            print(f"PC after DEC C: 0x{cpu.registers._pc:04X}")
            print(f"Zero flag after DEC C: {cpu.registers.flags.zero}")

            # Execute next few instructions
            print("\nNext 10 instructions:")
            for i in range(10):
                next_pc = cpu.registers._pc
                next_opcode = cpu.memory.read_byte(next_pc)
                next_b = cpu.registers._b
                next_c = cpu.registers._c

                cpu.step()

                # Decode instruction name
                if next_opcode == 0x20:
                    offset = cpu.memory.read_byte(next_pc + 1)
                    name = f"JR NZ,${offset:02X}"
                elif next_opcode == 0x0D:
                    name = "DEC C"
                elif next_opcode == 0x05:
                    name = "DEC B"
                elif next_opcode == 0x32:
                    name = "LDD (HL),A"
                else:
                    name = f"[0x{next_opcode:02X}]"

                pc_after_step = cpu.registers._pc
                print(f"  [{i}] 0x{next_pc:04X}: {name:15s} B:{next_b:3d} C:{next_c:3d} Z:{int(cpu.registers.flags.zero)} -> PC:0x{pc_after_step:04X}")

                # Check if we exited the loop region
                if pc_after_step < 0x026B or pc_after_step > 0x0270:
                    print(f"\n>>> EXITED LOOP! PC is now 0x{pc_after_step:04X}")
                    break
                elif pc_after_step == 0x026B and i > 2:
                    print(f"\n>>> Still stuck in loop despite C=0!")
                    break
            break

    # Safety check - if we've done too many iterations, something is wrong
    if iterations % 10000 == 0:
        print(f"Still running... iteration {iterations}, B={cpu.registers._b}, C={cpu.registers._c}, PC=0x{cpu.registers._pc:04X}")

if iterations >= max_iterations:
    print(f"\nReached max iterations ({max_iterations}) without C reaching 0")
    print(f"Final B: {cpu.registers._b}, C: {cpu.registers._c}")
