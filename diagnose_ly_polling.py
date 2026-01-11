"""
Quick diagnostic: what LY values does game read when LCD is OFF?
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

def diagnose_ly():
    """Quick test of LY when LCD OFF"""
    print("="*70)
    print("LY POLLING DIAGNOSTIC")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Test: Turn off LCD and see if LY advances
    print("\n1. Testing LY advancement when LCD is OFF...")

    # Manually turn off LCD
    cpu.memory.write_byte(0xFF40, 0x00)  # Turn OFF
    print(f"   Turned LCD OFF at cycle {cpu.total_cycles:,}")

    # Check LY progression
    ly_values = []
    for _ in range(1000):
        ly = cpu.memory.read_byte(0xFF44)
        ly_values.append(ly)
        cpu.step()

    print(f"   LY values seen: {set(ly_values)}")
    print(f"   LY range: {min(ly_values)} to {max(ly_values)}")

    if len(set(ly_values)) > 1:
        print(f"   LY IS advancing when LCD OFF")
    else:
        print(f"   ERROR: LY is STUCK at {ly_values[0]}")

    # Turn LCD back ON
    cpu.memory.write_byte(0xFF40, 0x91)
    print(f"\n   Turned LCD ON at cycle {cpu.total_cycles:,}")

    ly_values_on = []
    for _ in range(1000):
        ly = cpu.memory.read_byte(0xFF44)
        ly_values_on.append(ly)
        cpu.step()

    print(f"   LY values when ON: {min(ly_values_on)} to {max(ly_values_on)}")

    # Now test with actual game
    print("\n2. Testing with actual game execution...")

    cpu2 = CPU()
    cpu2.memory.load_rom_file(TETRIS_ROM)
    cpu2.simulate_boot()

    # Run until LCD turns OFF
    print("   Running until LCD turns OFF...")

    lcd_off_cycle = None
    last_lcdc = cpu2.memory.read_byte(0xFF40)

    for _ in range(30_000_000):  # 30M cycles max
        cpu2.step()

        lcdc = cpu2.memory.read_byte(0xFF40)
        if (last_lcdc & 0x80) and not (lcdc & 0x80):
            # LCD just turned OFF
            lcd_off_cycle = cpu2.total_cycles
            ly_at_off = cpu2.memory.read_byte(0xFF44)
            print(f"   LCD turned OFF at cycle {lcd_off_cycle:,}, LY={ly_at_off}")
            break
        last_lcdc = lcdc

    if lcd_off_cycle is None:
        print("   LCD never turned OFF in 30M cycles!")
        return

    # Sample LY while LCD is OFF
    print("   Sampling LY while LCD is OFF...")

    ly_samples = []
    for i in range(10_000):
        if i % 100 == 0:
            ly = cpu2.memory.read_byte(0xFF44)
            ly_samples.append(ly)
        cpu2.step()

    print(f"   LY samples (every 100 steps): {set(ly_samples)}")
    print(f"   LY range: {min(ly_samples)} to {max(ly_samples)}")

    if max(ly_samples) - min(ly_samples) > 50:
        print(f"   LY is advancing correctly (range: {max(ly_samples) - min(ly_samples)})")
    else:
        print(f"   WARNING: LY range seems limited ({max(ly_samples) - min(ly_samples)})")

    # Check if LCD turns back ON
    print("\n   Checking if LCD turns back ON...")

    for i in range(10_000_000):  # 10M cycles
        cpu2.step()

        lcdc = cpu2.memory.read_byte(0xFF40)
        if lcdc & 0x80:
            # LCD turned back ON
            lcd_on_cycle = cpu2.total_cycles
            ly_at_on = cpu2.memory.read_byte(0xFF44)
            print(f"   LCD turned back ON at cycle {lcd_on_cycle:,}, LY={ly_at_on}")
            print(f"   LCD was OFF for {lcd_on_cycle - lcd_off_cycle:,} cycles")
            return

    print(f"   LCD did NOT turn back ON in 10M cycles")
    print(f"   Game is stuck with LCD OFF!")

    # Final diagnostic
    lcdc_final = cpu2.memory.read_byte(0xFF40)
    ly_final = cpu2.memory.read_byte(0xFF44)
    pc_final = cpu2.registers._pc

    print(f"\n   Final state:")
    print(f"     LCDC: 0x{lcdc_final:02X}")
    print(f"     LY: {ly_final}")
    print(f"     PC: 0x{pc_final:04X}")


if __name__ == '__main__':
    diagnose_ly()
