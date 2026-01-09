"""
Trace B register from when it hits 0 until critical PC

We know:
- B becomes 0 at PC=0x0846 around cycle 463,508
- B should be 0x03 at PC=0x0652 around cycle 1,513,588
- Need to find where B SHOULD be set to 0x03 but isn't
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_b_after_zero():
    """Trace B register after it hits zero"""
    cpu = CPU()

    # Load test ROM
    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory.write_byte(i, byte)

    print("Running to cycle 463,000 (just before B hits 0)...")

    # Run to just before B hits 0
    while cpu.total_cycles < 463_000:
        cpu.step()

    print(f"At cycle {cpu.total_cycles:,}, B={cpu.registers._b:02X}")
    print()
    print("=" * 80)
    print("TRACKING B REGISTER FROM THIS POINT TO CRITICAL PC")
    print("=" * 80)
    print()

    critical_pc = 0x0652
    b_modifications = []

    try:
        while cpu.total_cycles < 2_000_000:  # Go past critical PC
            pc_before = cpu.registers._pc
            b_before = cpu.registers._b

            cpu.step()

            b_after = cpu.registers._b

            # Track ALL B changes
            if b_before != b_after:
                from src.opcodes import OPCODES
                opcode = cpu.memory.read_byte(pc_before)
                instr_name = OPCODES.get(opcode, ["UNKNOWN"])[0] if opcode in OPCODES else f"0x{opcode:02X}"

                entry = f"[{cpu.total_cycles:>10}] PC=0x{pc_before:04X}: {instr_name:20} | B: 0x{b_before:02X} -> 0x{b_after:02X}"
                b_modifications.append(entry)
                print(entry)

            # Check if we hit critical PC
            if cpu.registers._pc == critical_pc:
                print()
                print("=" * 80)
                print(f"REACHED CRITICAL PC AT CYCLE {cpu.total_cycles:,}")
                print(f"B = 0x{cpu.registers._b:02X} (expected: 0x03)")
                print("=" * 80)
                break

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print(f"Total B modifications tracked: {len(b_modifications)}")
    print("=" * 80)

if __name__ == "__main__":
    trace_b_after_zero()
