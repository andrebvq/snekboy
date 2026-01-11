"""
Monitor when Tetris enables STAT interrupts
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

# Track STAT writes
stat_writes = []
ie_writes = []

original_write = None

def traced_write(address, value):
    if address == 0xFF41:  # STAT
        stat_writes.append((traced_write.cpu.total_cycles, value))
    elif address == 0xFFFF:  # IE
        ie_writes.append((traced_write.cpu.total_cycles, value))
    return original_write(address, value)


def monitor_stat_enabling():
    """Monitor when game enables STAT interrupts"""
    print("="*70)
    print("MONITORING STAT INTERRUPT ENABLING")
    print("="*70)

    cpu = CPU()

    # Patch writes
    global original_write
    original_write = cpu.memory.write_byte
    traced_write.cpu = cpu
    cpu.memory.write_byte = traced_write

    cpu.memory.load_rom_file(TETRIS_ROM)

    print("\nRunning for 5M cycles...")

    while cpu.total_cycles < 5_000_000:
        cpu.step()

    print(f"Completed {cpu.total_cycles:,} cycles")

    # Analyze STAT writes
    print(f"\n" + "="*70)
    print("STAT REGISTER WRITES")
    print("="*70)

    print(f"\nTotal STAT writes: {len(stat_writes)}")

    if stat_writes:
        print(f"\nFirst 20 STAT writes:")
        for i, (cycles, value) in enumerate(stat_writes[:20]):
            print(f"  {i+1:3d}. Cycle {cycles:8d}: 0x{value:02X} (mode int: H={bool(value&0x08)} V={bool(value&0x10)} O={bool(value&0x20)} L={bool(value&0x40)})")

        # Check for specific patterns
        stat_with_interrupts = [v for c, v in stat_writes if (v & 0x78) != 0]

        if stat_with_interrupts:
            print(f"\nFound {len(stat_with_interrupts)} STAT writes with interrupts enabled!")
            print(f"  Values: {set(f'0x{v:02X}' for v in stat_with_interrupts)}")
        else:
            print(f"\n⚠️  No STAT writes enabled any interrupt sources")

    # Analyze IE writes
    print(f"\n" + "="*70)
    print("IE REGISTER WRITES")
    print("="*70)

    print(f"\nTotal IE writes: {len(ie_writes)}")

    if ie_writes:
        print(f"\nAll IE writes:")
        for i, (cycles, value) in enumerate(ie_writes):
            stat_enabled = bool(value & 0x02)
            print(f"  {i+1:3d}. Cycle {cycles:8d}: 0x{value:02X} (STAT int: {'✓' if stat_enabled else 'X'})")

        # Check if STAT ever gets enabled
        ie_with_stat = [v for c, v in ie_writes if v & 0x02]

        if ie_with_stat:
            print(f"\n✅ STAT interrupt WAS enabled in IE!")
            first_enable = next((c, v) for c, v in ie_writes if v & 0x02)
            print(f"  First enabled at cycle {first_enable[0]:,} with value 0x{first_enable[1]:02X}")
        else:
            print(f"\n❌ STAT interrupt NEVER enabled in IE")

    # Check current state
    print(f"\n" + "="*70)
    print("CURRENT STATE")
    print("="*70)

    stat = cpu.memory.read_byte(0xFF41)
    ie = cpu.memory.read_byte(0xFFFF)
    lyc = cpu.memory.read_byte(0xFF45)

    print(f"\nSTAT: 0x{stat:02X}")
    print(f"  HBlank int: {bool(stat & 0x08)}")
    print(f"  VBlank int: {bool(stat & 0x10)}")
    print(f"  OAM int: {bool(stat & 0x20)}")
    print(f"  LYC int: {bool(stat & 0x40)}")

    print(f"\nIE: 0x{ie:02X}")
    print(f"  STAT enabled: {bool(ie & 0x02)}")

    print(f"\nLYC: {lyc} (0x{lyc:02X})")

    # Conclusion
    print(f"\n" + "="*70)
    print("CONCLUSION")
    print("="*70)

    if (ie & 0x02) and (stat & 0x78):
        print(f"\n✅ STAT interrupts ARE enabled!")
        print(f"   IE has STAT enabled: {bool(ie & 0x02)}")
        print(f"   STAT has sources enabled: 0x{stat & 0x78:02X}")
    elif ie & 0x02:
        print(f"\n⚠️  STAT interrupt enabled in IE but no sources in STAT")
    elif stat & 0x78:
        print(f"\n⚠️  STAT sources enabled but not in IE")
    else:
        print(f"\n❌ STAT interrupts NOT enabled")
        print(f"   Tetris might not use STAT interrupts at this stage")


if __name__ == '__main__':
    monitor_stat_enabling()
