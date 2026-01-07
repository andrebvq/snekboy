"""
Diagnostic Tools - Debug and analyze emulator state

These tools help diagnose issues with game execution.

Usage:
  python tests/diagnostic_tools.py <tool_name> [args]

Available tools:
  tetris_state      - Show Tetris game state at 80M cycles
  trace_interrupts  - Trace IME changes and interrupt firing
  check_vblank      - Monitor VBlank interrupts
  polling_loop      - Analyze stuck polling loops
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def tool_tetris_state():
    """Comprehensive diagnostic of Tetris state"""
    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    print("Running Tetris to 80M cycles...")
    target = 80_000_000

    while cpu.total_cycles < target:
        cpu.step()

    print(f"\n{'='*70}")
    print(f"TETRIS STATE AT {cpu.total_cycles:,} CYCLES")
    print(f"{'='*70}\n")

    # CPU state
    print("CPU STATE:")
    print(f"  PC: 0x{cpu.registers._pc:04X}")
    print(f"  SP: 0x{cpu.registers._sp:04X}")
    print(f"  A: 0x{cpu.registers._a:02X}")
    print(f"  BC: 0x{cpu.registers.bc:04X}  DE: 0x{cpu.registers.de:04X}  HL: 0x{cpu.registers.hl:04X}")
    print(f"  IME: {cpu.ime}")
    print(f"  Halted: {cpu.halted}")
    print()

    # Interrupts
    ie = cpu.memory.read_byte(0xFFFF)
    if_reg = cpu.memory.read_byte(0xFF0F)
    print("INTERRUPTS:")
    print(f"  IE (0xFFFF): 0x{ie:02X}")
    print(f"  IF (0xFF0F): 0x{if_reg:02X}")
    print()

    # LCD
    lcdc = cpu.memory.read_byte(0xFF40)
    stat = cpu.memory.read_byte(0xFF41)
    ly = cpu.memory.read_byte(0xFF44)
    print("LCD/PPU:")
    print(f"  LCDC: 0x{lcdc:02X} (LCD {'ON' if lcdc & 0x80 else 'OFF'})")
    print(f"  STAT: 0x{stat:02X} (Mode {stat & 0x03})")
    print(f"  LY: {ly}")
    print()

    # Screen
    screen = cpu.ppu.get_screen_buffer()
    colors = set()
    for row in screen:
        colors.update(row)
    print(f"SCREEN: {len(colors)} colors - {sorted(colors)}")

def tool_trace_interrupts():
    """Trace interrupt enable/disable changes"""
    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    print("Tracing IME changes...")
    print()

    last_ime = cpu.ime
    changes = 0

    for i in range(500_000):
        pc_before = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc_before)

        cpu.step()

        if cpu.ime != last_ime:
            changes += 1

            instr = "DI" if opcode == 0xF3 else "EI" if opcode == 0xFB else f"[0x{opcode:02X}]"
            print(f"[{cpu.total_cycles:,}] PC=0x{pc_before:04X}: {instr:5s} - IME: {last_ime} -> {cpu.ime}")

            last_ime = cpu.ime

            if changes >= 10:
                print(f"\nStopped after {changes} changes")
                break

    print(f"\nTotal IME changes: {changes}")

def tool_check_vblank():
    """Monitor VBlank interrupt firing"""
    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Run to game loop
    print("Running to main game loop...")
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    print(f"Starting VBlank monitoring at cycle {cpu.total_cycles:,}")
    print()

    interrupt_count = 0
    max_cycles = 5_000_000
    start = cpu.total_cycles

    while cpu.total_cycles - start < max_cycles:
        pc_before = cpu.registers._pc

        cpu.step()

        pc_after = cpu.registers._pc

        # Detect interrupt (jump to 0x0040)
        if pc_after == 0x0040 and pc_before != 0x003F:
            interrupt_count += 1
            print(f"[{cpu.total_cycles:,}] VBlank interrupt #{interrupt_count}")

            if interrupt_count >= 5:
                break

    print(f"\nTotal VBlank interrupts in ~5s: {interrupt_count}")
    print(f"Expected: ~300 (59.7 Hz)")

def tool_polling_loop():
    """Analyze polling loop behavior"""
    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    print("Finding polling loop...")

    # Run until we hit common polling loop
    while cpu.registers._pc != 0x02ED:
        cpu.step()
        if cpu.total_cycles > 10_000_000:
            print("Polling loop not found")
            return

    print(f"Found polling loop at cycle {cpu.total_cycles:,}")
    print()

    # Disassemble loop
    print("Loop code:")
    pc = 0x02ED
    for i in range(5):
        opcode = cpu.memory.read_byte(pc)
        print(f"  0x{pc:04X}: 0x{opcode:02X}")
        pc += 1

    print()
    print(f"Current state:")
    print(f"  IME: {cpu.ime}")
    print(f"  IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
    print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    tool = sys.argv[1]

    tools = {
        "tetris_state": tool_tetris_state,
        "trace_interrupts": tool_trace_interrupts,
        "check_vblank": tool_check_vblank,
        "polling_loop": tool_polling_loop,
    }

    if tool not in tools:
        print(f"Unknown tool: {tool}")
        print(__doc__)
        sys.exit(1)

    tools[tool]()

if __name__ == "__main__":
    main()
