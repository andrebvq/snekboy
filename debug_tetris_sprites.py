"""Debug script to check Tetris sprites and rendering"""

import sys
sys.path.insert(0, 'C:\\Users\\andre\\OneDrive\\Desktop\\projects\\snekboy')

from src.cpu import CPU

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

print(f"Loading ROM: {rom_path}")
cpu = CPU()
cpu.memory.load_rom_file(rom_path)
print("ROM loaded\n")

# Run for a bit
print("Running for 2 million cycles...")
cycles_run = 0
max_cycles = 2_000_000

while cycles_run < max_cycles:
    cycles = cpu.step()
    cycles_run += cycles

print(f"Completed {cycles_run:,} cycles\n")

# Check OAM (sprite data)
print("OAM Data (Sprites 0-9):")
for i in range(10):
    oam_addr = 0xFE00 + (i * 4)
    y = cpu.memory.read_byte(oam_addr)
    x = cpu.memory.read_byte(oam_addr + 1)
    tile = cpu.memory.read_byte(oam_addr + 2)
    flags = cpu.memory.read_byte(oam_addr + 3)

    if y != 0 or x != 0:  # Only show sprites that are positioned
        print(f"  Sprite {i}: Y={y:3d} X={x:3d} Tile=0x{tile:02X} Flags=0x{flags:02X}")

# Check what the PPU thinks about rendering
print(f"\nPPU Current Mode: {cpu.ppu.current_mode}")
ly = cpu.memory.read_byte(0xFF44)
print(f"LY Register: {ly}")

# Let's manually render one line to see what's happening
print("\nManually checking scanline 80 (middle of screen):")
scanline = 80

# Check background
lcdc = cpu.memory.read_byte(0xFF40)
scy = cpu.memory.read_byte(0xFF42)
scx = cpu.memory.read_byte(0xFF43)
bgp = cpu.memory.read_byte(0xFF47)

print(f"  SCY={scy}, SCX={scx}")
print(f"  BGP=0x{bgp:02X}")

# Get the tile map row
y_in_map = (scanline + scy) % 256
tile_row = y_in_map // 8
y_in_tile = y_in_map % 8

print(f"  Scanline {scanline} maps to tile row {tile_row}, pixel row {y_in_tile} in tile")

# Get tiles for this row
tile_map_addr = 0x9800 + (tile_row * 32)
print(f"  Tile map address: 0x{tile_map_addr:04X}")

# Get first 10 tiles
print(f"  First 10 tiles in this row:")
for x in range(10):
    tile_idx = cpu.memory.read_byte(tile_map_addr + x)
    tile_addr = 0x8000 + (tile_idx * 16)
    byte1 = cpu.memory.read_byte(tile_addr + y_in_tile * 2)
    byte2 = cpu.memory.read_byte(tile_addr + y_in_tile * 2 + 1)
    print(f"    X={x}: Tile 0x{tile_idx:02X} @ 0x{tile_addr:04X}, Row data: 0x{byte1:02X} 0x{byte2:02X}")

# Check actual screen buffer at this line
screen = cpu.ppu.get_screen_buffer()
print(f"\nScreen buffer at scanline {scanline}, first 20 pixels:")
print("  " + "".join(str(screen[scanline][x]) for x in range(20)))

# Check another scanline
scanline2 = 81
print(f"\nScreen buffer at scanline {scanline2}, first 20 pixels:")
print("  " + "".join(str(screen[scanline2][x]) for x in range(20)))

# Look for patterns - are there alternating colors vertically?
print("\nChecking for vertical stripe pattern:")
print("Column 0, rows 80-89:")
for row in range(80, 90):
    print(f"  Row {row}: {screen[row][0]}")

print("\nColumn 1, rows 80-89:")
for row in range(80, 90):
    print(f"  Row {row}: {screen[row][1]}")
