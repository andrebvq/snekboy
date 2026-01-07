"""
Check if VBlank interrupts are being generated
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Monitoring interrupt generation...")
print()

max_cycles = 10_000_000
last_if = 0
vblank_count = 0
timer_count = 0
other_count = 0

for _ in range(max_cycles // 4):
    cpu.step()

    # Check IF register every step
    if_reg = cpu.memory.read_byte(0xFF0F)

    if if_reg != last_if:
        # Interrupt flags changed
        vblank = if_reg & 0x01
        lcd_stat = if_reg & 0x02
        timer = if_reg & 0x04
        serial = if_reg & 0x08
        joypad = if_reg & 0x10

        if vblank and not (last_if & 0x01):
            vblank_count += 1
            if vblank_count <= 5:
                lcdc = cpu.memory.read_byte(0xFF40)
                ly = cpu.memory.read_byte(0xFF44)
                print(f"[{cpu.total_cycles:,}] VBlank interrupt! (count: {vblank_count}) LCDC=0x{lcdc:02X}, LY={ly}")

        if timer and not (last_if & 0x04):
            timer_count += 1
            if timer_count <= 3:
                print(f"[{cpu.total_cycles:,}] Timer interrupt! (count: {timer_count})")

        last_if = if_reg

    if cpu.total_cycles >= max_cycles:
        break

print(f"\nAfter {cpu.total_cycles:,} cycles:")
print(f"  VBlank interrupts: {vblank_count}")
print(f"  Timer interrupts: {timer_count}")
print(f"  IE register: 0x{cpu.memory.read_byte(0xFFFF):02X}")
print(f"  IF register: 0x{cpu.memory.read_byte(0xFF0F):02X}")
print(f"  IME (interrupts enabled): {cpu.ime}")
print(f"  LCDC: 0x{cpu.memory.read_byte(0xFF40):02X}")
print(f"  LY: {cpu.memory.read_byte(0xFF44)}")

if vblank_count == 0:
    print("\n[PROBLEM] No VBlank interrupts generated!")
else:
    print(f"\n[OK] VBlank interrupts are working")
