"""
Debug joypad internals
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.joypad import Joypad

def test_joypad_directly():
    """Test joypad class directly"""
    print("Testing Joypad class directly...\n")

    joypad = Joypad()

    # Test initial state
    print("1. Initial state (no selection):")
    p1 = joypad.read_p1()
    print(f"   P1 = 0x{p1:02X} (binary: {p1:08b})")
    print(f"   Expected: 0xFF (all bits 1)")

    # Select buttons (bit 5 = 0)
    print("\n2. Select buttons (write 0x20 to P1):")
    joypad.write_p1(0x20)
    print(f"   select_buttons = {joypad.select_buttons}")
    print(f"   select_dpad = {joypad.select_dpad}")

    p1 = joypad.read_p1()
    print(f"   P1 = 0x{p1:02X} (binary: {p1:08b})")
    print(f"   Expected: 0xEF (buttons selected, no buttons pressed)")
    print(f"   Bits 0-3: {p1 & 0x0F:04b} (should be 1111 = not pressed)")

    # Press START
    print("\n3. Press START:")
    joypad.press_button('start')
    print(f"   button_start = {joypad.button_start}")

    p1 = joypad.read_p1()
    print(f"   P1 = 0x{p1:02X} (binary: {p1:08b})")
    print(f"   Expected: 0xE7 (bit 3 should be 0)")
    print(f"   Bit 3: {(p1 >> 3) & 1} (should be 0 = pressed)")

    if (p1 & 0x08) == 0:
        print("   ✅ START correctly shows as pressed!")
    else:
        print("   ❌ START NOT detected - BUG IN JOYPAD!")

    # Debug the read_p1 function
    print("\n4. Detailed trace of read_p1():")
    print(f"   select_buttons = {joypad.select_buttons}")
    print(f"   select_dpad = {joypad.select_dpad}")
    print(f"   button_start = {joypad.button_start}")

    # Manually calculate what result should be
    result = 0xCF  # 11001111
    print(f"   Initial result: 0x{result:02X}")

    if not joypad.select_buttons:
        result |= 0x20
        print(f"   After button select check: 0x{result:02X}")

    if not joypad.select_dpad:
        result |= 0x10
        print(f"   After dpad select check: 0x{result:02X}")

    # We're in the elif self.select_buttons branch
    if joypad.select_buttons and not joypad.select_dpad:
        print("   In 'select_buttons only' branch")

        if joypad.button_start:
            print(f"   button_start is True, clearing bit 3")
            result &= ~0x08
            print(f"   Result after clearing bit 3: 0x{result:02X}")

    print(f"   Final result: 0x{result:02X}")
    print(f"   Actual P1: 0x{p1:02X}")

    if result == p1:
        print("   ✅ Manual calculation matches!")
    else:
        print(f"   ❌ MISMATCH! Expected {result:02X}, got {p1:02X}")

if __name__ == '__main__':
    test_joypad_directly()
