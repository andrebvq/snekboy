"""
Debug Tetris button issue
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

cpu = CPU()

# Load Tetris ROM (adjust path as needed)
try:
    cpu.memory.load_rom_file('roms/tetris.gb')
except FileNotFoundError:
    print("Tetris ROM not found. Please place tetris.gb in roms/ folder")
    sys.exit(1)

# Run for a bit to get to title screen
print("Running to title screen...")
for _ in range(1_000_000):
    cpu.step()

print(f"\nAfter {cpu.total_cycles:,} cycles:")
print(f"IME (Interrupt Master Enable): {cpu.ime}")
print(f"IE (0xFFFF): 0x{cpu.memory.read_byte(0xFFFF):02X}")
print(f"  VBlank enabled: {bool(cpu.memory.read_byte(0xFFFF) & 0x01)}")
print(f"  LCD enabled:    {bool(cpu.memory.read_byte(0xFFFF) & 0x02)}")
print(f"  Timer enabled:  {bool(cpu.memory.read_byte(0xFFFF) & 0x04)}")
print(f"  Serial enabled: {bool(cpu.memory.read_byte(0xFFFF) & 0x08)}")
print(f"  Joypad enabled: {bool(cpu.memory.read_byte(0xFFFF) & 0x10)}")
print(f"IF (0xFF0F): 0x{cpu.memory.read_byte(0xFF0F):02X}")

# Press Start button
print("\nPressing START button...")
cpu.joypad.press_button('start')

print(f"After pressing START:")
print(f"IF (0xFF0F): 0x{cpu.memory.read_byte(0xFF0F):02X}")
print(f"  Joypad interrupt flag: {bool(cpu.memory.read_byte(0xFF0F) & 0x10)}")
print(f"P1 register (0xFF00): 0x{cpu.memory.read_byte(0xFF00):02X}")

# Run a few more cycles
print("\nRunning 100,000 more cycles with button held...")
for _ in range(100_000):
    cpu.step()

print(f"IF (0xFF0F) after cycles: 0x{cpu.memory.read_byte(0xFF0F):02X}")
print(f"P1 register: 0x{cpu.memory.read_byte(0xFF00):02X}")

# Try reading P1 directly
print("\nDirect P1 read test:")
print(f"Joypad internal state: {cpu.joypad.get_state_string()}")

# Select button group and read
cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons (bit 5 = 0)
print(f"After selecting buttons (write 0x20 to P1): 0x{cpu.memory.read_byte(0xFF00):02X}")
print(f"  Bit 3 (Start): {(cpu.memory.read_byte(0xFF00) >> 3) & 1} (0=pressed)")

# Release button
cpu.joypad.release_button('start')
cpu.memory.write_byte(0xFF00, 0x20)
print(f"After releasing START: 0x{cpu.memory.read_byte(0xFF00):02X}")
