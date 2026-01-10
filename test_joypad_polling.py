"""
Test if joypad polling works correctly
"""
import sys
sys.path.insert(0, '.')

from src.joypad import Joypad

# Create joypad
joypad = Joypad()

print("Testing joypad button reading...")
print()

# Test 1: No buttons pressed
print("Test 1: No buttons, selecting button group")
joypad.write_p1(0x10)  # Select button keys (bit 5 = 0, bit 4 = 1)
result = joypad.read_p1()
print(f"  Write: 0x10")
print(f"  Read:  0x{result:02X}")
print(f"  Binary: {result:08b}")
print(f"  Bit 3 (Start):  {(result >> 3) & 1} (expect 1 = not pressed)")
print(f"  Bit 2 (Select): {(result >> 2) & 1} (expect 1 = not pressed)")
print(f"  Bit 1 (B):      {(result >> 1) & 1} (expect 1 = not pressed)")
print(f"  Bit 0 (A):      {(result >> 0) & 1} (expect 1 = not pressed)")
print()

# Test 2: Press START button
print("Test 2: Press START, selecting button group")
joypad.press_button('start')
joypad.write_p1(0x10)  # Select button keys
result = joypad.read_p1()
print(f"  Write: 0x10")
print(f"  Read:  0x{result:02X}")
print(f"  Binary: {result:08b}")
print(f"  Bit 3 (Start):  {(result >> 3) & 1} (expect 0 = pressed)")
print(f"  Bit 2 (Select): {(result >> 2) & 1} (expect 1 = not pressed)")
print(f"  Bit 1 (B):      {(result >> 1) & 1} (expect 1 = not pressed)")
print(f"  Bit 0 (A):      {(result >> 0) & 1} (expect 1 = not pressed)")
print()

# Test 3: Select d-pad while START is pressed (should read all 1s for dpad)
print("Test 3: START still pressed, but select d-pad group")
joypad.write_p1(0x20)  # Select direction keys (bit 5 = 1, bit 4 = 0)
result = joypad.read_p1()
print(f"  Write: 0x20")
print(f"  Read:  0x{result:02X}")
print(f"  Binary: {result:08b}")
print(f"  Bit 3 (Down):  {(result >> 3) & 1} (expect 1 = not pressed)")
print(f"  Bit 2 (Up):    {(result >> 2) & 1} (expect 1 = not pressed)")
print(f"  Bit 1 (Left):  {(result >> 1) & 1} (expect 1 = not pressed)")
print(f"  Bit 0 (Right): {(result >> 0) & 1} (expect 1 = not pressed)")
print()

# Test 4: Press A button too
print("Test 4: Press A, select button group")
joypad.press_button('a')
joypad.write_p1(0x10)
result = joypad.read_p1()
print(f"  Write: 0x10")
print(f"  Read:  0x{result:02X}")
print(f"  Binary: {result:08b}")
print(f"  Bit 3 (Start):  {(result >> 3) & 1} (expect 0 = pressed)")
print(f"  Bit 2 (Select): {(result >> 2) & 1} (expect 1 = not pressed)")
print(f"  Bit 1 (B):      {(result >> 1) & 1} (expect 1 = not pressed)")
print(f"  Bit 0 (A):      {(result >> 0) & 1} (expect 0 = pressed)")
print()

# Test 5: Release START
print("Test 5: Release START, only A pressed")
joypad.release_button('start')
joypad.write_p1(0x10)
result = joypad.read_p1()
print(f"  Write: 0x10")
print(f"  Read:  0x{result:02X}")
print(f"  Binary: {result:08b}")
print(f"  Bit 3 (Start):  {(result >> 3) & 1} (expect 1 = not pressed)")
print(f"  Bit 2 (Select): {(result >> 2) & 1} (expect 1 = not pressed)")
print(f"  Bit 1 (B):      {(result >> 1) & 1} (expect 1 = not pressed)")
print(f"  Bit 0 (A):      {(result >> 0) & 1} (expect 0 = pressed)")
