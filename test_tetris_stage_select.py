"""
Test Tetris stage selection to see if fixes resolve the issue
"""

from src.cpu import CPU
import sys

# Create CPU
cpu = CPU()

# Load Tetris ROM
rom_path = r'C:\Users\andre\OneDrive\Desktop\gb\Tetris (World) (Rev 1)\Tetris (World) (Rev 1).gb'
cpu.memory.load_rom_file(rom_path)
cpu.simulate_boot()

print("Running Tetris until cycle 25M (past the problematic stage selection)...")
print("Looking for issues around cycle 24.5M where DMA from 0x2F00 occurs...")

target_cycles = 25_000_000
last_print = 0

try:
    while cpu.total_cycles < target_cycles:
        cpu.step()

        # Print progress every 1M cycles
        if cpu.total_cycles - last_print >= 1_000_000:
            print(f"  Cycles: {cpu.total_cycles // 1_000_000}M, PC: 0x{cpu.registers._pc:04X}")
            last_print = cpu.total_cycles

        # Check for infinite loop (PC stuck at same address)
        if cpu.total_cycles > 24_500_000 and cpu.total_cycles < 25_000_000:
            # In the problematic region
            if hasattr(cpu, '_last_pc') and cpu._last_pc == cpu.registers._pc:
                cpu._stuck_count = getattr(cpu, '_stuck_count', 0) + 1
                if cpu._stuck_count > 1000:
                    print(f"\n[ERROR] CPU appears stuck in loop at PC=0x{cpu.registers._pc:04X}")
                    print(f"  Cycles: {cpu.total_cycles}")
                    print(f"  Registers: A={cpu.registers.a:02X} BC={cpu.registers.get_bc():04X} DE={cpu.registers.get_de():04X} HL={cpu.registers.get_hl():04X}")
                    sys.exit(1)
            else:
                cpu._stuck_count = 0
            cpu._last_pc = cpu.registers._pc

    print(f"\nSuccess! Reached {cpu.total_cycles} cycles without crashing")
    print(f"Final PC: 0x{cpu.registers._pc:04X}")
    print(f"Final LCDC: 0x{cpu.memory._data[0xFF40]:02X}")

except KeyboardInterrupt:
    print(f"\nInterrupted at cycle {cpu.total_cycles}")
except Exception as e:
    print(f"\nError at cycle {cpu.total_cycles}: {e}")
    import traceback
    traceback.print_exc()
