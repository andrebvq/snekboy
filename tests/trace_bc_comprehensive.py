"""
Comprehensive trace of BC register to find where test number SHOULD be set

The test number should be in B when we reach the encoding routine.
Tests 01 and 02 work, so there must be code that sets B correctly for them.
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_bc_to_critical():
    """Trace BC register comprehensively"""
    cpu = CPU()

    # Load test ROM
    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print("=" * 80)
    print("COMPREHENSIVE BC REGISTER TRACE")
    print("=" * 80)
    print()

    critical_pc = 0x0652
    bc_modifications = []

    # Track serial output to know which test we're in
    last_serial_len = 0

    try:
        while cpu.total_cycles < 30_000_000:
            pc_before = cpu.registers._pc
            bc_before = cpu.registers.bc
            b_before = cpu.registers._b
            c_before = cpu.registers._c

            cpu.step()

            bc_after = cpu.registers.bc
            b_after = cpu.registers._b
            c_after = cpu.registers._c

            # Check for serial output changes (test progress)
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_chars = cpu.memory._serial_output[last_serial_len:]
                print()
                print(f"[{cpu.total_cycles:>10}] SERIAL OUTPUT: {bytes(new_chars)}")
                print()
                last_serial_len = current_serial_len

            # Track BC changes
            if bc_before != bc_after:
                from src.opcodes import OPCODES
                opcode = cpu.memory.read_byte(pc_before)
                instr_name = OPCODES.get(opcode, ["UNKNOWN"])[0] if opcode in OPCODES else f"0x{opcode:02X}"

                entry = (f"[{cpu.total_cycles:>10}] PC=0x{pc_before:04X}: {instr_name:20} | "
                         f"BC: 0x{bc_before:04X} -> 0x{bc_after:04X} "
                         f"(B: 0x{b_before:02X}->0x{b_after:02X}, C: 0x{c_before:02X}->0x{c_after:02X})")

                bc_modifications.append(entry)

                # Print immediately if B changes to a value that could be a test number (1-11)
                if 1 <= b_after <= 11:
                    print(f">>> TEST NUMBER? {entry}")

            # Check if we hit critical PC
            if cpu.registers._pc == critical_pc:
                print()
                print("=" * 80)
                print(f"REACHED CRITICAL PC AT CYCLE {cpu.total_cycles:,}")
                print(f"BC = 0x{cpu.registers.bc:04X} (B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X})")
                print(f"Expected B = 0x03")
                print("=" * 80)
                print()
                print("LAST 30 BC MODIFICATIONS:")
                for entry in bc_modifications[-30:]:
                    print(entry)
                break

    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print(f"Total BC modifications: {len(bc_modifications)}")
    print("=" * 80)

if __name__ == "__main__":
    trace_bc_to_critical()
