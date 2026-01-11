"""
Test Tetris with proper timing - wait longer before pressing START
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

def count_pixels(screen):
    """Count non-background pixels"""
    return sum(1 for row in screen for pixel in row if pixel != 0)

def test_timing():
    """Test with longer wait times"""
    print("="*70)
    print("TETRIS TIMING TEST")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Wait longer for copyright screen (real time: ~5 seconds = ~350k cycles)
    print("\n1. Waiting for copyright screen to fully display...")
    milestones = [100_000, 200_000, 300_000, 400_000, 500_000, 700_000, 1_000_000]

    for target in milestones:
        while cpu.total_cycles < target:
            cpu.step()

        screen = cpu.ppu.get_screen_buffer()
        pixels = count_pixels(screen)

        print(f"   {target//1000:4d}k cycles: {pixels:5d} non-bg pixels")

    # NOW try pressing START
    print("\n2. Pressing START (should be at title screen now)...")
    cpu.memory.joypad.press_button('start')

    for _ in range(20_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    # Wait for screen to update
    for _ in range(200_000):
        cpu.step()

    screen = cpu.ppu.get_screen_buffer()
    pixels_after = count_pixels(screen)

    print(f"\n   After START: {pixels_after:5d} non-bg pixels")

    # Compare
    screen_before = cpu.ppu.get_screen_buffer()

    # Press START again
    print("\n3. Pressing START again (to select game mode)...")
    cpu.memory.joypad.press_button('start')

    for _ in range(20_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    for _ in range(300_000):
        cpu.step()

    screen_after_second = cpu.ppu.get_screen_buffer()
    pixels_after_second = count_pixels(screen_after_second)

    print(f"   After second START: {pixels_after_second:5d} non-bg pixels")

    # Check for changes
    changes1 = sum(1 for y in range(144) for x in range(160)
                   if screen_before[y][x] != cpu.ppu.get_screen_buffer()[y][x])

    print(f"\n   Pixels changed after second START: {changes1}")

    # Run for a long time to see if ANYTHING changes
    print("\n4. Running for extended time to see if screen updates...")
    prev_pixels = pixels_after_second

    for i in range(10):
        for _ in range(200_000):
            cpu.step()

        screen = cpu.ppu.get_screen_buffer()
        pixels = count_pixels(screen)

        if pixels != prev_pixels:
            print(f"   {cpu.total_cycles//1000:5d}k cycles: {pixels:5d} pixels (CHANGED!)")
            prev_pixels = pixels
        else:
            print(f"   {cpu.total_cycles//1000:5d}k cycles: {pixels:5d} pixels (same)")

    # Final analysis
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    # Check LCDC
    lcdc = cpu.memory.read_byte(0xFF40)
    print(f"LCDC: 0x{lcdc:02X}")
    print(f"  LCD enabled: {bool(lcdc & 0x80)}")
    print(f"  BG enabled: {bool(lcdc & 0x01)}")
    print(f"  Sprites enabled: {bool(lcdc & 0x02)}")

    # Check if game is running or stuck
    pc = cpu.registers._pc
    print(f"\nPC: 0x{pc:04X}")

    # Check if halted
    print(f"Halted: {cpu.halted}")

    # Sample some code at PC
    print(f"\nCode at PC:")
    for i in range(8):
        byte = cpu.memory.read_byte(pc + i)
        print(f"  0x{pc+i:04X}: 0x{byte:02X}")


if __name__ == '__main__':
    test_timing()
