"""
Test OAM DMA implementation with Tetris
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

# Track DMA writes
dma_writes = []

original_write = None

def traced_write(address, value):
    if address == 0xFF46:  # DMA register
        dma_writes.append((traced_write.cpu.total_cycles, value))
    return original_write(address, value)


def count_pixels(screen):
    """Count non-background pixels"""
    return sum(1 for row in screen for pixel in row if pixel != 0)


def show_screen_ascii(screen, title):
    """Show screen as ASCII art"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print('='*60)

    chars = [' ', '.', '+', '#']

    print("+" + "-" * 40 + "+")
    for y in range(0, 144, 4):
        line = "|"
        for x in range(0, 160, 4):
            avg = 0
            for dy in range(4):
                for dx in range(4):
                    if y+dy < 144 and x+dx < 160:
                        avg += screen[y+dy][x+dx]
            avg = avg // 16
            line += chars[min(avg, 3)]
        line += "|"
        print(line)
    print("+" + "-" * 40 + "+")


def test_oam_dma():
    """Test if OAM DMA fixes Tetris"""
    print("="*70)
    print("OAM DMA TEST")
    print("="*70)

    cpu = CPU()

    # Patch to trace DMA
    global original_write
    original_write = cpu.memory.write_byte
    traced_write.cpu = cpu
    cpu.memory.write_byte = traced_write

    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    print("\n1. Booting to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    screen1 = cpu.ppu.get_screen_buffer()
    pixels1 = count_pixels(screen1)

    print(f"   Pixels: {pixels1:,}")
    print(f"   DMA writes so far: {len(dma_writes)}")

    if dma_writes:
        print(f"\n   First DMA write:")
        cycles, value = dma_writes[0]
        print(f"     Cycle {cycles:,}: DMA from 0x{value:02X}00")

        # Check what was copied
        print(f"\n   Checking OAM after first DMA:")
        cpu.memory._bypass_ppu_restrictions = True

        for i in range(5):
            oam_addr = 0xFE00 + (i * 4)
            y = cpu.memory.read_byte(oam_addr + 0)
            x = cpu.memory.read_byte(oam_addr + 1)
            tile = cpu.memory.read_byte(oam_addr + 2)
            flags = cpu.memory.read_byte(oam_addr + 3)

            y_adj = y - 16
            x_adj = x - 8

            visible = (0 <= y_adj < 144 and -7 <= x_adj < 160)

            print(f"     Sprite {i}: Y={y:3d}({y_adj:+4d}), X={x:3d}({x_adj:+4d}), Tile=0x{tile:02X}, Flags=0x{flags:02X} {'[VIS]' if visible else ''}")

        cpu.memory._bypass_ppu_restrictions = False

    # Run longer
    print("\n2. Running to 3M cycles...")
    while cpu.total_cycles < 3_000_000:
        cpu.step()

    screen2 = cpu.ppu.get_screen_buffer()
    pixels2 = count_pixels(screen2)

    print(f"   Pixels: {pixels2:,}")
    print(f"   DMA writes total: {len(dma_writes)}")

    changes = sum(1 for y in range(144) for x in range(160)
                  if screen1[y][x] != screen2[y][x])

    if changes > 0:
        print(f"   Screen CHANGED: {changes} pixels different!")
        show_screen_ascii(screen2, "After 3M Cycles (with DMA)")
    else:
        print(f"   Screen UNCHANGED")

    # Try pressing START
    print("\n3. Pressing START...")
    cpu.memory.joypad.press_button('start')

    for _ in range(50_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    for _ in range(300_000):
        cpu.step()

    screen3 = cpu.ppu.get_screen_buffer()
    pixels3 = count_pixels(screen3)

    print(f"   Pixels after START: {pixels3:,}")

    changes2 = sum(1 for y in range(144) for x in range(160)
                   if screen2[y][x] != screen3[y][x])

    if changes2 > 0:
        print(f"   Screen CHANGED: {changes2} pixels different!")
        show_screen_ascii(screen3, "After START Press")
    else:
        print(f"   Screen UNCHANGED")

    # Check VRAM writes
    print("\n4. Checking for VRAM writes...")

    vram_writes = []

    original_write2 = cpu.memory.write_byte

    def track_vram(address, value):
        if 0x8000 <= address <= 0x9FFF:
            vram_writes.append((cpu.total_cycles, address, value))
        return original_write2(address, value)

    cpu.memory.write_byte = track_vram

    for _ in range(200_000):
        cpu.step()

    print(f"   VRAM writes in 200k cycles: {len(vram_writes)}")

    if vram_writes:
        print(f"   First 10 VRAM writes:")
        for i, (cycles, addr, value) in enumerate(vram_writes[:10]):
            print(f"     {i+1}. Cycle {cycles:8d}: [0x{addr:04X}] = 0x{value:02X}")

    # Final verdict
    print(f"\n" + "="*70)
    print("VERDICT")
    print("="*70)

    print(f"\nDMA writes detected: {len(dma_writes)}")

    if len(dma_writes) > 0:
        print(f"  OAM DMA is being used by the game!")

        # Show all DMA writes
        print(f"\n  All DMA writes:")
        for i, (cycles, value) in enumerate(dma_writes[:20]):
            print(f"    {i+1:3d}. Cycle {cycles:8d}: DMA from 0x{value:02X}00")
    else:
        print(f"  Game has NOT triggered OAM DMA yet")

    if len(vram_writes) > 0:
        print(f"\n  VRAM writes detected: {len(vram_writes)}")
        print(f"  Game IS updating graphics!")
    else:
        print(f"\n  NO VRAM writes detected")
        print(f"  Game still not updating graphics")

    if pixels3 != pixels1:
        print(f"\n  Screen pixels changed: {pixels1} -> {pixels3}")
        print(f"  Screen IS updating!")
    else:
        print(f"\n  Screen pixels unchanged: {pixels1}")
        print(f"  Screen still frozen")


if __name__ == '__main__':
    test_oam_dma()
