"""
Deep trace of B register to find where it gets wrong value

According to docs/test_03_investigation_summary.md:
- At PC=0x0652 (cycle 12,784,220): B=0x02 (should be 0x03)
- This causes wrong test encoding (0x6000 instead of 0x5300)

We need to find WHERE B gets set to wrong value.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_b_register():
    """Trace execution and monitor B register changes"""
    cpu = CPU()

    # Load test ROM
    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print(f"Loaded {len(rom_data)} bytes")
    print("=" * 80)
    print("TRACING B REGISTER MODIFICATIONS")
    print("=" * 80)
    print()

    last_b_value = cpu.registers._b
    last_bc_value = cpu.registers.bc
    modification_count = 0
    max_cycles = 30_000_000

    # Track when we hit the critical point
    critical_pc = 0x0652
    critical_reached = False

    try:
        while cpu.total_cycles < max_cycles:
            pc_before = cpu.registers._pc
            b_before = cpu.registers._b
            bc_before = cpu.registers.bc

            # Execute one instruction
            cpu.step()

            b_after = cpu.registers._b
            bc_after = cpu.registers.bc

            # Check if B register changed (either directly or via BC)
            if b_before != b_after:
                modification_count += 1

                # Read the opcode that was executed
                opcode = cpu.memory.read_byte(pc_before)

                # Get instruction name from OPCODES table
                from src.opcodes import OPCODES
                instr_name = OPCODES.get(opcode, ["UNKNOWN"])[0] if opcode in OPCODES else f"0x{opcode:02X}"

                print(f"[{cpu.total_cycles:>10}] PC=0x{pc_before:04X}: {instr_name:20} | "
                      f"B: 0x{b_before:02X} -> 0x{b_after:02X} | "
                      f"BC: 0x{bc_before:04X} -> 0x{bc_after:04X}")

                last_b_value = b_after
                last_bc_value = bc_after

                # Stop if we've tracked enough modifications
                if modification_count > 100:
                    print()
                    print("=" * 80)
                    print(f"Tracked {modification_count} B register modifications")
                    print(f"Current B value: 0x{b_after:02X}")
                    print(f"Current BC value: 0x{bc_after:04X}")
                    print("=" * 80)
                    break

            # Check if we reached the critical point
            if cpu.registers._pc == critical_pc and not critical_reached:
                critical_reached = True
                print()
                print("=" * 80)
                print(f"REACHED CRITICAL PC: 0x{critical_pc:04X} at cycle {cpu.total_cycles}")
                print(f"B register value: 0x{cpu.registers._b:02X} (expected: 0x03)")
                print(f"BC register value: 0x{cpu.registers.bc:04X}")
                print("=" * 80)
                print()

                # If B is wrong, we found the problem already
                if cpu.registers._b != 0x03:
                    print(f"BUG CONFIRMED: B=0x{cpu.registers._b:02X} instead of 0x03")
                    print(f"Last modification at count: {modification_count}")
                else:
                    print(f"B value is CORRECT (0x03) at critical point!")

                break

    except KeyboardInterrupt:
        print("\nTrace interrupted")
    except Exception as e:
        print(f"\nTrace error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("TRACE COMPLETE")
    print(f"Total B modifications tracked: {modification_count}")
    print(f"Final B value: 0x{cpu.registers._b:02X}")
    print(f"Final BC value: 0x{cpu.registers.bc:04X}")
    print(f"Final cycles: {cpu.total_cycles:,}")
    print("=" * 80)

if __name__ == "__main__":
    trace_b_register()
