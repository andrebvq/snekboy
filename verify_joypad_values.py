"""
Verify exact joypad values being read
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

def verify_joypad():
    """Verify joypad values"""
    print("="*70)
    print("VERIFYING JOYPAD VALUES")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    # Test joypad reads WITHOUT button pressed
    print(f"\n1. Testing joypad reads with NO buttons pressed:")

    # Write to P1 to select buttons
    cpu.memory.write_byte(0xFF00, 0x10)  # Select button keys (bit 4 = 0)
    p1_buttons_no_press = cpu.memory.read_byte(0xFF00)
    print(f"   P1 after writing 0x10 (select buttons): 0x{p1_buttons_no_press:02X} = 0b{p1_buttons_no_press:08b}")
    print(f"     Bit 3 (START): {(p1_buttons_no_press >> 3) & 1} (1=not pressed, 0=pressed)")
    print(f"     Bit 2 (SELECT): {(p1_buttons_no_press >> 2) & 1}")
    print(f"     Bit 1 (B): {(p1_buttons_no_press >> 1) & 1}")
    print(f"     Bit 0 (A): {(p1_buttons_no_press >> 0) & 1}")

    # Write to P1 to select dpad
    cpu.memory.write_byte(0xFF00, 0x20)  # Select direction keys (bit 5 = 0)
    p1_dpad_no_press = cpu.memory.read_byte(0xFF00)
    print(f"   P1 after writing 0x20 (select dpad): 0x{p1_dpad_no_press:02X} = 0b{p1_dpad_no_press:08b}")
    print(f"     Bit 3 (DOWN): {(p1_dpad_no_press >> 3) & 1}")
    print(f"     Bit 2 (UP): {(p1_dpad_no_press >> 2) & 1}")
    print(f"     Bit 1 (LEFT): {(p1_dpad_no_press >> 1) & 1}")
    print(f"     Bit 0 (RIGHT): {(p1_dpad_no_press >> 0) & 1}")

    # Now test WITH START pressed
    print(f"\n2. Testing joypad reads WITH START pressed:")

    cpu.memory.joypad.press_button('start')

    cpu.memory.write_byte(0xFF00, 0x10)  # Select button keys
    p1_buttons_with_start = cpu.memory.read_byte(0xFF00)
    print(f"   P1 after writing 0x10 (select buttons): 0x{p1_buttons_with_start:02X} = 0b{p1_buttons_with_start:08b}")
    print(f"     Bit 3 (START): {(p1_buttons_with_start >> 3) & 1} (expected 0 when pressed)")
    print(f"     Bit 2 (SELECT): {(p1_buttons_with_start >> 2) & 1}")
    print(f"     Bit 1 (B): {(p1_buttons_with_start >> 1) & 1}")
    print(f"     Bit 0 (A): {(p1_buttons_with_start >> 0) & 1}")

    if p1_buttons_with_start != p1_buttons_no_press:
        print(f"\n   START button IS being detected!")
        print(f"   Value changed from 0x{p1_buttons_no_press:02X} to 0x{p1_buttons_with_start:02X}")
    else:
        print(f"\n   ERROR: START button NOT detected - value unchanged!")

    cpu.memory.joypad.release_button('start')

    # Test other buttons
    print(f"\n3. Testing A button:")
    cpu.memory.joypad.press_button('a')
    cpu.memory.write_byte(0xFF00, 0x10)
    p1_with_a = cpu.memory.read_byte(0xFF00)
    print(f"   P1 with A pressed: 0x{p1_with_a:02X} = 0b{p1_with_a:08b}")
    print(f"     Bit 0 (A): {(p1_with_a >> 0) & 1} (expected 0)")
    cpu.memory.joypad.release_button('a')

    print(f"\n4. Testing RIGHT button:")
    cpu.memory.joypad.press_button('right')
    cpu.memory.write_byte(0xFF00, 0x20)
    p1_with_right = cpu.memory.read_byte(0xFF00)
    print(f"   P1 with RIGHT pressed: 0x{p1_with_right:02X} = 0b{p1_with_right:08b}")
    print(f"     Bit 0 (RIGHT): {(p1_with_right >> 0) & 1} (expected 0)")
    cpu.memory.joypad.release_button('right')

    # Monitor game's joypad polling
    print(f"\n5. Monitoring game's joypad polling with START pressed:")

    cpu.memory.joypad.press_button('start')

    p1_writes = []
    p1_reads = []

    original_write = cpu.memory.write_byte
    original_read = cpu.memory.read_byte

    def traced_write(address, value):
        if address == 0xFF00:
            p1_writes.append((cpu.total_cycles, value, cpu.registers._pc))
        return original_write(address, value)

    def traced_read(address):
        result = original_read(address)
        if address == 0xFF00:
            p1_reads.append((cpu.total_cycles, result, cpu.registers._pc))
        return result

    cpu.memory.write_byte = traced_write
    cpu.memory.read_byte = traced_read

    for _ in range(100_000):
        cpu.step()

    print(f"   P1 writes in 100k cycles: {len(p1_writes)}")
    print(f"   P1 reads in 100k cycles: {len(p1_reads)}")

    if p1_writes:
        print(f"\n   Last 10 P1 writes:")
        for cycle, value, pc in p1_writes[-10:]:
            print(f"     Cycle {cycle:8d}: PC=0x{pc:04X} wrote 0x{value:02X}")

    if p1_reads:
        print(f"\n   Last 10 P1 reads:")
        for cycle, value, pc in p1_reads[-10:]:
            start_bit = (value >> 3) & 1
            print(f"     Cycle {cycle:8d}: PC=0x{pc:04X} read 0x{value:02X} (START bit={start_bit})")


if __name__ == '__main__':
    verify_joypad()
