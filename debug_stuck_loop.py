"""
Debug why the game is stuck in a loop at 0x02ED
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def debug_stuck_loop():
    print("="*70)
    print("DEBUGGING STUCK LOOP")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Run to the point where it gets stuck
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    print(f"\nAt {cpu.total_cycles:,} cycles")
    print(f"PC: 0x{cpu.registers._pc:04X}")

    # Check the flag it's waiting for
    flag_value = cpu.memory.read_byte(0xFF85)
    print(f"\n0xFF85 (flag being waited on): 0x{flag_value:02X}")

    # Check nearby HRAM
    print(f"\nHRAM around 0xFF85:")
    for addr in range(0xFF80, 0xFF90):
        value = cpu.memory.read_byte(addr)
        print(f"  0x{addr:04X}: 0x{value:02X}")

    # Check VBlank interrupt status
    ie = cpu.memory.read_byte(0xFFFF)
    if_flags = cpu.memory.read_byte(0xFF0F)
    print(f"\nInterrupts:")
    print(f"  IE: 0x{ie:02X} (VBlank={bool(ie&1)}, LCD={bool(ie&2)}, Timer={bool(ie&4)})")
    print(f"  IF: 0x{if_flags:02X} (VBlank={bool(if_flags&1)}, LCD={bool(if_flags&2)}, Timer={bool(if_flags&4)})")
    print(f"  IME: {cpu.ime}")

    # Monitor the loop for a bit
    print(f"\nMonitoring 0xFF85 for changes...")

    prev_value = flag_value
    loop_iterations = 0

    for _ in range(1_000_000):
        cpu.step()

        current_value = cpu.memory.read_byte(0xFF85)

        if current_value != prev_value:
            print(f"  0xFF85 changed: 0x{prev_value:02X} -> 0x{current_value:02X} at cycle {cpu.total_cycles}")
            prev_value = current_value

        # Check if we're still at the same PC (in the loop)
        if cpu.registers._pc == 0x02ED:
            loop_iterations += 1

    print(f"\nLoop iterations detected: {loop_iterations:,}")

    # Check if it ever left the loop
    print(f"Final PC: 0x{cpu.registers._pc:04X}")
    print(f"Final 0xFF85: 0x{cpu.memory.read_byte(0xFF85):02X}")

    # Check when VBlank interrupt fires
    print(f"\nChecking VBlank interrupt behavior...")

    vblank_count = 0
    prev_if = cpu.memory.read_byte(0xFF0F)

    for _ in range(100_000):
        cpu.step()

        current_if = cpu.memory.read_byte(0xFF0F)

        # Check if VBlank bit went from 0 to 1
        if (current_if & 1) and not (prev_if & 1):
            vblank_count += 1
            print(f"  VBlank interrupt fired at cycle {cpu.total_cycles}")

            if vblank_count >= 3:
                break

        prev_if = current_if

    print(f"\nVBlank interrupts detected: {vblank_count}")

    # The game might be waiting for VBlank to set this flag
    # Let's check if there's a VBlank handler that should set 0xFF85
    print(f"\nChecking VBlank interrupt handler...")

    # VBlank vector is at 0x0040
    vblank_vector = 0x0040

    print(f"Code at VBlank handler (0x{vblank_vector:04X}):")
    for i in range(16):
        byte = cpu.memory.read_byte(vblank_vector + i)
        print(f"  0x{vblank_vector+i:04X}: 0x{byte:02X}")


if __name__ == '__main__':
    debug_stuck_loop()
