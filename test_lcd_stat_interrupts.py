"""
Test LCD STAT interrupts to verify they're working correctly
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

def test_stat_interrupts():
    """Test if STAT interrupts are being generated"""
    print("="*70)
    print("LCD STAT INTERRUPT TEST")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Run until game has booted
    print("\nBooting Tetris...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    print(f"Booted to {cpu.total_cycles:,} cycles")

    # Check STAT register
    stat = cpu.memory.read_byte(0xFF41)
    lyc = cpu.memory.read_byte(0xFF45)
    ie = cpu.memory.read_byte(0xFFFF)

    print(f"\nSTAT register: 0x{stat:02X}")
    print(f"  Mode: {stat & 0x03}")
    print(f"  Coincidence flag: {bool(stat & 0x04)}")
    print(f"  HBlank interrupt enable: {bool(stat & 0x08)}")
    print(f"  VBlank interrupt enable: {bool(stat & 0x10)}")
    print(f"  OAM interrupt enable: {bool(stat & 0x20)}")
    print(f"  LYC interrupt enable: {bool(stat & 0x40)}")

    print(f"\nLYC (compare value): {lyc} (0x{lyc:02X})")
    print(f"IE register: 0x{ie:02X}")
    print(f"  LCD STAT interrupt enabled: {bool(ie & 0x02)}")

    # Monitor STAT interrupts for a few frames
    print("\nMonitoring STAT interrupts for 5 frames...")

    stat_interrupts = []
    vblank_interrupts = []

    prev_if = cpu.memory.read_byte(0xFF0F)

    for frame in range(5):
        # Run for one frame (70224 cycles)
        start_cycles = cpu.total_cycles
        frame_stat_count = 0
        frame_vblank_count = 0

        while cpu.total_cycles < start_cycles + 70224:
            cpu.step()

            # Check if STAT interrupt was triggered
            current_if = cpu.memory.read_byte(0xFF0F)

            # STAT interrupt (bit 1)
            if (current_if & 0x02) and not (prev_if & 0x02):
                frame_stat_count += 1
                ly = cpu.memory.read_byte(0xFF44)
                mode = cpu.memory.read_byte(0xFF41) & 0x03
                stat_interrupts.append((cpu.total_cycles, ly, mode))

            # VBlank interrupt (bit 0)
            if (current_if & 0x01) and not (prev_if & 0x01):
                frame_vblank_count += 1
                vblank_interrupts.append(cpu.total_cycles)

            prev_if = current_if

        print(f"  Frame {frame+1}: {frame_stat_count} STAT interrupts, {frame_vblank_count} VBlank interrupts")

    # Summary
    print(f"\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    print(f"\nTotal STAT interrupts: {len(stat_interrupts)}")
    print(f"Total VBlank interrupts: {len(vblank_interrupts)}")

    if len(stat_interrupts) > 0:
        print(f"\nFirst 10 STAT interrupts:")
        for i, (cycles, ly, mode) in enumerate(stat_interrupts[:10]):
            mode_name = ["HBlank", "VBlank", "OAM", "Transfer"][mode]
            print(f"  {i+1}. Cycle {cycles:8d}, LY={ly:3d}, Mode={mode} ({mode_name})")

    # Check LYC coincidence
    print(f"\nChecking if LYC={lyc} triggers interrupts...")

    stat_at_lyc = [s for s in stat_interrupts if s[1] == lyc]

    if stat_at_lyc:
        print(f"  Found {len(stat_at_lyc)} STAT interrupts at LY={lyc}")
        print(f"  LYC coincidence interrupt is WORKING!")
    elif lyc == 0:
        print(f"  LYC is 0 - game hasn't set it yet")
    else:
        print(f"  No STAT interrupts at LY={lyc}")
        print(f"  LYC coincidence might not be working OR interrupt not enabled")

    # Check mode interrupts
    mode_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for _, _, mode in stat_interrupts:
        mode_counts[mode] += 1

    print(f"\nSTAT interrupts by mode:")
    print(f"  Mode 0 (HBlank): {mode_counts[0]}")
    print(f"  Mode 1 (VBlank): {mode_counts[1]}")
    print(f"  Mode 2 (OAM):    {mode_counts[2]}")
    print(f"  Mode 3 (Transfer): {mode_counts[3]}")

    # Analyze if any mode is generating interrupts
    if sum(mode_counts.values()) > 0:
        print(f"\n✅ STAT interrupts ARE being generated!")

        if mode_counts[2] > 0:
            print(f"  ✅ OAM Search interrupts working ({mode_counts[2]} detected)")
        else:
            print(f"  ⚠️  No OAM Search interrupts detected")

        if mode_counts[0] > 0:
            print(f"  ✅ HBlank interrupts working ({mode_counts[0]} detected)")
        else:
            print(f"  ⚠️  No HBlank interrupts detected")

    else:
        print(f"\n❌ NO STAT interrupts detected!")
        print(f"  This could mean:")
        print(f"  - STAT interrupts not enabled in IE register")
        print(f"  - No STAT interrupt sources enabled in STAT register")
        print(f"  - Interrupt generation bug in PPU")

    # Final check: are interrupts being serviced?
    print(f"\n" + "="*70)
    print("INTERRUPT SERVICE CHECK")
    print("="*70)

    # Check if LCD STAT handler is being called
    # We can't directly monitor this, but we can check if interrupts are enabled
    ime = cpu.ime
    ie = cpu.memory.read_byte(0xFFFF)

    print(f"IME (master interrupt enable): {ime}")
    print(f"IE register: 0x{ie:02X}")

    if not ime:
        print(f"⚠️  WARNING: Master interrupts are DISABLED!")
    elif not (ie & 0x02):
        print(f"⚠️  WARNING: LCD STAT interrupt not enabled in IE!")
    else:
        print(f"✅ LCD STAT interrupt is enabled and ready")


if __name__ == '__main__':
    test_stat_interrupts()
