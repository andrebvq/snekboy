"""
Debug the CALL instruction at 0xC24C that jumps to suspicious address 0xC35C
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def debug_call():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running until PC=0xC24C...")

    target_pc = 0xC24C
    found = False

    while cpu.total_cycles < 30_000_000 and not found:
        if cpu.registers._pc == target_pc:
            found = True
            print(f"\n{'='*80}")
            print(f"Reached PC=0x{target_pc:04X} at cycle {cpu.total_cycles:,}")
            print(f"{'='*80}")
            print(f"Registers: A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
            print(f"Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
            print()

            # Read the CALL instruction
            opcode = cpu.memory.read_byte(target_pc)
            low_byte = cpu.memory.read_byte(target_pc + 1)
            high_byte = cpu.memory.read_byte(target_pc + 2)
            call_target = low_byte | (high_byte << 8)

            print(f"Instruction at 0x{target_pc:04X}:")
            print(f"  Opcode: 0x{opcode:02X} (CALL nn)")
            print(f"  Low byte: 0x{low_byte:02X}")
            print(f"  High byte: 0x{high_byte:02X}")
            print(f"  Call target: 0x{call_target:04X}")
            print()

            # Show memory at the call target
            print(f"Memory at call target 0x{call_target:04X}:")
            for offset in range(16):
                addr = call_target + offset
                value = cpu.memory.read_byte(addr)
                marker = " <-- ENTRY" if offset == 0 else ""
                print(f"  0x{addr:04X}: 0x{value:02X}{marker}")
            print()

            # Check if this looks like valid code
            entry_byte = cpu.memory.read_byte(call_target)
            if entry_byte == 0xC9:
                print("*** WARNING: Call target starts with RET (0xC9) - This is suspicious! ***")
                print("*** This will immediately return without doing anything ***")
            elif entry_byte == 0x00:
                print("*** WARNING: Call target starts with NOP (0x00) - Might be uninitialized! ***")

            # Also show memory around 0xC24C
            print(f"\nMemory around 0x{target_pc:04X}:")
            for addr in range(target_pc - 8, target_pc + 16):
                value = cpu.memory.read_byte(addr)
                marker = " <-- PC" if addr == target_pc else ""
                print(f"  0x{addr:04X}: 0x{value:02X}{marker}")
            print()

            break
        cpu.step()

    if not found:
        print(f"Did not reach PC=0x{target_pc:04X} within 30M cycles")

if __name__ == "__main__":
    debug_call()
