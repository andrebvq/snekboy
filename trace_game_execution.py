"""
Trace game execution to see what's happening
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
    """Trace what the game is doing"""
    print("="*70)
    print("TRACING GAME EXECUTION WITH BOOT ROM")
    print("="*70)

    cpu = CPU()
    cpu.memory.load_rom_file(TETRIS_ROM)
    cpu.simulate_boot()

    # Run to stable state
    print("\nRunning to 2M cycles...")
    while cpu.total_cycles < 2_000_000:
        cpu.step()

    print(f"Reached {cpu.total_cycles:,} cycles")
    print(f"Current PC: 0x{cpu.registers._pc:04X}")

    # Trace execution for a while
    print("\nTracing next 10,000 instructions...")

    pc_counts = {}
    instruction_log = []

    for i in range(10_000):
        pc = cpu.registers._pc
        pc_counts[pc] = pc_counts.get(pc, 0) + 1

        if i < 50:  # Log first 50
            opcode = cpu.memory.read_byte(pc)
            instruction_log.append((pc, opcode))

        cpu.step()

    # Show most common addresses
    print("\nMost visited addresses:")
    sorted_pcs = sorted(pc_counts.items(), key=lambda x: x[1], reverse=True)
    for pc, count in sorted_pcs[:20]:
        percent = (count * 100.0) / 10_000
        print(f"  0x{pc:04X}: {count:5d} times ({percent:5.2f}%)")

    # Show first 50 instructions
    print("\nFirst 50 instructions executed:")
    for i, (pc, opcode) in enumerate(instruction_log):
        print(f"  {i:3d}. PC=0x{pc:04X} opcode=0x{opcode:02X}")

    # Check some key memory locations
    print("\nKey memory locations:")
    print(f"  0xFF85 (VBlank flag): 0x{cpu.memory.read_byte(0xFF85):02X}")
    print(f"  0xFF00 (P1/Joypad): 0x{cpu.memory.read_byte(0xFF00):02X}")
    print(f"  0xFF40 (LCDC): 0x{cpu.memory.read_byte(0xFF40):02X}")
    print(f"  0xFF44 (LY): 0x{cpu.memory.read_byte(0xFF44):02X}")
    print(f"  0xFF41 (STAT): 0x{cpu.memory.read_byte(0xFF41):02X}")
    print(f"  0xFF0F (IF): 0x{cpu.memory.read_byte(0xFF0F):02X}")
    print(f"  0xFFFF (IE): 0x{cpu.memory.read_byte(0xFFFF):02X}")

    # Check if stuck in a loop
    if sorted_pcs[0][1] > 5000:
        print(f"\nWARNING: Spending {sorted_pcs[0][1]} cycles at 0x{sorted_pcs[0][0]:04X}")
        print("  Game might be stuck in a tight loop!")

    # Try reading some ROM around common PC
    common_pc = sorted_pcs[0][0]
    print(f"\nROM bytes around 0x{common_pc:04X}:")
    for offset in range(-5, 10):
        addr = common_pc + offset
        if 0 <= addr < 0x8000:
            byte = cpu.memory.read_byte(addr)
            marker = " <--" if offset == 0 else ""
            print(f"  0x{addr:04X}: 0x{byte:02X}{marker}")

    # Check cartridge header
    print("\nCartridge header info:")
    print(f"  Entry point: 0x{cpu.memory.read_byte(0x0100):02X}{cpu.memory.read_byte(0x0101):02X}")

    title_bytes = [cpu.memory.read_byte(0x0134 + i) for i in range(16)]
    title = ''.join(chr(b) if 32 <= b < 127 else '.' for b in title_bytes)
    print(f"  Title: {title}")

    cart_type = cpu.memory.read_byte(0x0147)
    print(f"  Cartridge type: 0x{cart_type:02X}")

    rom_size = cpu.memory.read_byte(0x0148)
    print(f"  ROM size: 0x{rom_size:02X}")

    ram_size = cpu.memory.read_byte(0x0149)
    print(f"  RAM size: 0x{ram_size:02X}")


if __name__ == '__main__':
    trace_execution()
