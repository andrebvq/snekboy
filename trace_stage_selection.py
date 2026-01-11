"""
Trace stage selection to gameplay transition
Logs everything to tracing.txt
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
from src.tracer import Tracer

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def trace_stage_selection():
    """Trace the stage selection issue"""
    print("="*70)
    print("TRACING STAGE SELECTION TRANSITION")
    print("="*70)
    print("\nLogs will be written to tracing.txt")
    print("This may take a while as game runs slow...")

    # Create tracer
    tracer = Tracer("tracing.txt", enabled=True)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    tracer.log_section("BOOT COMPLETE")
    tracer.log_state(cpu.total_cycles, cpu.memory.read_byte(0xFF44),
                     cpu.memory.read_byte(0xFF40), cpu.registers._pc)

    # Instrument memory reads/writes
    original_read = cpu.memory.read_byte
    original_write = cpu.memory.write_byte

    vram_write_count = 0
    ly_read_count = 0
    last_lcdc = cpu.memory.read_byte(0xFF40)

    def traced_read(address):
        nonlocal ly_read_count
        result = original_read(address)

        # Log LY reads (but not every one, would be too many)
        if address == 0xFF44 and ly_read_count % 1000 == 0:
            tracer.log_ly_read(cpu.total_cycles, cpu.registers._pc, result)
            ly_read_count += 1

        return result

    def traced_write(address, value):
        nonlocal vram_write_count, last_lcdc

        # Log LCDC writes
        if address == 0xFF40:
            if value != last_lcdc:
                tracer.log_lcdc_write(cpu.total_cycles, cpu.registers._pc, value)
                last_lcdc = value

        # Log VRAM writes (non-zero only)
        if 0x8000 <= address <= 0x9FFF and value != 0x00:
            # Don't log every single one, just periodically
            if vram_write_count < 100 or vram_write_count % 100 == 0:
                tracer.log_vram_write(cpu.total_cycles, cpu.registers._pc, address, value)
            vram_write_count += 1

        # Log DMA
        if address == 0xFF46:
            tracer.log_dma_trigger(cpu.total_cycles, cpu.registers._pc, value)

        return original_write(address, value)

    cpu.memory.read_byte = traced_read
    cpu.memory.write_byte = traced_write

    # Track VBlank
    last_if = cpu.memory._data[0xFF0F]
    vblank_count = 0

    # Run to copyright screen (let it take its time)
    print("\n1. Running to copyright screen (may take 30+ seconds)...")
    tracer.log_section("PHASE 1: BOOT TO COPYRIGHT SCREEN")

    start_time = time.time()
    last_update = start_time

    while cpu.total_cycles < 25_000_000:  # ~25 seconds at 60 FPS
        cpu.step()

        # Track VBlanks
        current_if = cpu.memory._data[0xFF0F]
        if (current_if & 0x01) and not (last_if & 0x01):
            vblank_count += 1
            if vblank_count % 60 == 0:  # Every ~1 second
                tracer.log_vblank(cpu.total_cycles)
        last_if = current_if

        # Progress update every 5 seconds
        now = time.time()
        if now - last_update >= 5.0:
            elapsed = now - start_time
            ly = cpu.memory.read_byte(0xFF44)
            lcdc = cpu.memory.read_byte(0xFF40)
            print(f"   {elapsed:.0f}s elapsed - Cycle {cpu.total_cycles:,} - LY={ly} LCDC=0x{lcdc:02X}")
            tracer.log_state(cpu.total_cycles, ly, lcdc, cpu.registers._pc)
            last_update = now

    print(f"   Reached {cpu.total_cycles:,} cycles in {time.time() - start_time:.0f}s")
    print(f"   VBlanks: {vblank_count}")
    print(f"   VRAM writes: {vram_write_count}")

    # Now simulate START button press on stage select
    tracer.log_section("PHASE 2: PRESSING START ON STAGE SELECT")
    print("\n2. Pressing START to start game...")

    cpu.memory.joypad.press_button('start')
    tracer.log(f"[{cpu.total_cycles:10d}] *** START BUTTON PRESSED ***")

    # Hold START and run
    start_time = time.time()
    last_update = start_time
    target = cpu.total_cycles + 30_000_000  # Another ~30 seconds

    while cpu.total_cycles < target:
        cpu.step()

        # Track VBlanks
        current_if = cpu.memory._data[0xFF0F]
        if (current_if & 0x01) and not (last_if & 0x01):
            vblank_count += 1
        last_if = current_if

        # Progress update
        now = time.time()
        if now - last_update >= 5.0:
            elapsed = now - start_time
            ly = cpu.memory.read_byte(0xFF44)
            lcdc = cpu.memory.read_byte(0xFF40)
            print(f"   {elapsed:.0f}s elapsed - Cycle {cpu.total_cycles:,} - LY={ly} LCDC=0x{lcdc:02X}")
            tracer.log_state(cpu.total_cycles, ly, lcdc, cpu.registers._pc)
            last_update = now

    cpu.memory.joypad.release_button('start')
    tracer.log(f"[{cpu.total_cycles:10d}] *** START BUTTON RELEASED ***")

    print(f"   Reached {cpu.total_cycles:,} cycles in {time.time() - start_time:.0f}s")

    # Final state
    tracer.log_section("FINAL STATE")
    ly = cpu.memory.read_byte(0xFF44)
    lcdc = cpu.memory.read_byte(0xFF40)
    tracer.log_state(cpu.total_cycles, ly, lcdc, cpu.registers._pc)

    print(f"\nFinal state:")
    print(f"   Total VBlanks: {vblank_count}")
    print(f"   Total VRAM writes: {vram_write_count}")
    print(f"   LY: {ly}")
    print(f"   LCDC: 0x{lcdc:02X} ({'ON' if lcdc & 0x80 else 'OFF'})")
    print(f"   PC: 0x{cpu.registers._pc:04X}")

    tracer.close()
    print("\nTrace complete! Check tracing.txt for details.")


if __name__ == '__main__':
    trace_stage_selection()
