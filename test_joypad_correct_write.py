"""
Test joypad with CORRECT P1 writes
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.joypad import Joypad

def test():
    print("Testing with correct P1 values...\n")

    joypad = Joypad()

    # Select BUTTONS (bit 5 = 0, bit 4 = 1)
    print("1. Write 0x10 to select BUTTONS:")
    print("   0x10 = 0001 0000")
    print("   bit 5 = 0 (select buttons)")
    print("   bit 4 = 1 (don't select dpad)")

    joypad.write_p1(0x10)
    print(f"   -> select_buttons = {joypad.select_buttons}")
    print(f"   -> select_dpad = {joypad.select_dpad}")

    p1 = joypad.read_p1()
    print(f"   P1 reads as: 0x{p1:02X}")

    # Press START
    print("\n2. Press START button:")
    joypad.press_button('start')

    p1 = joypad.read_p1()
    print(f"   P1 = 0x{p1:02X}")
    print(f"   bit 3 = {(p1 >> 3) & 1} (should be 0 = pressed)")

    if (p1 & 0x08) == 0:
        print("   SUCCESS! START detected!")
    else:
        print("   FAIL! START not detected")

    joypad.release_button('start')

    # Select DPAD (bit 5 = 1, bit 4 = 0)
    print("\n3. Write 0x20 to select DPAD:")
    print("   0x20 = 0010 0000")
    print("   bit 5 = 1 (don't select buttons)")
    print("   bit 4 = 0 (select dpad)")

    joypad.write_p1(0x20)
    print(f"   -> select_buttons = {joypad.select_buttons}")
    print(f"   -> select_dpad = {joypad.select_dpad}")

    # Press LEFT
    print("\n4. Press LEFT:")
    joypad.press_button('left')

    p1 = joypad.read_p1()
    print(f"   P1 = 0x{p1:02X}")
    print(f"   bit 1 = {(p1 >> 1) & 1} (should be 0 = pressed)")

    if (p1 & 0x02) == 0:
        print("   SUCCESS! LEFT detected!")
    else:
        print("   FAIL! LEFT not detected")

if __name__ == '__main__':
    test()
