"""
Quick test of joypad fix
"""

import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Force fresh import
if 'src.joypad' in sys.modules:
    del sys.modules['src.joypad']
if 'src.cpu' in sys.modules:
    del sys.modules['src.cpu']
if 'src.memory' in sys.modules:
    del sys.modules['src.memory']

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def quick_joypad_test():
    """Quick test if joypad works"""
    print("Testing joypad fix...")

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot quickly
    while cpu.total_cycles < 100_000:
        cpu.step()

    print("\n1. Testing button press detection:")

    # Test START button
    print("\nBEFORE pressing START:")
    cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons
    p1 = cpu.memory.read_byte(0xFF00)
    print(f"  P1 = 0x{p1:02X}, bit 3 = {(p1 >> 3) & 1} (should be 1 = not pressed)")

    cpu.memory.joypad.press_button('start')

    print("\nAFTER pressing START:")
    cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons
    p1 = cpu.memory.read_byte(0xFF00)
    print(f"  P1 = 0x{p1:02X}, bit 3 = {(p1 >> 3) & 1} (should be 0 = pressed)")

    if (p1 & 0x08) == 0:
        print("  ✅ START button detected correctly!")
    else:
        print("  ❌ START button NOT detected")

    cpu.memory.joypad.release_button('start')

    # Test A button
    print("\nTesting A button:")
    cpu.memory.joypad.press_button('a')
    cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons
    p1 = cpu.memory.read_byte(0xFF00)
    print(f"  P1 = 0x{p1:02X}, bit 0 = {p1 & 1} (should be 0 = pressed)")

    if (p1 & 0x01) == 0:
        print("  ✅ A button detected correctly!")
    else:
        print("  ❌ A button NOT detected")

    cpu.memory.joypad.release_button('a')

    # Test D-pad
    print("\nTesting LEFT:")
    cpu.memory.joypad.press_button('left')
    cpu.memory.write_byte(0xFF00, 0x10)  # Select dpad
    p1 = cpu.memory.read_byte(0xFF00)
    print(f"  P1 = 0x{p1:02X}, bit 1 = {(p1 >> 1) & 1} (should be 0 = pressed)")

    if (p1 & 0x02) == 0:
        print("  ✅ LEFT detected correctly!")
    else:
        print("  ❌ LEFT NOT detected")

    print("\n" + "="*50)
    if ((cpu.memory.read_byte(0xFF00) & 0x02) == 0):
        print("JOYPAD FIX SUCCESSFUL! ✅")
    else:
        print("Joypad still broken ❌")

if __name__ == '__main__':
    quick_joypad_test()
