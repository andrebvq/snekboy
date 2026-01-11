"""
Detailed joypad debugging - check if button presses are being detected
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

def test_joypad_detection():
    """Test if joypad input is being detected correctly"""
    print("="*70)
    print("JOYPAD DETECTION TEST")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot to menu
    print("\n1. Booting to menu...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    print(f"\nAt {cpu.total_cycles:,} cycles (menu screen)")

    # Check joypad state BEFORE pressing anything
    print("\n--- BEFORE pressing START ---")
    print(f"Joypad internal state: {cpu.memory.joypad.get_state_string()}")
    print(f"P1 register: 0x{cpu.memory.read_byte(0xFF00):02X}")

    # Have game read joypad (simulate what game does)
    # First select button keys
    cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons (bit 5 = 0)
    p1_buttons = cpu.memory.read_byte(0xFF00)
    print(f"P1 after selecting buttons: 0x{p1_buttons:02X}")

    # Then select dpad
    cpu.memory.write_byte(0xFF00, 0x10)  # Select dpad (bit 4 = 0)
    p1_dpad = cpu.memory.read_byte(0xFF00)
    print(f"P1 after selecting dpad: 0x{p1_dpad:02X}")

    # Now press START
    print("\n--- PRESSING START ---")
    cpu.memory.joypad.press_button('start')
    print(f"Joypad internal state: {cpu.memory.joypad.get_state_string()}")

    # Check IF register
    if_before = cpu.memory.read_byte(0xFF0F)
    print(f"IF register: 0x{if_before:02X} (Joypad bit: {bool(if_before & 0x10)})")

    # Read P1 again
    cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons
    p1_buttons = cpu.memory.read_byte(0xFF00)
    print(f"P1 with buttons selected: 0x{p1_buttons:02X}")
    print(f"  Bit 3 (START): {(p1_buttons >> 3) & 1} (0=pressed, 1=not pressed)")
    print(f"  Bit 2 (SELECT): {(p1_buttons >> 2) & 1}")
    print(f"  Bit 1 (B): {(p1_buttons >> 1) & 1}")
    print(f"  Bit 0 (A): {p1_buttons & 1}")

    # Run a few cycles to let interrupt propagate
    print("\nRunning 1000 cycles...")
    for _ in range(1000):
        cpu.step()

    # Check state after
    if_after = cpu.memory.read_byte(0xFF0F)
    print(f"IF register after: 0x{if_after:02X}")

    # Release START
    print("\n--- RELEASING START ---")
    cpu.memory.joypad.release_button('start')
    print(f"Joypad internal state: {cpu.memory.joypad.get_state_string()}")

    cpu.memory.write_byte(0xFF00, 0x20)  # Select buttons
    p1_buttons = cpu.memory.read_byte(0xFF00)
    print(f"P1 with buttons selected: 0x{p1_buttons:02X}")
    print(f"  Bit 3 (START): {(p1_buttons >> 3) & 1}")

    # Now test if the game's interrupt handler would work
    print("\n" + "="*70)
    print("INTERRUPT ENABLE CHECK")
    print("="*70)

    ie = cpu.memory.read_byte(0xFFFF)
    print(f"IE register: 0x{ie:02X}")
    print(f"  VBlank enabled: {bool(ie & 0x01)}")
    print(f"  LCD enabled: {bool(ie & 0x02)}")
    print(f"  Timer enabled: {bool(ie & 0x04)}")
    print(f"  Serial enabled: {bool(ie & 0x08)}")
    print(f"  Joypad enabled: {bool(ie & 0x10)}")

    print(f"\nIME (Master interrupt enable): {cpu.ime}")

    # Check if joypad interrupt would be serviced
    if_flags = cpu.memory.read_byte(0xFF0F)
    triggered = ie & if_flags & 0x1F
    print(f"\nTriggered interrupts (IE & IF): 0x{triggered:02X}")

    if triggered & 0x10:
        print("  -> Joypad interrupt is REQUESTED and ENABLED - should be serviced!")
    elif if_flags & 0x10:
        print("  -> Joypad interrupt is REQUESTED but NOT ENABLED in IE")
    else:
        print("  -> No joypad interrupt pending")

    # Manual test: Try to trigger joypad interrupt multiple times
    print("\n" + "="*70)
    print("RAPID BUTTON PRESS TEST")
    print("="*70)

    for i in range(5):
        print(f"\nPress {i+1}:")
        cpu.memory.joypad.press_button('start')

        # Run a bit
        for _ in range(1000):
            cpu.step()

        if_flags = cpu.memory.read_byte(0xFF0F)
        print(f"  IF: 0x{if_flags:02X}")

        cpu.memory.joypad.release_button('start')

        for _ in range(1000):
            cpu.step()


if __name__ == '__main__':
    test_joypad_detection()
