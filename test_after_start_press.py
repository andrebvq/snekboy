"""
Test if pressing START triggers VRAM updates
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

def test_start_press():
    """Test START button press"""
    print("="*70)
    print("TESTING START BUTTON WITH VRAM TRACKING")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    vram_writes_before = []
    vram_writes_during = []
    vram_writes_after = []

    original_write = cpu.memory.write_byte

    stage = 'before'

    def traced_write(address, value):
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            write_info = {
                'cycle': cpu.total_cycles,
                'pc': cpu.registers._pc,
                'address': address,
                'value': value
            }

            if stage == 'before':
                vram_writes_before.append(write_info)
            elif stage == 'during':
                vram_writes_during.append(write_info)
            else:
                vram_writes_after.append(write_info)

        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Run to 2M cycles (stable state)
    print("\n1. Running to 2M cycles (before START)...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    screen1 = cpu.ppu.get_screen_buffer()
    pixels1 = sum(1 for row in screen1 for pixel in row if pixel != 0)

    print(f"   Pixels: {pixels1:,}")
    print(f"   VRAM writes: {len(vram_writes_before)}")

    # Press START
    print("\n2. Pressing START...")
    stage = 'during'
    cpu.memory.joypad.press_button('start')

    for _ in range(100_000):
        cpu.step()

    print(f"   VRAM writes during press: {len(vram_writes_during)}")

    # Release and continue
    print("\n3. Releasing START and continuing...")
    cpu.memory.joypad.release_button('start')
    stage = 'after'

    for _ in range(500_000):
        cpu.step()

    screen2 = cpu.ppu.get_screen_buffer()
    pixels2 = sum(1 for row in screen2 for pixel in row if pixel != 0)

    print(f"   Pixels: {pixels2:,}")
    print(f"   VRAM writes after press: {len(vram_writes_after)}")

    # Results
    print(f"\n" + "="*70)
    print("RESULTS")
    print("="*70)

    print(f"\nVRAM writes:")
    print(f"  Before START: {len(vram_writes_before)}")
    print(f"  During START: {len(vram_writes_during)}")
    print(f"  After START: {len(vram_writes_after)}")

    if vram_writes_during or vram_writes_after:
        print(f"\n  SUCCESS! Game is writing to VRAM!")

        if vram_writes_during:
            print(f"\n  First 10 writes during START:")
            for i, write in enumerate(vram_writes_during[:10]):
                print(f"    {i+1}. Cycle {write['cycle']:8d}: [0x{write['address']:04X}]=0x{write['value']:02X}")

        if vram_writes_after:
            print(f"\n  First 10 writes after START:")
            for i, write in enumerate(vram_writes_after[:10]):
                print(f"    {i+1}. Cycle {write['cycle']:8d}: [0x{write['address']:04X}]=0x{write['value']:02X}")
    else:
        print(f"\n  No VRAM writes after START press")
        print(f"  Game still not responding to input")

    if pixels2 != pixels1:
        print(f"\nScreen changed: {pixels1} -> {pixels2} pixels")
    else:
        print(f"\nScreen unchanged: {pixels1} pixels")


if __name__ == '__main__':
    test_start_press()
