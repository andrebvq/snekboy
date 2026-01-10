"""Debug script to run Super Mario Land and log execution before crash"""

import sys
sys.path.insert(0, 'C:\\Users\\andre\\OneDrive\\Desktop\\projects\\snekboy')

from src.cpu import CPU
import time

rom_path = r"C:\Users\andre\OneDrive\Desktop\gb\Super Mario Land (World)\Super Mario Land (World).gb"

print(f"Loading ROM: {rom_path}")
cpu = CPU()
cpu.memory.load_rom_file(rom_path)
print("ROM loaded")

# Run for a bit, logging the last N instructions
log_size = 500  # Increased to capture more history
instruction_log = []

try:
    cycles_run = 0
    max_cycles = 10_000_000  # Run for 10M cycles

    print("Starting execution...")
    last_print = 0

    while cycles_run < max_cycles:
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)

        # Log this instruction
        instruction_log.append((pc, opcode))
        if len(instruction_log) > log_size:
            instruction_log.pop(0)

        # Print progress every 100k cycles
        if cycles_run - last_print >= 100_000:
            print(f"  Cycles: {cycles_run:,} | PC: 0x{pc:04X}")
            last_print = cycles_run

        # Execute
        cycles = cpu.step()
        cycles_run += cycles

    print(f"\nCompleted {cycles_run:,} cycles without crashing")

except Exception as e:
    print(f"\n!!! CRASH at cycle {cycles_run} !!!")
    print(f"Error: {e}\n")

    # Find the first jump into RAM
    first_ram_idx = None
    for i, (pc, opcode) in enumerate(instruction_log):
        if 0xC000 <= pc <= 0xDFFF:
            first_ram_idx = i
            break

    if first_ram_idx is not None and first_ram_idx > 0:
        print(f"First jump into RAM detected at instruction #{first_ram_idx}")
        print(f"Instructions around the jump into RAM:")
        start = max(0, first_ram_idx - 10)
        for i in range(start, min(len(instruction_log), first_ram_idx + 5)):
            pc, opcode = instruction_log[i]
            marker = " <-- FIRST RAM INSTRUCTION" if i == first_ram_idx else ""
            loc = "RAM" if 0xC000 <= pc <= 0xDFFF else "ROM"
            print(f"  [{loc}] PC=0x{pc:04X}: opcode=0x{opcode:02X}{marker}")

    print(f"\nLast 20 instructions before crash:")
    for i in range(max(0, len(instruction_log) - 20), len(instruction_log)):
        pc, opcode = instruction_log[i]
        marker = " <-- CRASH HERE" if i == len(instruction_log) - 1 else ""
        loc = "RAM" if 0xC000 <= pc <= 0xDFFF else "ROM"
        print(f"  [{loc}] PC=0x{pc:04X}: opcode=0x{opcode:02X}{marker}")

    print(f"\nCPU state at crash:")
    print(f"  PC: 0x{cpu.registers._pc:04X}")
    print(f"  SP: 0x{cpu.registers._sp:04X}")
    print(f"  A: 0x{cpu.registers._a:02X}")
    print(f"  F: Z={cpu.registers.flags.zero} N={cpu.registers.flags.subtract} H={cpu.registers.flags.half_carry} C={cpu.registers.flags.carry}")

    # Check what's in RAM around the crash address
    crash_pc = cpu.registers._pc - 1
    if 0xC000 <= crash_pc <= 0xDFFF:
        print(f"\nRAM contents around crash PC (0x{crash_pc:04X}):")
        start = max(0xC000, crash_pc - 10)
        end = min(0xDFFF, crash_pc + 10)
        for addr in range(start, end + 1):
            byte = cpu.memory.read_byte(addr)
            marker = " <--" if addr == crash_pc else ""
            print(f"  0x{addr:04X}: 0x{byte:02X}{marker}")
