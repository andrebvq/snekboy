"""
Test joypad implementation
"""

from src.joypad import Joypad

print("Testing Joypad Implementation")
print("="*60)

joypad = Joypad()

# Test 1: Default state (no buttons pressed)
print("\nTest 1: Default state")
print(f"  P1 (no selection): 0x{joypad.read_p1():02X}")
assert joypad.read_p1() == 0xFF, "Expected 0xFF when nothing selected"
print("  [PASS]")

# Test 2: Select button keys and press A
print("\nTest 2: Press A button")
joypad.write_p1(0xDF)  # Select button keys (bit 5 = 0)
joypad.press_button('a')
p1_value = joypad.read_p1()
print(f"  P1 with A pressed: 0x{p1_value:02X}")
# Should be: 11011110 = 0xDE (bit 0 = 0 for A pressed)
assert (p1_value & 0x01) == 0, "Bit 0 should be 0 when A is pressed"
print("  [PASS]")

# Test 3: Release A, press Start
print("\nTest 3: Press Start button")
joypad.release_button('a')
joypad.press_button('start')
p1_value = joypad.read_p1()
print(f"  P1 with Start pressed: 0x{p1_value:02X}")
# Should have bit 3 = 0 for Start
assert (p1_value & 0x08) == 0, "Bit 3 should be 0 when Start is pressed"
print("  [PASS]")

# Test 4: Select D-pad and press Right
print("\nTest 4: Press Right on D-pad")
joypad.release_all()
joypad.write_p1(0xEF)  # Select direction keys (bit 4 = 0)
joypad.press_button('right')
p1_value = joypad.read_p1()
print(f"  P1 with Right pressed: 0x{p1_value:02X}")
# Should have bit 0 = 0 for Right
assert (p1_value & 0x01) == 0, "Bit 0 should be 0 when Right is pressed"
print("  [PASS]")

# Test 5: Press Up on D-pad
print("\nTest 5: Press Up on D-pad")
joypad.release_all()
joypad.press_button('up')
p1_value = joypad.read_p1()
print(f"  P1 with Up pressed: 0x{p1_value:02X}")
# Should have bit 2 = 0 for Up
assert (p1_value & 0x04) == 0, "Bit 2 should be 0 when Up is pressed"
print("  [PASS]")

# Test 6: Press multiple buttons
print("\nTest 6: Press A + B together")
joypad.release_all()
joypad.write_p1(0xDF)  # Select button keys
joypad.press_button('a')
joypad.press_button('b')
p1_value = joypad.read_p1()
print(f"  P1 with A+B pressed: 0x{p1_value:02X}")
# Both bit 0 (A) and bit 1 (B) should be 0
assert (p1_value & 0x01) == 0, "Bit 0 should be 0 for A"
assert (p1_value & 0x02) == 0, "Bit 1 should be 0 for B"
print("  [PASS]")

# Test 7: State string
print("\nTest 7: State string representation")
joypad.release_all()
joypad.press_button('a')
joypad.press_button('up')
state = joypad.get_state_string()
print(f"  State string: '{state}'")
assert 'A' in state and 'UP' in state, "State should show A and UP"
print("  [PASS]")

print("\n" + "="*60)
print("All joypad tests passed!")
print("\nJoypad button mapping:")
print("  A button:      'A' key")
print("  B button:      'S' key")
print("  Start button:  'Z' key")
print("  Select button: 'X' key")
print("  D-Pad Up:      'I' key")
print("  D-Pad Down:    'K' key")
print("  D-Pad Left:    'J' key")
print("  D-Pad Right:   'L' key")
