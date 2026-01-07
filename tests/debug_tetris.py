"""
Debug Tetris execution to see what's happening
"""

from src.cpu import CPU

cpu = CPU()

print("Loading Tetris ROM...")
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("\nRunning first 100,000 cycles with LCD register monitoring...")
print("="*80)

last_lcdc = None
last_ly = None

for i in range(25000):  # 100,000 cycles
    cpu.step()

    # Check every 1000 cycles
    if cpu.total_cycles % 4000 == 0:
        lcdc = cpu.memory.read_byte(0xFF40)
        ly = cpu.memory.read_byte(0xFF44)
        stat = cpu.memory.read_byte(0xFF41)
        pc = cpu.registers._pc

        if lcdc != last_lcdc or ly != last_ly:
            print(f"Cycle {cpu.total_cycles:8d} | PC=0x{pc:04X} | LCDC=0x{lcdc:02X} | LY={ly:3d} | STAT=0x{stat:02X} | Mode={stat & 0x03}")
            last_lcdc = lcdc
            last_ly = ly

print(f"\n{'='*80}")
print("Final state:")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
print(f"  LY: {cpu.memory.read_byte(0xFF44)}")
print(f"  STAT: 0x{cpu.memory.read_byte(0xFF41):02X}")
print(f"  Total cycles: {cpu.total_cycles:,}")

# Check if LCD is on
lcdc = cpu.memory.read_byte(0xFF40)
if lcdc & 0x80:
    print("\n  LCD is ON")
else:
    print("\n  LCD is OFF - this is the problem!")
    print("  Game should turn LCD on during boot")

# Check screen buffer
screen = cpu.ppu.get_screen_buffer()
colors_used = set()
for row in screen:
    colors_used.update(row)
print(f"\n  Colors in screen buffer: {sorted(colors_used)}")

# Check if stuck in a loop
print("\n" + "="*80)
print("Checking if stuck in infinite loop...")

pc_history = []
for i in range(100):
    pc = cpu.registers._pc
    pc_history.append(pc)
    cpu.step()

unique_pcs = len(set(pc_history))
print(f"  Unique PC values in last 100 instructions: {unique_pcs}")
if unique_pcs < 5:
    print(f"  WARNING: Stuck in tight loop around PC=0x{cpu.registers._pc:04X}")
    from collections import Counter
    most_common = Counter(pc_history).most_common(3)
    print(f"  Most common PCs: {most_common}")
