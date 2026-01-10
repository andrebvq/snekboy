"""Debug script to check what Tetris is displaying"""

import sys
sys.path.insert(0, 'C:\\Users\\andre\\OneDrive\\Desktop\\projects\\snekboy')

from src.cpu import CPU
import time

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

print(f"Loading ROM: {rom_path}")
cpu = CPU()
cpu.memory.load_rom_file(rom_path)
print("ROM loaded\n")

# Run for a bit to let the game initialize
print("Running for 2 million cycles...")
cycles_run = 0
max_cycles = 2_000_000

while cycles_run < max_cycles:
    try:
        cycles = cpu.step()
        cycles_run += cycles

        if cycles_run % 500_000 == 0:
            print(f"  {cycles_run:,} cycles...")
    except Exception as e:
        print(f"Error at {cycles_run:,} cycles: {e}")
        break

print(f"\nCompleted {cycles_run:,} cycles\n")

# Check PPU state
print("PPU State:")
print(f"  LCDC (0xFF40): 0x{cpu.memory.read_byte(0xFF40):02X}")
lcdc = cpu.memory.read_byte(0xFF40)
print(f"    LCD Enable: {bool(lcdc & 0x80)}")
print(f"    Window Tile Map: {'0x9C00' if lcdc & 0x40 else '0x9800'}")
print(f"    Window Enable: {bool(lcdc & 0x20)}")
print(f"    BG & Window Tile Data: {'0x8000' if lcdc & 0x10 else '0x8800'}")
print(f"    BG Tile Map: {'0x9C00' if lcdc & 0x08 else '0x9800'}")
print(f"    OBJ Size: {'8x16' if lcdc & 0x04 else '8x8'}")
print(f"    OBJ Enable: {bool(lcdc & 0x02)}")
print(f"    BG Enable: {bool(lcdc & 0x01)}")

print(f"\n  STAT (0xFF41): 0x{cpu.memory.read_byte(0xFF41):02X}")
print(f"  SCY (0xFF42): {cpu.memory.read_byte(0xFF42)}")
print(f"  SCX (0xFF43): {cpu.memory.read_byte(0xFF43)}")
print(f"  LY (0xFF44): {cpu.memory.read_byte(0xFF44)}")
print(f"  BGP (0xFF47): 0x{cpu.memory.read_byte(0xFF47):02X}")

# Check background tile map (first few entries)
print("\nBackground Tile Map (0x9800-0x981F, first 32 tiles of row 0):")
tile_map_start = 0x9800
tiles = []
for i in range(32):
    tile_idx = cpu.memory.read_byte(tile_map_start + i)
    tiles.append(tile_idx)
print("  " + " ".join(f"{t:02X}" for t in tiles))

# Check if tiles have unique indices
unique_tiles = set(tiles)
print(f"\nUnique tile indices in first row: {len(unique_tiles)}")
print(f"  Tile indices: {sorted(unique_tiles)}")

# Sample a few tiles from VRAM
print("\nSample Tile Data from VRAM:")
base_addr = 0x8000 if lcdc & 0x10 else 0x8800

for tile_idx in sorted(list(unique_tiles))[:5]:
    if lcdc & 0x10:  # 0x8000 addressing
        addr = 0x8000 + (tile_idx * 16)
    else:  # 0x8800 addressing (signed)
        if tile_idx < 128:
            addr = 0x9000 + (tile_idx * 16)
        else:
            addr = 0x8800 + ((tile_idx - 128) * 16)

    print(f"\n  Tile #{tile_idx:02X} at address 0x{addr:04X}:")
    # Show first 4 rows (8 bytes)
    for row in range(4):
        byte1 = cpu.memory.read_byte(addr + row * 2)
        byte2 = cpu.memory.read_byte(addr + row * 2 + 1)
        print(f"    Row {row}: 0x{byte1:02X} 0x{byte2:02X}", end="")
        # Decode the pixels
        pixels = []
        for bit in range(7, -1, -1):
            low = (byte1 >> bit) & 1
            high = (byte2 >> bit) & 1
            pixel_color = (high << 1) | low
            pixels.append(str(pixel_color))
        print(f"  -> {''.join(pixels)}")

# Check screen buffer
print("\nChecking PPU screen buffer...")
screen = cpu.ppu.get_screen_buffer()
colors_used = set()
for row in screen:
    colors_used.update(row)
print(f"Colors in screen buffer: {sorted(colors_used)}")

# Check if there's a pattern (vertical stripes)
print("\nFirst 10 pixels of row 0:")
print("  " + " ".join(str(screen[0][i]) for i in range(10)))
print("First 10 pixels of row 1:")
print("  " + " ".join(str(screen[1][i]) for i in range(10)))
print("First 10 pixels of row 2:")
print("  " + " ".join(str(screen[2][i]) for i in range(10)))
