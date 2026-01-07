"""
Test if joypad is working with Tetris ROM
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Testing joypad integration...")
print()

# Run for a bit
for _ in range(1_000_000 // 4):
    cpu.step()

print(f"After running for a while:")
print(f"  Cycles: {cpu.total_cycles:,}")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")
print(f"  IME: {cpu.ime}")
print()

# Check if game is reading P1
print("Checking P1 register...")
p1_before = cpu.memory.read_byte(0xFF00)
print(f"  P1 before button press: 0x{p1_before:02X}")

# Press Start button
print("\nPressing Start button...")
cpu.memory.joypad.press_button('start')

# Check IF register to see if interrupt was triggered
if_after_press = cpu.memory.read_byte(0xFF0F)
print(f"  IF after press: 0x{if_after_press:02X}")
if if_after_press & 0x10:
    print("  [OK] Joypad interrupt was triggered (bit 4 set)")
else:
    print("  [INFO] No joypad interrupt (bit 4 not set)")

# Read P1 with button group selected
cpu.memory.write_byte(0xFF00, 0xDF)  # Select buttons
p1_with_start = cpu.memory.read_byte(0xFF00)
print(f"  P1 with Start pressed (buttons selected): 0x{p1_with_start:02X}")
if (p1_with_start & 0x08) == 0:
    print("  [OK] Start button is detected (bit 3 = 0)")
else:
    print("  [PROBLEM] Start button NOT detected (bit 3 = 1)")

# Run a few more cycles to see if game responds
print("\nRunning a few more cycles to see if game responds...")
old_pc = cpu.registers._pc
for _ in range(10000):
    cpu.step()

new_pc = cpu.registers._pc
print(f"  PC changed from 0x{old_pc:04X} to 0x{new_pc:04X}")

if old_pc != new_pc:
    print("  [OK] PC is moving, game is running")
else:
    print("  [INFO] PC unchanged, might be in a loop")

# Check P1 reads in game code
print("\nMonitoring P1 register reads...")
read_count = 0
for i in range(100000):
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Check for LDH A,(FF00) or similar P1 reads
    # F0 00 = LDH A,(n) where n=0x00 means reading from 0xFF00
    if opcode == 0xF0:
        next_byte = cpu.memory.read_byte(pc + 1)
        if next_byte == 0x00:
            read_count += 1
            if read_count <= 3:
                print(f"  Game reading P1 at PC=0x{pc:04X}")

    cpu.step()

print(f"\nP1 register was read {read_count} times in 100,000 cycles")
if read_count > 0:
    print("  [OK] Game is polling joypad")
else:
    print("  [PROBLEM] Game doesn't seem to be reading joypad")
