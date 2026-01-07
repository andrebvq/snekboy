"""
Check what register the polling loop is reading
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

# Run to the stuck loop
while cpu.registers._pc != 0x02ED:
    cpu.step()
    if cpu.total_cycles > 100_000_000:
        print("Never reached loop")
        exit(1)

print(f"Reached polling loop at cycle {cpu.total_cycles:,}")
print()

# The instruction at 0x02ED is LDH A,(n) which is 0xF0 followed by offset
opcode = cpu.memory.read_byte(0x02ED)
offset = cpu.memory.read_byte(0x02EE)

print(f"Instruction bytes: 0x{opcode:02X} 0x{offset:02X}")
print(f"This reads from address: 0xFF{offset:02X}")
print()

# What's the value at that address?
register_addr = 0xFF00 + offset
value = cpu.memory.read_byte(register_addr)
print(f"Current value at 0xFF{offset:02X}: 0x{value:02X}")
print()

# Identify common I/O registers
register_names = {
    0xFF00: "P1/JOYP (Joypad)",
    0xFF01: "SB (Serial data)",
    0xFF02: "SC (Serial control)",
    0xFF04: "DIV (Divider)",
    0xFF05: "TIMA (Timer counter)",
    0xFF06: "TMA (Timer modulo)",
    0xFF07: "TAC (Timer control)",
    0xFF0F: "IF (Interrupt flags)",
    0xFF40: "LCDC (LCD control)",
    0xFF41: "STAT (LCD status)",
    0xFF42: "SCY (Scroll Y)",
    0xFF43: "SCX (Scroll X)",
    0xFF44: "LY (LCD Y coordinate)",
    0xFF45: "LYC (LY compare)",
}

reg_name = register_names.get(register_addr, "Unknown")
print(f"Register name: {reg_name}")
print()

print("Loop logic:")
print(f"  1. Read value from 0xFF{offset:02X} ({reg_name})")
print(f"  2. Test if zero (AND A)")
print(f"  3. Jump back if zero")
print(f"  4. Exit loop only when value is NON-ZERO")
print()

print(f"Game is waiting for 0xFF{offset:02X} to become non-zero!")
print()

# Monitor this register for a while
print(f"Monitoring 0xFF{offset:02X} for 1 million cycles...")
last_value = value
changes = 0

for i in range(1_000_000 // 4):
    cpu.step()

    new_value = cpu.memory.read_byte(register_addr)
    if new_value != last_value:
        changes += 1
        if changes <= 10:
            print(f"  [{cpu.total_cycles:,}] Value changed: 0x{last_value:02X} -> 0x{new_value:02X}")
        last_value = new_value

        if new_value != 0:
            print(f"\n  [!] Register became non-zero! Value: 0x{new_value:02X}")
            print(f"      Loop should exit now")

            # Step a few more times
            old_pc = cpu.registers._pc
            for _ in range(10):
                cpu.step()
            new_pc = cpu.registers._pc

            if new_pc != 0x02ED and new_pc != 0x02EF and new_pc != 0x02F0:
                print(f"      [OK] Loop exited! PC: 0x{old_pc:04X} -> 0x{new_pc:04X}")
            else:
                print(f"      [PROBLEM] Still in loop despite non-zero value")
            break

print(f"\nTotal changes observed: {changes}")
print(f"Final value: 0x{last_value:02X}")

if changes == 0:
    print(f"\n[PROBLEM] Register 0xFF{offset:02X} never changes - this is why game is stuck!")
