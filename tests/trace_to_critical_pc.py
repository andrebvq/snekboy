"""
Trace execution until we reach the critical PC where B should be 0x03

Critical point: PC=0x0652 where test number is encoded
Expected: B=0x03
Actual (per docs): B=0x02
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_to_critical_pc():
    """Run until critical PC and check B value"""
    cpu = CPU()

    # Load test ROM
    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print(f"Loaded {len(rom_data)} bytes")
    print("=" * 80)
    print("RUNNING TO CRITICAL PC: 0x0652")
    print("=" * 80)
    print()

    critical_pc = 0x0652
    max_cycles = 30_000_000

    # Track last few B register changes before critical PC
    b_history = []
    track_last_n = 20

    try:
        while cpu.total_cycles < max_cycles:
            pc_before = cpu.registers._pc
            b_before = cpu.registers._b
            bc_before = cpu.registers.bc

            # Check if we're at the critical PC BEFORE executing
            if pc_before == critical_pc:
                print("=" * 80)
                print(f"REACHED CRITICAL PC: 0x{critical_pc:04X}")
                print(f"Cycle: {cpu.total_cycles:,}")
                print(f"B register: 0x{cpu.registers._b:02X} (expected: 0x03)")
                print(f"BC register: 0x{cpu.registers.bc:04X}")
                print(f"A register: 0x{cpu.registers._a:02X}")
                print(f"DE register: 0x{cpu.registers.de:04X}")
                print(f"HL register: 0x{cpu.registers.hl:04X}")
                print(f"SP: 0x{cpu.registers._sp:04X}")
                print("=" * 80)
                print()

                # Show last few B register changes
                print("LAST 20 B REGISTER MODIFICATIONS:")
                print("-" * 80)
                for entry in b_history[-20:]:
                    print(entry)
                print("=" * 80)

                # Result
                if cpu.registers._b == 0x03:
                    print("SUCCESS: B register has correct value (0x03)")
                else:
                    print(f"BUG FOUND: B register is 0x{cpu.registers._b:02X}, expected 0x03")
                    print(f"Off by: {0x03 - cpu.registers._b}")

                break

            # Execute one instruction
            cpu.step()

            b_after = cpu.registers._b
            bc_after = cpu.registers.bc

            # Track B register changes
            if b_before != b_after:
                from src.opcodes import OPCODES
                opcode = cpu.memory.read_byte(pc_before)
                instr_name = OPCODES.get(opcode, ["UNKNOWN"])[0] if opcode in OPCODES else f"0x{opcode:02X}"

                entry = (f"[{cpu.total_cycles:>10}] PC=0x{pc_before:04X}: {instr_name:20} | "
                         f"B: 0x{b_before:02X} -> 0x{b_after:02X}")

                b_history.append(entry)

                # Keep only last N entries
                if len(b_history) > track_last_n * 2:
                    b_history = b_history[-track_last_n:]

            # Progress indicator every 1M cycles
            if cpu.total_cycles % 1_000_000 == 0:
                print(f"Cycle: {cpu.total_cycles:,} | PC: 0x{cpu.registers._pc:04X} | B: 0x{cpu.registers._b:02X}")

    except KeyboardInterrupt:
        print("\nTrace interrupted")
    except Exception as e:
        print(f"\nTrace error: {e}")
        import traceback
        traceback.print_exc()

    if cpu.total_cycles >= max_cycles:
        print()
        print("=" * 80)
        print("TIMEOUT: Did not reach critical PC within 30M cycles")
        print(f"Final PC: 0x{cpu.registers._pc:04X}")
        print(f"Final B: 0x{cpu.registers._b:02X}")
        print("=" * 80)

if __name__ == "__main__":
    trace_to_critical_pc()
