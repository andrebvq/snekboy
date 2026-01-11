"""
Focus on what happens when LCD turns OFF after stage select
"""

import sys
import os
import time

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def trace_lcd_off():
    """Trace LCD OFF period"""
    print("="*70)
    print("TRACING LCD OFF PERIOD")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Track LCD state changes
    lcd_state_changes = []
    vram_writes = []
    ly_at_lcd_off = []

    original_write = cpu.memory.write_byte

    def traced_write(address, value):
        # Track LCDC writes
        if address == 0xFF40:
            lcdc_before = cpu.memory._data[0xFF40]
            lcd_before = (lcdc_before & 0x80) != 0
            lcd_after = (value & 0x80) != 0

            if lcd_before != lcd_after:
                ly = cpu.memory.read_byte(0xFF44)
                lcd_state_changes.append({
                    'cycle': cpu.total_cycles,
                    'pc': cpu.registers._pc,
                    'lcdc': value,
                    'lcd_on': lcd_after,
                    'ly': ly
                })

                if not lcd_after:  # Turning OFF
                    ly_at_lcd_off.append(ly)

        # Track VRAM writes during LCD OFF
        if 0x8000 <= address <= 0x9FFF:
            lcdc = cpu.memory._data[0xFF40]
            if not (lcdc & 0x80):  # LCD is OFF
                vram_writes.append({
                    'cycle': cpu.total_cycles,
                    'pc': cpu.registers._pc,
                    'address': address,
                    'value': value
                })

        return original_write(address, value)

    cpu.memory.write_byte = traced_write

    # Run to stage select (give it time)
    print("\n1. Running to stage select (25M cycles)...")
    start_time = time.time()
    last_update = start_time

    while cpu.total_cycles < 25_000_000:
        cpu.step()

        now = time.time()
        if now - last_update >= 10.0:
            elapsed = now - start_time
            print(f"   {elapsed:.0f}s - {cpu.total_cycles:,} cycles")
            last_update = now

    print(f"   Reached stage select in {time.time() - start_time:.0f}s")

    # Check LCD state changes so far
    print(f"\n   LCD state changes so far: {len(lcd_state_changes)}")
    if lcd_state_changes:
        for i, change in enumerate(lcd_state_changes[-5:]):
            status = "ON" if change['lcd_on'] else "OFF"
            print(f"     {i+1}. Cycle {change['cycle']:10d}: LCD {status} (LY={change['ly']})")

    # Press START
    print("\n2. Pressing START...")
    cpu.memory.joypad.press_button('start')

    # Run and watch for LCD to turn OFF
    print("   Waiting for LCD to turn OFF...")

    lcd_off_cycle = None
    start_time = time.time()
    timeout = start_time + 120  # 2 minute timeout

    while time.time() < timeout:
        cpu.step()

        # Check if LCD just turned OFF
        if lcd_state_changes:
            last_change = lcd_state_changes[-1]
            if not last_change['lcd_on'] and lcd_off_cycle is None:
                lcd_off_cycle = last_change['cycle']
                if lcd_off_cycle > 25_000_000:  # After our initial run
                    print(f"   LCD turned OFF at cycle {lcd_off_cycle:,}!")
                    print(f"   LY at LCD OFF: {last_change['ly']}")
                    break

    if lcd_off_cycle is None:
        print("   ERROR: LCD never turned OFF!")
        return

    # Now run for a while with LCD OFF and watch what happens
    print("\n3. Running with LCD OFF (monitoring VRAM writes)...")

    target = cpu.total_cycles + 5_000_000  # 5M more cycles
    start_time = time.time()
    last_update = start_time

    while cpu.total_cycles < target:
        cpu.step()

        now = time.time()
        if now - last_update >= 5.0:
            elapsed = now - start_time
            ly = cpu.memory.read_byte(0xFF44)
            lcdc = cpu.memory.read_byte(0xFF40)
            lcd_status = "ON" if (lcdc & 0x80) else "OFF"
            print(f"   {elapsed:.0f}s - Cycle {cpu.total_cycles:,} - LY={ly} LCD={lcd_status}")
            last_update = now

    # Results
    print(f"\n" + "="*70)
    print("RESULTS")
    print("="*70)

    print(f"\nLCD state changes: {len(lcd_state_changes)}")
    print(f"  Last 10 changes:")
    for change in lcd_state_changes[-10:]:
        status = "ON" if change['lcd_on'] else "OFF"
        print(f"    Cycle {change['cycle']:10d}: PC=0x{change['pc']:04X} LCD {status} (LY={change['ly']}) LCDC=0x{change['lcdc']:02X}")

    # Check if LCD ever turned back ON
    lcd_off_count = sum(1 for c in lcd_state_changes if not c['lcd_on'])
    lcd_on_count = sum(1 for c in lcd_state_changes if c['lcd_on'])

    print(f"\n  LCD turned OFF: {lcd_off_count} times")
    print(f"  LCD turned ON: {lcd_on_count} times")

    if lcd_state_changes:
        final_state = lcd_state_changes[-1]
        if not final_state['lcd_on']:
            print(f"\n  WARNING: LCD is still OFF!")
            print(f"  Last turned OFF at cycle {final_state['cycle']:,}")

    # VRAM writes during LCD OFF
    vram_during_off = [w for w in vram_writes if w['cycle'] > lcd_off_cycle]

    print(f"\nVRAM writes during LCD OFF: {len(vram_during_off)}")
    if vram_during_off:
        print(f"  First 20 writes:")
        for i, write in enumerate(vram_during_off[:20]):
            print(f"    {i+1:3d}. Cycle {write['cycle']:10d}: PC=0x{write['pc']:04X} [0x{write['address']:04X}]=0x{write['value']:02X}")
    else:
        print(f"  NO VRAM writes during LCD OFF!")
        print(f"  This is the problem - game should write to VRAM when LCD is OFF")

    # Final state
    lcdc = cpu.memory.read_byte(0xFF40)
    ly = cpu.memory.read_byte(0xFF44)
    print(f"\nFinal state:")
    print(f"  LCDC: 0x{lcdc:02X} (LCD {'ON' if lcdc & 0x80 else 'OFF'})")
    print(f"  LY: {ly}")
    print(f"  PC: 0x{cpu.registers._pc:04X}")


if __name__ == '__main__':
    trace_lcd_off()
