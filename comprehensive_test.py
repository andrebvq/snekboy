"""
Comprehensive test of all emulator features with Tetris
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

def comprehensive_test():
    """Run comprehensive test"""
    print("="*70)
    print("COMPREHENSIVE EMULATOR TEST WITH TETRIS")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Verify boot state
    print("\n1. BOOT STATE VERIFICATION")
    print(f"  CPU Registers:")
    print(f"    A: 0x{cpu.registers._a:02X} (expected 0x01)")
    print(f"    F: 0x{cpu.registers.flags.to_byte():02X} (expected 0xB0)")
    print(f"    BC: 0x{cpu.registers._b:02X}{cpu.registers._c:02X} (expected 0x0013)")
    print(f"    PC: 0x{cpu.registers._pc:04X} (expected 0x0100)")
    print(f"    SP: 0x{cpu.registers._sp:04X} (expected 0xFFFE)")

    print(f"\n  Hardware Registers:")
    print(f"    LCDC: 0x{cpu.memory.read_byte(0xFF40):02X} (expected 0x91)")
    print(f"    IF: 0x{cpu.memory.read_byte(0xFF0F):02X} (expected 0xE1)")
    print(f"    IE: 0x{cpu.memory.read_byte(0xFFFF):02X} (expected 0x00)")
    print(f"    NR52: 0x{cpu.memory.read_byte(0xFF26):02X} (expected 0xF1)")

    # Run and track features
    vram_writes = []
    vblank_count = 0
    joypad_reads = 0

    original_write = cpu.memory.write_byte
    original_read = cpu.memory.read_byte

    def traced_write(address, value):
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            vram_writes.append(cpu.total_cycles)
        return original_write(address, value)

    def traced_read(address):
        nonlocal joypad_reads, vblank_count
        if address == 0xFF00:
            joypad_reads += 1
        return original_read(address)

    traced_read.cpu = cpu

    cpu.memory.write_byte = traced_write
    cpu.memory.read_byte = traced_read

    # Track VBlank interrupts
    last_if = cpu.memory._data[0xFF0F]

    # Run to 3M cycles
    print("\n2. RUNNING TO 3M CYCLES")
    while cpu.total_cycles < 3_000_000:
        cpu.step()

        # Count VBlanks by watching IF register
        current_if = cpu.memory._data[0xFF0F]
        if (current_if & 0x01) and not (last_if & 0x01):
            vblank_count += 1
        last_if = current_if

    print(f"  Total cycles: {cpu.total_cycles:,}")
    print(f"  VBlank interrupts: {vblank_count}")
    print(f"  VRAM writes (non-zero): {len(vram_writes)}")
    print(f"  Joypad reads: {joypad_reads}")

    # Check screen
    screen = cpu.ppu.get_screen_buffer()
    pixels = sum(1 for row in screen for pixel in row if pixel != 0)
    print(f"  Screen pixels: {pixels:,}")

    # Check execution
    print("\n3. EXECUTION CHECK")
    pc_trace = []
    for _ in range(100):
        pc_trace.append(cpu.registers._pc)
        cpu.step()

    unique_pcs = len(set(pc_trace))
    print(f"  Unique PCs in 100 steps: {unique_pcs}")
    most_common = max(set(pc_trace), key=pc_trace.count)
    count = pc_trace.count(most_common)
    print(f"  Most common PC: 0x{most_common:04X} ({count}/100)")

    # Press START and check response
    print("\n4. INPUT TEST")
    cpu.memory.joypad.press_button('start')

    vram_before = len(vram_writes)
    for _ in range(100_000):
        cpu.step()

    cpu.memory.joypad.release_button('start')

    vram_after = len(vram_writes)
    vram_during_input = vram_after - vram_before

    print(f"  VRAM writes during START press: {vram_during_input}")

    screen2 = cpu.ppu.get_screen_buffer()
    pixels2 = sum(1 for row in screen2 for pixel in row if pixel != 0)

    if pixels2 != pixels:
        print(f"  Screen changed: {pixels} -> {pixels2}")
    else:
        print(f"  Screen unchanged: {pixels}")

    # Final verdict
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)

    all_good = True

    if vblank_count > 30:
        print(f"  VBlank interrupts: WORKING ({vblank_count} interrupts)")
    else:
        print(f"  VBlank interrupts: FAILED ({vblank_count} interrupts)")
        all_good = False

    if len(vram_writes) > 1000:
        print(f"  VRAM writes: WORKING ({len(vram_writes)} writes)")
    else:
        print(f"  VRAM writes: FAILED ({len(vram_writes)} writes)")
        all_good = False

    if joypad_reads > 100:
        print(f"  Joypad polling: WORKING ({joypad_reads} reads)")
    else:
        print(f"  Joypad polling: FAILED ({joypad_reads} reads)")
        all_good = False

    if pixels > 1000:
        print(f"  Screen rendering: WORKING ({pixels} pixels)")
    else:
        print(f"  Screen rendering: FAILED ({pixels} pixels)")
        all_good = False

    if vram_during_input > 0 or pixels2 != pixels:
        print(f"  Input response: WORKING (game responds to buttons)")
    else:
        print(f"  Input response: NOT WORKING (game ignores buttons)")
        all_good = False

    if all_good:
        print(f"\n  ALL SYSTEMS OPERATIONAL!")
    else:
        print(f"\n  SOME SYSTEMS NOT WORKING")


if __name__ == '__main__':
    comprehensive_test()
