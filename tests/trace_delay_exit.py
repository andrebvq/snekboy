"""
Trace the exact moment when delay should exit

Focus on when A becomes small enough that SUB 0x05 causes underflow
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running to cycle 12.34M (just after '03' printed)...")
    while cpu.total_cycles < 12_340_000:
        cpu.step()

    print(f"At cycle {cpu.total_cycles:,}")
    print()

    # Now trace delay routine, watching for A < 5
    print("=" * 80)
    print("WATCHING FOR A < 5 (when SUB should underflow)")
    print("=" * 80)
    print()

    found_underflow = False
    trace_after_underflow = 0

    while cpu.total_cycles < 13_000_000:
        pc_before = cpu.registers._pc
        a_before = cpu.registers._a

        # Check if we're at SUB instruction with A < 5
        if pc_before == 0x0213:
            opcode = cpu.memory.read_byte(pc_before)
            operand = cpu.memory.read_byte(pc_before + 1)

            if a_before <= 5:  # This SUB will cause underflow
                carry_before = cpu.registers.flags.carry
                cpu.step()
                carry_after = cpu.registers.flags.carry
                a_after = cpu.registers._a

                print(f"[{cpu.total_cycles:>12,}] PC=0x{pc_before:04X}: SUB 0x{operand:02X}")
                print(f"    A: 0x{a_before:02X} -> 0x{a_after:02X}")
                print(f"    Carry: {carry_before} -> {carry_after}")
                print(f"    Expected: Carry should be True (underflow)")

                if not carry_after:
                    print(f"    ERROR: Carry not set after underflow!")

                found_underflow = True
                trace_after_underflow = 20  # Trace next 20 instructions
                continue

        # Trace instructions after underflow
        if trace_after_underflow > 0:
            from src.opcodes import OPCODES
            opcode = cpu.memory.read_byte(pc_before)
            instr_info = OPCODES.get(opcode, ["UNKNOWN", 1, 4, (0,0,0,0)])
            instr_name = instr_info[0]

            carry = "C" if cpu.registers.flags.carry else "-"
            zero = "Z" if cpu.registers.flags.zero else "-"

            cpu.step()

            a_after = cpu.registers._a
            pc_after = cpu.registers._pc

            print(f"[{cpu.total_cycles:>12,}] PC=0x{pc_before:04X}: {instr_name:15} | A=0x{a_before:02X} {zero}{carry} -> PC=0x{pc_after:04X}")

            trace_after_underflow -= 1

            if trace_after_underflow == 0:
                break
        else:
            cpu.step()

if __name__ == "__main__":
    trace()
