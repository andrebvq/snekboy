"""
Trace exactly what happens in one frame between flag set and clear
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

def trace_frame():
    """Trace one complete frame"""
    print("="*70)
    print("TRACING ONE FRAME OF EXECUTION")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 1.5M cycles...")
    while cpu.total_cycles < 1_500_000:
        cpu.step()

    # Wait until we're AT the flag check instruction
    print("\nWaiting to reach VBlank wait loop (PC=0x02ED)...")
    while cpu.registers._pc != 0x02ED:
        cpu.step()

    print(f"At VBlank wait loop at cycle {cpu.total_cycles:,}")
    print(f"Flag value: 0x{cpu.memory.read_byte(0xFF85):02X}")

    # Now wait for flag to be SET
    print("\nWaiting for flag to be set to 0x01...")
    start_cycle = cpu.total_cycles
    while cpu.memory.read_byte(0xFF85) == 0x00:
        cpu.step()

    print(f"Flag set at cycle {cpu.total_cycles:,} (waited {cpu.total_cycles - start_cycle} cycles)")

    # Now trace until flag is cleared
    print("\nTracing execution until flag cleared...")

    trace_log = []
    in_trace = True
    max_instructions = 500

    for i in range(max_instructions):
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        # Decode key instructions
        if opcode == 0xCD:  # CALL nn
            low = cpu.memory.read_byte(pc + 1)
            high = cpu.memory.read_byte(pc + 2)
            target = (high << 8) | low
            trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: CALL 0x{target:04X}")
        elif opcode == 0xC3:  # JP nn
            low = cpu.memory.read_byte(pc + 1)
            high = cpu.memory.read_byte(pc + 2)
            target = (high << 8) | low
            trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: JP 0x{target:04X}")
        elif opcode == 0xC9:  # RET
            trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: RET")
        elif opcode == 0xAF:  # XOR A
            if pc == 0x02F2:  # This is the XOR A before clearing flag
                trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: XOR A (about to clear flag)")
        elif opcode == 0xE0:  # LDH (n), A
            addr = 0xFF00 | cpu.memory.read_byte(pc + 1)
            if addr == 0xFF85:
                a_value = cpu.registers._a
                trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: LDH (0xFF85), A (A=0x{a_value:02X}) - CLEARING FLAG")
        elif pc in [0x02ED, 0x02EF, 0x02F0]:
            # VBlank wait loop instructions
            if opcode == 0xF0:  # LDH A, (n)
                trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: LDH A, (0xFF85)")
            elif opcode == 0xA7:  # AND A
                trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: AND A")
            elif opcode == 0x28:  # JR Z, n
                trace_log.append(f"  {i:3d}. PC=0x{pc:04X}: JR Z, (back to wait)")

        cpu.step()

        # Check if flag was cleared
        flag_value = cpu.memory.read_byte(0xFF85)
        if flag_value == 0x00 and i > 10:  # Give it a few instructions
            trace_log.append(f"\n  Flag cleared at instruction {i}")
            break

    # Print trace
    print(f"\nFull execution trace ({len(trace_log)} instructions):")
    for line in trace_log:
        print(line)

    # Check current state
    print(f"\nFinal state:")
    print(f"  PC: 0x{cpu.registers._pc:04X}")
    print(f"  Flag (0xFF85): 0x{cpu.memory.read_byte(0xFF85):02X}")


if __name__ == '__main__':
    trace_frame()
