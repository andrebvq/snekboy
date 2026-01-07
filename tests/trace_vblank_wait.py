"""
Trace the VBlank wait loop to see what's happening with LY
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we're at the loop
while cpu.registers._pc != 0x0233:
    cpu.step()
    if cpu.total_cycles > 20_000_000:
        print("Never reached 0x0233")
        exit(1)

print(f"Reached VBlank wait loop at cycle {cpu.total_cycles:,}")
print(f"Loop code:")
print(f"  0x0233: LDH A,(0x44)  ; Read LY")
print(f"  0x0235: CP 0x94       ; Compare with 148")
print(f"  0x0237: JR NZ,-6      ; Loop if LY != 148")
print()

print("Watching LY values:")
last_ly = -1
ly_changes = 0
iterations = 0

for i in range(500):
    pc = cpu.registers._pc

    if pc == 0x0233:
        # About to read LY
        cpu.step()  # Execute LDH A,(0x44)

        ly = cpu.registers._a  # LY was just loaded into A

        if ly != last_ly:
            print(f"  [{iterations:4d}] LY changed: {last_ly} -> {ly} (cycle: {cpu.total_cycles:,})")
            last_ly = ly
            ly_changes += 1

            if ly == 0x94:
                print(f"\n  >>> LY reached 0x94! Loop should exit now")

                # Execute the CP and JR NZ
                cpu.step()  # CP 0x94
                cpu.step()  # JR NZ

                print(f"  >>> After JR NZ, PC is: 0x{cpu.registers._pc:04X}")
                if cpu.registers._pc != 0x0233:
                    print(f"  >>> Loop exited successfully!")
                else:
                    print(f"  >>> [BUG] Loop did NOT exit even though LY == 0x94!")
                break

        iterations += 1

        # Execute CP and JR NZ
        cpu.step()  # CP
        cpu.step()  # JR NZ
    else:
        cpu.step()

print(f"\nAfter {iterations} loop iterations:")
print(f"  LY changes observed: {ly_changes}")
print(f"  Last LY value: {last_ly}")
print(f"  Current PC: 0x{cpu.registers._pc:04X}")

if ly_changes == 0:
    print("\n[PROBLEM] LY never changed! PPU may not be running properly")
elif iterations >= 500:
    print(f"\n[PROBLEM] Loop ran for 500 iterations without LY reaching 0x94")
    print(f"  LY range: 0 to {last_ly}")
