"""
Trace actual joypad reads/writes by the game
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

# Monkey patch to trace joypad access
original_write = None
original_read = None

joypad_writes = []
joypad_reads = []


def traced_write(address, value):
    if address == 0xFF00:
        joypad_writes.append((traced_write.cpu.total_cycles if traced_write.cpu else 0, value))
    return original_write(address, value)


def traced_read(address):
    result = original_read(address)
    if address == 0xFF00:
        joypad_reads.append((traced_read.cpu.total_cycles if traced_read.cpu else 0, result))
    return result


def test_joypad_usage():
    """Monitor how the game actually uses the joypad"""
    print("="*70)
    print("TRACING JOYPAD USAGE BY TETRIS")
    print("="*70)

    cpu = CPU()

    # Patch memory to trace joypad access
    global original_write, original_read
    original_write = cpu.memory.write_byte
    original_read = cpu.memory.read_byte

    traced_write.cpu = cpu
    traced_read.cpu = cpu

    cpu.memory.write_byte = traced_write
    cpu.memory.read_byte = traced_read

    cpu.memory.load_rom_file(TETRIS_ROM)

    print("\nBooting...")
    while cpu.total_cycles < 500_000:
        cpu.step()

    print(f"\nAfter boot ({cpu.total_cycles:,} cycles):")
    print(f"  Joypad writes: {len(joypad_writes)}")
    print(f"  Joypad reads: {len(joypad_reads)}")

    if joypad_writes:
        print("\nLast 10 joypad writes:")
        for cycles, value in joypad_writes[-10:]:
            print(f"    {cycles:8d}: wrote 0x{value:02X}")

    if joypad_reads:
        print("\nLast 10 joypad reads:")
        for cycles, value in joypad_reads[-10:]:
            print(f"    {cycles:8d}: read  0x{value:02X}")

    # Clear traces
    joypad_writes.clear()
    joypad_reads.clear()

    # Press START
    print("\n" + "="*70)
    print("Pressing START")
    print("="*70)

    cpu.memory.joypad.press_button('start')

    # Run and monitor
    for _ in range(100_000):
        cpu.step()

    print(f"\nAfter pressing START ({cpu.total_cycles:,} cycles):")
    print(f"  Joypad writes: {len(joypad_writes)}")
    print(f"  Joypad reads: {len(joypad_reads)}")

    if joypad_writes:
        print("\nJoypad writes during button press:")
        for cycles, value in joypad_writes[:20]:
            print(f"    {cycles:8d}: wrote 0x{value:02X}")

    if joypad_reads:
        print("\nJoypad reads during button press:")
        for cycles, value in joypad_reads[:20]:
            print(f"    {cycles:8d}: read  0x{value:02X} (bits 0-3: {value & 0x0F:04b})")

    # Check IF register
    if_flags = cpu.memory.read_byte(0xFF0F)
    ie = cpu.memory.read_byte(0xFFFF)

    print(f"\nInterrupt state:")
    print(f"  IF: 0x{if_flags:02X} (joypad bit: {bool(if_flags & 0x10)})")
    print(f"  IE: 0x{ie:02X} (joypad enabled: {bool(ie & 0x10)})")

    # Look for the pattern of button reading
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)

    if len(joypad_writes) == 0:
        print("Game is NOT reading joypad at all!")
        print("This is very strange - maybe game is stuck in a loop?")
    else:
        # Check if game is polling
        write_values = set(value for _, value in joypad_writes)
        print(f"Game wrote these values to P1: {', '.join(f'0x{v:02X}' for v in sorted(write_values))}")

        # Check if it's selecting both button groups
        has_button_select = any(v & 0x20 == 0 for _, v in joypad_writes)
        has_dpad_select = any(v & 0x10 == 0 for _, v in joypad_writes)

        print(f"Selects buttons: {has_button_select}")
        print(f"Selects dpad: {has_dpad_select}")

        if joypad_reads:
            # See what values it read
            read_values = [value & 0x0F for _, value in joypad_reads]
            print(f"\nButton states read (bits 0-3):")
            for i, (cycles, value) in enumerate(joypad_reads[:10]):
                print(f"  Read #{i+1}: {value & 0x0F:04b} ({'pressed' if (value & 0x0F) != 0x0F else 'none'})")


if __name__ == '__main__':
    test_joypad_usage()
