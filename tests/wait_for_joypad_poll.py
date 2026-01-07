"""
Wait for the game to start polling the joypad
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Waiting for game to start polling joypad (reading P1 at 0xFF00)...")
print()

max_cycles = 100_000_000
check_every = 1_000_000
last_check = 0
p1_reads = 0

while cpu.total_cycles < max_cycles:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Detect reads of P1 register
    # LDH A,(n) with n=0x00 reads from 0xFF00
    if opcode == 0xF0:
        next_byte = cpu.memory.read_byte(pc + 1)
        if next_byte == 0x00:
            p1_reads += 1
            if p1_reads == 1:
                print(f"[{cpu.total_cycles:,}] First P1 read at PC=0x{pc:04X}!")
                print(f"  LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
                print(f"  LY: {cpu.memory.read_byte(0xFF44)}")
                print()
                print("Game is now polling joypad - input should work!")
                break

    cpu.step()

    # Progress update
    if cpu.total_cycles - last_check >= check_every:
        lcdc = cpu.memory.read_byte(0xFF40)
        ly = cpu.memory.read_byte(0xFF44)
        print(f"[{cpu.total_cycles:,}] Still waiting... PC=0x{pc:04X}, LCDC=0x{lcdc:02X}, LY={ly}")
        last_check = cpu.total_cycles

if p1_reads == 0:
    print(f"\nReached {max_cycles:,} cycles without game polling joypad")
    print("This is unusual - most games start polling input within a few million cycles")
else:
    # Test if buttons work
    print("\nTesting button presses now that game is polling...")

    # Press Start
    cpu.memory.joypad.press_button('start')
    cpu.memory.write_byte(0xFF00, 0xDF)  # Select buttons
    p1 = cpu.memory.read_byte(0xFF00)
    print(f"  P1 with Start pressed: 0x{p1:02X} (bit 3={1 if p1 & 0x08 else 0})")

    # Run a bit to see if game responds
    old_pc = cpu.registers._pc
    for _ in range(100000):
        cpu.step()

    new_pc = cpu.registers._pc
    print(f"  After pressing Start, PC: 0x{old_pc:04X} -> 0x{new_pc:04X}")
