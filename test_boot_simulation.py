"""
Test if boot ROM simulation fixes Tetris frozen screen
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

def test_with_boot_simulation():
    """Test if boot ROM simulation fixes the frozen screen"""
    print("="*70)
    print("TESTING WITH BOOT ROM SIMULATION")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Simulate boot ROM
    print("\nSimulating boot ROM...")
    cpu.simulate_boot()

    # Check VRAM was cleared
    print("\nChecking VRAM after boot simulation:")
    vram_zeros = sum(1 for addr in range(0x8000, 0xA000)
                     if cpu.memory.read_byte(addr) == 0x00)
    print(f"  VRAM zeros: {vram_zeros}/8192 ({vram_zeros*100/8192:.1f}%)")

    if vram_zeros == 8192:
        print("  VRAM completely cleared!")
    else:
        print(f"  VRAM not fully cleared - {8192-vram_zeros} non-zero bytes remain")

    # Check registers
    print(f"\nPost-boot register state:")
    print(f"  A: 0x{cpu.registers._a:02X} (expected 0x01)")
    print(f"  BC: 0x{cpu.registers._b:02X}{cpu.registers._c:02X} (expected 0x0013)")
    print(f"  DE: 0x{cpu.registers._d:02X}{cpu.registers._e:02X} (expected 0x00D8)")
    print(f"  HL: 0x{cpu.registers._h:02X}{cpu.registers._l:02X} (expected 0x014D)")
    print(f"  PC: 0x{cpu.registers._pc:04X} (expected 0x0100)")
    print(f"  SP: 0x{cpu.registers._sp:04X} (expected 0xFFFE)")
    print(f"  F: 0x{cpu.registers.flags.to_byte():02X} (expected 0xB0)")

    # Check LCD registers
    print(f"\nLCD register state:")
    print(f"  LCDC (0xFF40): 0x{cpu.memory.read_byte(0xFF40):02X} (expected 0x91)")
    print(f"  BGP (0xFF47): 0x{cpu.memory.read_byte(0xFF47):02X} (expected 0xFC)")
    print(f"  OBP0 (0xFF48): 0x{cpu.memory.read_byte(0xFF48):02X} (expected 0xFF)")
    print(f"  FF50 (boot disable): 0x{cpu.memory.read_byte(0xFF50):02X} (expected 0x01)")

    # Run to 1M cycles and check screen
    print("\n1. Running to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    screen1 = cpu.ppu.get_screen_buffer()
    pixels1 = sum(1 for row in screen1 for pixel in row if pixel != 0)

    print(f"   Non-bg pixels: {pixels1:,}")

    # Check for vertical stripe pattern
    stripe_lines = 0
    for y in range(144):
        row = screen1[y]
        # Stripes have repeating pattern every 8 pixels
        is_stripe = all(row[x] == row[x % 8] for x in range(160))
        if is_stripe and any(row[x] != 0 for x in range(8)):
            stripe_lines += 1

    if stripe_lines > 100:
        print(f"   Stripes detected on {stripe_lines} lines")
    else:
        print(f"   No obvious stripe pattern - looks normal!")

    # Run to 2M cycles
    print("\n2. Running to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    screen2 = cpu.ppu.get_screen_buffer()
    pixels2 = sum(1 for row in screen2 for pixel in row if pixel != 0)

    print(f"   Non-bg pixels: {pixels2:,}")

    changes = sum(1 for y in range(144) for x in range(160)
                  if screen1[y][x] != screen2[y][x])

    if changes > 0:
        print(f"   Screen CHANGED: {changes} pixels different!")
    else:
        print(f"   Screen UNCHANGED")

    # Press START
    print("\n3. Pressing START button...")
    cpu.memory.joypad.press_button('start')

    for _ in range(50_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    for _ in range(300_000):
        cpu.step()

    screen3 = cpu.ppu.get_screen_buffer()
    pixels3 = sum(1 for row in screen3 for pixel in row if pixel != 0)

    print(f"   Pixels after START: {pixels3:,}")

    changes2 = sum(1 for y in range(144) for x in range(160)
                   if screen2[y][x] != screen3[y][x])

    if changes2 > 0:
        print(f"   Screen CHANGED: {changes2} pixels different!")
    else:
        print(f"   Screen UNCHANGED")

    # Check for VRAM writes
    print("\n4. Monitoring VRAM writes...")

    vram_writes = []
    original_write = cpu.memory.write_byte

    def track_vram(address, value):
        if 0x8000 <= address <= 0x9FFF:
            vram_writes.append((cpu.total_cycles, address, value))
        return original_write(address, value)

    cpu.memory.write_byte = track_vram

    for _ in range(200_000):
        cpu.step()

    print(f"   VRAM writes in 200k cycles: {len(vram_writes)}")

    if vram_writes:
        print(f"   First 5 VRAM writes:")
        for i, (cycles, addr, value) in enumerate(vram_writes[:5]):
            print(f"     {i+1}. Cycle {cycles:8d}: [0x{addr:04X}] = 0x{value:02X}")

    # Final verdict
    print(f"\n" + "="*70)
    print("VERDICT")
    print("="*70)

    if vram_zeros == 8192:
        print("\nBoot ROM simulation: SUCCESS")
        print("  VRAM cleared correctly")
        print("  Registers initialized correctly")
    else:
        print("\nBoot ROM simulation: PARTIAL")
        print(f"  VRAM not fully cleared ({8192-vram_zeros} bytes remain)")

    if stripe_lines > 100:
        print("\nStripe problem: STILL PRESENT")
        print(f"  {stripe_lines}/144 lines show stripe pattern")
    else:
        print("\nStripe problem: FIXED")
        print("  No vertical stripes detected")

    if len(vram_writes) > 0:
        print(f"\nVRAM updates: YES")
        print(f"  {len(vram_writes)} writes detected")
        print("  Game IS updating graphics!")
    else:
        print(f"\nVRAM updates: NO")
        print("  Game still not writing to VRAM")

    if pixels3 != pixels1:
        print(f"\nScreen animation: YES")
        print(f"  Pixels changed from {pixels1} to {pixels3}")
    else:
        print(f"\nScreen animation: NO")
        print(f"  Screen still frozen at {pixels1} pixels")


if __name__ == '__main__':
    test_with_boot_simulation()
