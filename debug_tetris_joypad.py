"""
Debug Tetris joypad reads
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

# Monkey patch to trace P1 reads/writes
original_read = None
original_write = None

cpu = CPU()

# Save originals
original_read = cpu.memory.read_byte
original_write = cpu.memory.write_byte

def trace_read(address):
    result = original_read(address)
    if address == 0xFF00:
        print(f"[READ  P1] -> 0x{result:02X} (bin: {result:08b})")
    return result

def trace_write(address, value):
    if address == 0xFF00:
        print(f"[WRITE P1] <- 0x{value:02X} (bin: {value:08b})")
    original_write(address, value)

# Patch memory
cpu.memory.read_byte = trace_read
cpu.memory.write_byte = trace_write

# Load Tetris
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Running Tetris for 5M cycles...")
print("Watching for P1 reads/writes...")
print()

# Run to get to the level select screen
for _ in range(5_000_000):
    cpu.step()

print(f"\nReached {cpu.total_cycles:,} cycles")
print("\nNow pressing START button...")
cpu.memory.joypad.press_button('start')
print(f"Button state: {cpu.memory.joypad.get_state_string()}")

print("\nRunning 100k more cycles with START held...")
for _ in range(100_000):
    cpu.step()

print(f"\nTotal cycles: {cpu.total_cycles:,}")
print(f"Final button state: {cpu.memory.joypad.get_state_string()}")
