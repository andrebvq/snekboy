"""
Test if VRAM writes are working correctly
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

def test_vram_write_access():
    """Test VRAM write access during different PPU modes"""
    print("=" * 70)
    print("VRAM WRITE ACCESS TEST")
    print("=" * 70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    print("\nBooting Tetris...")
    while cpu.total_cycles < 100_000:
        cpu.step()

    print(f"Booted at {cpu.total_cycles:,} cycles")

    # Try writing to VRAM in different modes
    print("\nTesting VRAM writes in different PPU modes...")

    test_patterns = []

    for i in range(1000):  # Monitor for a bit
        ppu_mode = cpu.ppu.current_mode
        ly = cpu.memory.read_byte(0xFF44)

        # Try writing to VRAM
        test_addr = 0x8000 + (i % 256)
        test_value = (i + 123) & 0xFF

        # Write directly (bypassing restrictions to see if it works)
        cpu.memory._data[test_addr] = test_value

        # Read back
        read_value = cpu.memory._data[test_addr]

        if read_value == test_value:
            result = "OK"
        else:
            result = f"FAIL (wrote {test_value:02X}, got {read_value:02X})"

        test_patterns.append((ppu_mode, ly, result))

        # Step a bit
        for _ in range(10):
            cpu.step()

    # Analyze results
    mode_results = {0: [], 1: [], 2: [], 3: []}
    for mode, ly, result in test_patterns:
        mode_results[mode].append(result == "OK")

    print("\nResults by PPU mode:")
    mode_names = {0: "HBlank", 1: "VBlank", 2: "OAM Search", 3: "Pixel Transfer"}
    for mode in range(4):
        if mode_results[mode]:
            success = sum(mode_results[mode])
            total = len(mode_results[mode])
            print(f"  Mode {mode} ({mode_names[mode]}): {success}/{total} writes successful")

    # Now check if game can write to VRAM
    print("\n" + "=" * 70)
    print("MONITORING GAME VRAM WRITES")
    print("=" * 70)

    cpu2 = CPU()
    cpu2.memory.load_rom_file(TETRIS_ROM)

    print("\nMonitoring VRAM changes during boot...")

    # Take snapshot of VRAM before
    vram_before = []
    for addr in range(0x8000, 0x9800):
        vram_before.append(cpu2.memory._data[addr])

    # Run for a bit
    for _ in range(500_000):
        cpu2.step()

    # Take snapshot after
    vram_after = []
    for addr in range(0x8000, 0x9800):
        vram_after.append(cpu2.memory._data[addr])

    # Count changes
    changes = 0
    for i in range(len(vram_before)):
        if vram_before[i] != vram_after[i]:
            changes += 1

    print(f"\nVRAM bytes changed: {changes}/6144")

    if changes > 0:
        print("✅ Game IS writing to VRAM")
        # Show some examples
        print("\nFirst 10 changed addresses:")
        count = 0
        for i in range(len(vram_before)):
            if vram_before[i] != vram_after[i] and count < 10:
                addr = 0x8000 + i
                print(f"  0x{addr:04X}: 0x{vram_before[i]:02X} -> 0x{vram_after[i]:02X}")
                count += 1
    else:
        print("❌ Game is NOT writing to VRAM (or writes are blocked)")

        # Check PPU mode distribution
        print("\nChecking PPU mode distribution during execution...")
        cpu3 = CPU()
        cpu3.memory.load_rom_file(TETRIS_ROM)

        mode_counts = {0: 0, 1: 0, 2: 0, 3: 0}

        for _ in range(10_000):
            mode = cpu3.ppu.current_mode
            mode_counts[mode] += 1
            cpu3.step()

        total = sum(mode_counts.values())
        print("\nPPU mode distribution:")
        for mode in range(4):
            pct = mode_counts[mode] * 100 / total
            print(f"  Mode {mode} ({mode_names[mode]}): {mode_counts[mode]:5d} steps ({pct:5.1f}%)")

        # If Mode 3 is too high, VRAM writes are always blocked
        if mode_counts[3] * 100 / total > 50:
            print("\n⚠️  WARNING: Mode 3 (Pixel Transfer) is > 50% of time")
            print("   VRAM writes are being blocked too much!")


if __name__ == '__main__':
    test_vram_write_access()
