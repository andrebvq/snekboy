"""
Generate a trace with the fixed memory.py to see if DMA from 0x2F00 still occurs
"""

from src.emulator import Emulator

# Create emulator with tracing
emu = Emulator(trace_file="tracing/fixed_trace.txt")

print("Running Tetris with tracing until 25M cycles...")

target = 25_000_000
while emu.cpu.total_cycles < target:
    emu.step()
    if emu.cpu.total_cycles % 1_000_000 == 0:
        print(f"  {emu.cpu.total_cycles // 1_000_000}M cycles")

print(f"Done! Generated trace at tracing/fixed_trace.txt")
print(f"Final PC: 0x{emu.cpu.registers._pc:04X}")
print(f"Final LCDC: 0x{emu.cpu.memory._data[0xFF40]:02X}")
