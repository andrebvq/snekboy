"""
Trace execution flow to see what code Tetris is running
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

def trace_execution():
    """Trace what code is executing"""
    print("="*70)
    print("EXECUTION FLOW TRACE")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    print("\nBooting to 1M cycles...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    # Track PC values
    print("\nTracking PC for 100k cycles...")

    pc_hist = {}
    pc_sequence = []

    start_cycles = cpu.total_cycles

    while cpu.total_cycles < start_cycles + 100_000:
        pc = cpu.registers._pc

        if pc not in pc_hist:
            pc_hist[pc] = 0
        pc_hist[pc] += 1

        # Record sequence (sample every 100 instructions)
        if len(pc_sequence) < 1000 and len(pc_sequence) % 10 == 0:
            pc_sequence.append(pc)

        cpu.step()

    # Analyze
    print(f"\nAnalysis of 100k cycles:")
    print(f"  Unique PC values: {len(pc_hist)}")

    # Top 20 most frequent PCs
    top_pcs = sorted(pc_hist.items(), key=lambda x: x[1], reverse=True)[:20]

    print(f"\nTop 20 most executed addresses:")
    for i, (pc, count) in enumerate(top_pcs):
        pct = count * 100 / 100_000
        print(f"  {i+1:2d}. 0x{pc:04X}: {count:6d} times ({pct:5.1f}%)")

    # Check if stuck in a tight loop
    if top_pcs[0][1] > 50_000:
        print(f"\n⚠️  CPU is spending {top_pcs[0][1]*100/100_000:.1f}% at 0x{top_pcs[0][0]:04X}")
        print(f"     Likely a very tight loop!")

    # Show PC sequence pattern
    print(f"\nPC sequence (every 10th instruction):")
    for i in range(0, min(50, len(pc_sequence)), 5):
        pcs = " ".join(f"0x{pc:04X}" for pc in pc_sequence[i:i+5])
        print(f"  {i:3d}: {pcs}")

    # Disassemble top address
    print(f"\nDisassembly at most frequent address (0x{top_pcs[0][0]:04X}):")
    addr = top_pcs[0][0]
    for i in range(10):
        byte = cpu.memory.read_byte(addr + i)
        print(f"  0x{addr+i:04X}: 0x{byte:02X}")

    # Check if code is updating VRAM
    print(f"\nChecking VRAM writes...")

    # Track writes to VRAM
    vram_writes = []

    original_write = cpu.memory.write_byte

    def track_vram(address, value):
        if 0x8000 <= address <= 0x9FFF:
            vram_writes.append((cpu.total_cycles, address, value))
        return original_write(address, value)

    cpu.memory.write_byte = track_vram

    # Run for another 100k cycles
    start_cycles = cpu.total_cycles
    while cpu.total_cycles < start_cycles + 100_000:
        cpu.step()

    print(f"  VRAM writes in 100k cycles: {len(vram_writes)}")

    if vram_writes:
        print(f"\n  First 20 VRAM writes:")
        for i, (cycles, addr, value) in enumerate(vram_writes[:20]):
            print(f"    {i+1}. Cycle {cycles:8d}: [0x{addr:04X}] = 0x{value:02X}")
    else:
        print(f"\n  ❌ NO VRAM writes detected!")
        print(f"     Game is not updating graphics!")

    # Check if screen buffer ever changes
    print(f"\nChecking if screen buffer changes...")

    screen1 = [row[:] for row in cpu.ppu.get_screen_buffer()]

    for _ in range(100_000):
        cpu.step()

    screen2 = cpu.ppu.get_screen_buffer()

    changes = sum(1 for y in range(144) for x in range(160)
                  if screen1[y][x] != screen2[y][x])

    print(f"  Pixels changed: {changes}/23,040")

    if changes == 0:
        print(f"  ❌ Screen buffer NEVER changes!")
    else:
        print(f"  ✅ Screen buffer is updating ({changes*100/23040:.1f}%)")


if __name__ == '__main__':
    trace_execution()
