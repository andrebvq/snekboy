"""
Disassemble the main loop to see where execution goes
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cpu import CPU

TETRIS_ROM = r"C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb"

def disassemble_area():
    """Disassemble key areas"""
    print("="*70)
    print("DISASSEMBLY OF MAIN LOOP")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)

    # Boot
    while cpu.total_cycles < 1_000_000:
        cpu.step()

    # Disassemble around the wait loop
    print("\nWait loop and exit (0x02ED-0x0300):")
    for addr in range(0x02ED, 0x0300):
        byte = cpu.memory.read_byte(addr)
        print(f"  0x{addr:04X}: 0x{byte:02X}")

    # The JP instruction at 0x02F5 is 3 bytes: C3 XX XX
    jp_target_low = cpu.memory.read_byte(0x02F6)
    jp_target_high = cpu.memory.read_byte(0x02F7)
    jp_target = (jp_target_high << 8) | jp_target_low

    print(f"\nJP at 0x02F5 jumps to: 0x{jp_target:04X}")

    # Disassemble target
    print(f"\nCode at jump target (0x{jp_target:04X}):")
    for addr in range(jp_target, jp_target + 32):
        byte = cpu.memory.read_byte(addr)
        print(f"  0x{addr:04X}: 0x{byte:02X}")

    # Now trace actual execution
    print(f"\n" + "="*70)
    print("EXECUTION TRACE")
    print("="*70)

    # Reset and trace through one loop iteration
    cpu2 = CPU()
    cpu2.memory.load_rom_file(TETRIS_ROM)

    while cpu2.total_cycles < 1_000_000:
        cpu2.step()

    # Now we're in the wait loop. Trace next 200 instructions
    print(f"\nTracing next 200 instructions from wait loop:")

    trace = []
    for i in range(200):
        pc = cpu2.registers._pc
        opcode = cpu2.memory.read_byte(pc)
        trace.append((pc, opcode))
        cpu2.step()

    # Show unique PCs in order
    seen = set()
    unique_trace = []
    for pc, opcode in trace:
        if pc not in seen:
            seen.add(pc)
            unique_trace.append((pc, opcode))

    print(f"\nUnique PCs visited (in order):")
    for i, (pc, opcode) in enumerate(unique_trace[:30]):
        print(f"  {i+1:3d}. 0x{pc:04X}: 0x{opcode:02X}")

    # Check if it ever leaves the loop area
    max_pc = max(pc for pc, _ in trace)
    min_pc = min(pc for pc, _ in trace)

    print(f"\nPC range: 0x{min_pc:04X} - 0x{max_pc:04X}")

    if max_pc < 0x0300:
        print(f"⚠️  CPU never leaves the 0x02XX range!")
        print(f"   Stuck in main loop area")
    else:
        print(f"✅ CPU executes beyond main loop")


if __name__ == '__main__':
    disassemble_area()
