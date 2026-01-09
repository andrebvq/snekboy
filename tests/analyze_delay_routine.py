"""
Analyze the delay routine at 0x0213-0x022A

The routine appears to be:
- 0x0213: SUB 0x05
- 0x0215: JR NC,-4  (loop back to 0x0213 if no carry)
- ...more code...

Let's trace the A register through this routine to understand why it loops forever.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def analyze_delay():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Load ROM correctly
    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running to cycle 600k...")
    while cpu.total_cycles < 600_000:
        cpu.step()

    print(f"At cycle {cpu.total_cycles:,}")
    print(f"PC: 0x{cpu.registers._pc:04X}")
    print(f"A: 0x{cpu.registers._a:02X}")
    print()
    print("=" * 80)
    print("TRACING DELAY ROUTINE - WATCHING A REGISTER")
    print("=" * 80)
    print()

    trace_count = 0
    max_trace = 100
    last_a = cpu.registers._a

    # Track first entry to delay function
    delay_calls = []

    try:
        while trace_count < max_trace:
            pc_before = cpu.registers._pc
            a_before = cpu.registers._a

            # Detect CALL to 0x0213
            if pc_before == 0x0225:
                opcode = cpu.memory.read_byte(pc_before)
                if opcode == 0xCD:  # CALL nn
                    delay_calls.append((cpu.total_cycles, a_before))
                    print(f"[{cpu.total_cycles:>9,}] CALL 0x0213 with A=0x{a_before:02X}")

            cpu.step()

            a_after = cpu.registers._a

            # Track execution inside delay routine
            if 0x0213 <= pc_before <= 0x022A:
                if a_before != a_after or pc_before in [0x0213, 0x0217, 0x021A, 0x021C]:
                    from src.opcodes import OPCODES
                    opcode = cpu.memory.read_byte(pc_before)
                    instr_info = OPCODES.get(opcode, ["UNKNOWN", 1, 4, (0,0,0,0)])
                    instr_name = instr_info[0]

                    carry = "C" if cpu.registers.flags.carry else "-"
                    zero = "Z" if cpu.registers.flags.zero else "-"

                    print(f"  [{cpu.total_cycles:>9,}] 0x{pc_before:04X}: {instr_name:15} | A: 0x{a_before:02X} -> 0x{a_after:02X} | {zero}{carry}")

            # Stop after a few delay calls
            if len(delay_calls) >= 3:
                trace_count += 1
                if trace_count >= max_trace:
                    break

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print(f"Total delay calls traced: {len(delay_calls)}")
    for i, (cycle, a_val) in enumerate(delay_calls):
        print(f"  Call {i+1}: cycle {cycle:,}, A=0x{a_val:02X}")
    print("=" * 80)

if __name__ == "__main__":
    analyze_delay()
