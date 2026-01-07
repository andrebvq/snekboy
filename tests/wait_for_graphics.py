"""
Run until the screen buffer has actual graphics (not all one color)
"""

from src.cpu import CPU

cpu = CPU()
rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"
cpu.memory.load_rom_file(rom_path)

print("Running until screen buffer shows graphics...")
print()

max_cycles = 200_000_000  # 200 million cycles max
check_interval = 1_000_000  # Check every 1M cycles

last_check = 0

while cpu.total_cycles < max_cycles:
    try:
        cpu.step()

        if cpu.total_cycles - last_check >= check_interval:
            # Check screen buffer
            screen = cpu.ppu.get_screen_buffer()
            colors = set()
            for row in screen:
                colors.update(row)

            lcdc = cpu.memory.read_byte(0xFF40)
            ly = cpu.memory.read_byte(0xFF44)
            pc = cpu.registers._pc

            # If we have more than one color, there's actual graphics!
            if len(colors) > 1:
                print(f"\n[{cpu.total_cycles:,}] GRAPHICS DETECTED!")
                print(f"  Colors in buffer: {sorted(colors)}")
                print(f"  LCDC: 0x{lcdc:02X}")
                print(f"  LY: {ly}")
                print(f"  PC: 0x{pc:04X}")

                # Count how many pixels of each color
                color_counts = {0: 0, 1: 0, 2: 0, 3: 0}
                for row in screen:
                    for color in row:
                        color_counts[color] = color_counts.get(color, 0) + 1

                print(f"  Color distribution:")
                for color, count in sorted(color_counts.items()):
                    pct = (count / (160 * 144)) * 100
                    print(f"    Color {color}: {count:5d} pixels ({pct:5.1f}%)")

                print(f"\n[SUCCESS] Tetris is displaying graphics!")
                break
            else:
                if cpu.total_cycles % 10_000_000 == 0:
                    print(f"[{cpu.total_cycles:,}] Still solid color {list(colors)[0]}, PC=0x{pc:04X}, LCDC=0x{lcdc:02X}")

            last_check = cpu.total_cycles

    except NotImplementedError as e:
        print(f"\nUnimplemented: {e}")
        print(f"PC: 0x{cpu.registers._pc:04X}")
        break
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        break

if cpu.total_cycles >= max_cycles:
    print(f"\nReached {max_cycles:,} cycles without seeing graphics")
    print("The game may be stuck waiting for joypad input")
