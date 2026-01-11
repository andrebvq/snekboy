"""
Test all button presses to see if any trigger VRAM updates
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

def test_all_buttons():
    """Test all button combinations"""
    print("="*70)
    print("TESTING ALL BUTTONS")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    vram_writes = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            vram_writes.append({
                'cycle': cpu.total_cycles,
                'button': traced_write.current_button,
                'address': address,
                'value': value
            })
        return original_write(address, value)

    traced_write.current_button = 'none'
    cpu.memory.write_byte = traced_write

    # Run to stable state
    print("\nRunning to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    screen1 = cpu.ppu.get_screen_buffer()
    pixels1 = sum(1 for row in screen1 for pixel in row if pixel != 0)
    print(f"   Initial pixels: {pixels1:,}")
    print(f"   Boot VRAM writes: {len(vram_writes)}")

    initial_writes = len(vram_writes)

    # Try each button
    buttons = ['start', 'select', 'a', 'b', 'up', 'down', 'left', 'right']

    for button in buttons:
        print(f"\n  Testing {button.upper()} button...")
        traced_write.current_button = button

        # Press button
        cpu.memory.joypad.press_button(button)

        # Hold for a while
        for _ in range(50_000):
            cpu.step()

        # Release
        cpu.memory.joypad.release_button(button)

        # Wait a bit more
        for _ in range(50_000):
            cpu.step()

        writes_this_button = len(vram_writes) - initial_writes
        print(f"     VRAM writes: {writes_this_button}")

        if writes_this_button > 0:
            print(f"     SUCCESS! {button.upper()} triggered VRAM writes!")

    # Also try waiting without any input
    print(f"\n  Waiting 500k cycles with no input...")
    traced_write.current_button = 'waiting'

    for _ in range(500_000):
        cpu.step()

    writes_while_waiting = len(vram_writes) - initial_writes - sum(
        1 for w in vram_writes[initial_writes:] if w['button'] in buttons
    )

    if writes_while_waiting > 0:
        print(f"     VRAM writes while waiting: {writes_while_waiting}")

    # Final results
    print(f"\n" + "="*70)
    print("RESULTS")
    print("="*70)

    total_new_writes = len(vram_writes) - initial_writes

    print(f"\nTotal VRAM writes after boot: {total_new_writes}")

    if total_new_writes > 0:
        print(f"\nBreakdown by trigger:")
        for button in buttons + ['waiting']:
            count = sum(1 for w in vram_writes[initial_writes:] if w['button'] == button)
            if count > 0:
                print(f"  {button}: {count} writes")

        print(f"\nFirst 10 new VRAM writes:")
        for i, write in enumerate(vram_writes[initial_writes:initial_writes+10]):
            print(f"  {i+1}. Cycle {write['cycle']:8d}: trigger={write['button']} [0x{write['address']:04X}]=0x{write['value']:02X}")
    else:
        print(f"\nNo VRAM writes detected after boot")
        print(f"Game is not responding to any input")

    # Check screen changes
    screen2 = cpu.ppu.get_screen_buffer()
    pixels2 = sum(1 for row in screen2 for pixel in row if pixel != 0)

    if pixels2 != pixels1:
        print(f"\nScreen changed: {pixels1} -> {pixels2} pixels")
    else:
        print(f"\nScreen unchanged: {pixels1} pixels")


if __name__ == '__main__':
    test_all_buttons()
