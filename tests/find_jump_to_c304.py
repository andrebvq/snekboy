"""
Find when and how PC jumps to 0xC304 (the bad infinite loop area)
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from src.opcodes import OPCODES

def find_bad_jump():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Looking for when PC jumps to 0xC304...")
    print()

    last_pcs = []  # Track last 20 PCs
    max_history = 20

    while cpu.total_cycles < 30_000_000:
        pc = cpu.registers._pc

        # Keep history
        last_pcs.append(pc)
        if len(last_pcs) > max_history:
            last_pcs.pop(0)

        # Check if we've reached the bad area
        if pc == 0xC304:
            print(f"={'='*80}")
            print(f"FOUND IT! PC reached 0xC304 at cycle {cpu.total_cycles:,}")
            print(f"={'='*80}")
            print()
            print("Last 20 PC values before reaching 0xC304:")
            for i, old_pc in enumerate(last_pcs[-20:]):
                print(f"  {i-19:>3}: 0x{old_pc:04X}")
            print()

            # Show the instruction that jumped here
            if len(last_pcs) >= 2:
                prev_pc = last_pcs[-2]
                opcode = cpu.memory.read_byte(prev_pc)
                instr_name = OPCODES.get(opcode, ["??"])[0]

                print(f"Previous PC: 0x{prev_pc:04X}")
                print(f"Instruction at previous PC: 0x{opcode:02X} ({instr_name})")

                # Show bytes at prev_pc
                print(f"\nBytes at 0x{prev_pc:04X}:")
                for offset in range(5):
                    addr = prev_pc + offset
                    val = cpu.memory.read_byte(addr)
                    marker = " <--" if offset == 0 else ""
                    print(f"  0x{addr:04X}: 0x{val:02X}{marker}")
                print()

            # Show registers
            print(f"Registers:")
            print(f"  A=0x{cpu.registers._a:02X} BC=0x{cpu.registers.bc:04X} DE=0x{cpu.registers.de:04X} HL=0x{cpu.registers.hl:04X} SP=0x{cpu.registers._sp:04X}")
            print(f"  Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
            print()

            # Show memory around 0xC304
            print("Memory around 0xC304:")
            for addr in range(0xC2F4, 0xC314):
                val = cpu.memory.read_byte(addr)
                marker = " <-- PC" if addr == 0xC304 else ""
                print(f"  0x{addr:04X}: 0x{val:02X}{marker}")

            break

        cpu.step()

    if cpu.total_cycles >= 30_000_000:
        print("Did not reach 0xC304 within 30M cycles")

if __name__ == "__main__":
    find_bad_jump()
