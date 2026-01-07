"""
Trace exactly what happens when LY reaches 94 (0x94)
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run until we're at the loop
while cpu.registers._pc != 0x0233:
    cpu.step()

print("Waiting for LY to reach 0x94 (148 decimal)...")

for i in range(2000):
    pc = cpu.registers._pc

    if pc == 0x0233:
        # Check LY BEFORE reading it
        ly_before_read = cpu.memory.read_byte(0xFF44)

        # Execute LDH A,(0x44) - read LY into A
        cpu.step()

        a_value = cpu.registers._a  # What was loaded

        # Execute CP 0x94
        cpu.step()

        z_flag = cpu.registers.flags.zero  # Will be True if A == 0x94

        # Read PC before JR
        pc_before_jr = cpu.registers._pc

        # Execute JR NZ
        cpu.step()

        pc_after_jr = cpu.registers._pc

        # Print when LY is close to or equals 0x94
        if ly_before_read >= 0x90:  # Print when close
            jumped = (pc_after_jr == 0x0233)
            print(f"[{i:4d}] LY=0x{ly_before_read:02X} ({ly_before_read:3d}), A=0x{a_value:02X}, Z={int(z_flag)}, jumped={jumped}, PC: 0x{pc_after_jr:04X}")

            if ly_before_read == 0x94 and not z_flag:
                print(f"     >>> [BUG] LY==0x94 but zero flag is False! A=0x{a_value:02X}")
                print(f"     >>> CP should have set zero flag to True")
                break

            if ly_before_read == 0x94 and z_flag and jumped:
                print(f"     >>> [BUG] LY==0x94, zero flag is True, but still jumped!")
                break

            if ly_before_read == 0x94 and z_flag and not jumped:
                print(f"     >>> [OK] Loop correctly exited when LY==0x94")
                break

            if ly_before_read > 0x94:
                print(f"     >>> LY went past 0x94! Missed it somehow")
                break
    else:
        cpu.step()

print(f"\nFinal state:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  LY: 0x{cpu.memory.read_byte(0xFF44):02X}")
