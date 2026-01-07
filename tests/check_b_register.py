"""
Check what's happening with B register in the stuck loop
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until just before the stuck loop
while cpu.total_cycles < 148_000:
    cpu.step()

print(f"Just before stuck loop:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  B: 0x{cpu.registers._b:02X}")
print(f"  C: 0x{cpu.registers._c:02X}")
print(f"  A: 0x{cpu.registers._a:02X}")
print(f"  HL: 0x{cpu.registers.hl:04X}")

# Step through to the loop
for _ in range(50):
    cpu.step()
    if cpu.registers._pc == 0x026B:
        break

print(f"\nAt start of loop (PC=0x026B):")
print(f"  B: 0x{cpu.registers._b:02X} ({cpu.registers._b} decimal)")
print(f"  Zero flag: {cpu.registers.flags.zero}")

# Execute the loop and watch B
print(f"\nTracing B register through loop:")
print("="*60)

for i in range(500):  # Increased to 500 iterations to see B reach 0
    pc = cpu.registers._pc
    b_before = cpu.registers._b
    z_before = cpu.registers.flags.zero

    cpu.step()

    b_after = cpu.registers._b
    z_after = cpu.registers.flags.zero

    if pc == 0x026C:  # DEC B instruction
        # Only print every 10th iteration until we get close to 0
        if b_after <= 5 or b_before % 10 == 0:
            print(f"[{i:2d}] DEC B: {b_before} -> {b_after}, Zero: {z_before} -> {z_after}")

        if b_after == 0:
            print(f"\n     B reached 0! Zero flag should be True")
            if not z_after:
                print(f"     [BUG] Zero flag is False when it should be True!")
            else:
                print(f"     [OK] Zero flag is correctly True!")

            # Continue a bit more to see if loop exits
            print(f"\nContinuing 5 more steps to see if loop exits...")
            for j in range(5):
                next_pc = cpu.registers._pc
                cpu.step()
                print(f"     Step {j+1}: PC was 0x{next_pc:04X}, now 0x{cpu.registers._pc:04X}")
            break

    # Safety check - if we're still at same PC after 500 iterations, something is wrong
    if i == 499:
        print(f"\n[ERROR] Loop did not exit after 500 iterations!")
        print(f"  Current PC: 0x{cpu.registers._pc:04X}")
        print(f"  Current B: 0x{cpu.registers._b:02X}")
        print(f"  Zero flag: {cpu.registers.flags.zero}")
