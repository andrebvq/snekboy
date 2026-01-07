"""
Wait for LCD to actually turn ON (LCDC bit 7 = 1) and stay on
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Waiting for LCD to turn on (LCDC bit 7 = 1)...")
print()

max_cycles = 500_000_000  # 500 million cycles max
check_interval = 100_000

last_check = 0
lcd_on_count = 0
last_lcdc = 0

while cpu.total_cycles < max_cycles:
    try:
        cpu.step()

        # Check periodically
        if cpu.total_cycles - last_check >= check_interval:
            lcdc = cpu.memory.read_byte(0xFF40)
            ly = cpu.memory.read_byte(0xFF44)
            pc = cpu.registers._pc

            # Check if LCD is on (bit 7 = 1)
            lcd_enabled = (lcdc & 0x80) != 0

            if lcd_enabled:
                lcd_on_count += 1
                print(f"[{cpu.total_cycles:,}] LCD ON! LCDC=0x{lcdc:02X}, LY={ly}, PC=0x{pc:04X}")

                # If LCD has been on for 10 consecutive checks, assume it's stable
                if lcd_on_count >= 10:
                    print(f"\nLCD appears to be stable ON!")
                    print(f"LCDC: 0x{lcdc:02X}")
                    print(f"LY: {ly}")
                    print(f"PC: 0x{pc:04X}")

                    # Check screen buffer
                    screen = cpu.ppu.get_screen_buffer()
                    colors = set()
                    for row in screen:
                        colors.update(row)
                    print(f"Screen buffer colors: {sorted(colors)}")

                    break
            else:
                if lcd_on_count > 0:
                    print(f"[{cpu.total_cycles:,}] LCD turned OFF again (was on for {lcd_on_count} checks)")
                lcd_on_count = 0

            last_check = cpu.total_cycles
            last_lcdc = lcdc

    except NotImplementedError as e:
        print(f"\nUnimplemented instruction: {e}")
        print(f"PC: 0x{cpu.registers._pc:04X}, Cycles: {cpu.total_cycles:,}")
        break
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        break

if cpu.total_cycles >= max_cycles:
    print(f"\nReached {max_cycles:,} cycles without LCD staying on")
    print(f"Last LCDC: 0x{last_lcdc:02X}")
