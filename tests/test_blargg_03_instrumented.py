"""
Instrumented version of test 03 to trace SP/HL instruction execution
"""

from src.cpu import CPU

def run_test_03_instrumented():
    cpu = CPU()

    # Load ROM
    rom_path = "test_roms/cpu_instrs/individual/03-op sp,hl.gb"
    try:
        with open(rom_path, 'rb') as f:
            rom_data = f.read()
    except FileNotFoundError:
        print(f"File not found: {rom_path}")
        print("Trying main cpu_instrs.gb instead...")
        rom_path = "test_roms/cpu_instrs.gb"
        with open(rom_path, 'rb') as f:
            rom_data = f.read()

    print(f"Loaded {len(rom_data)} bytes from {rom_path}")

    # Copy ROM to memory
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Running test with SP/HL instruction tracing...\n")

    # Track SP/HL instructions
    sp_hl_opcodes = {
        0x39: "ADD HL,SP",
        0xF9: "LD SP,HL",
        0xE8: "ADD SP,n",
        0xF8: "LD HL,SP+n"
    }

    instruction_counts = {opcode: 0 for opcode in sp_hl_opcodes}
    max_cycles = 30_000_000
    last_serial_len = 0

    try:
        while cpu.total_cycles < max_cycles:
            pc = cpu.registers._pc
            opcode = cpu.memory.read_byte(pc)

            # Check if this is a SP/HL instruction
            if opcode in sp_hl_opcodes:
                instruction_counts[opcode] += 1

                # Get instruction details BEFORE execution
                sp_before = cpu.registers._sp
                hl_before = cpu.registers.hl
                flags_before = {
                    'Z': cpu.registers.flags.zero,
                    'N': cpu.registers.flags.subtract,
                    'H': cpu.registers.flags.half_carry,
                    'C': cpu.registers.flags.carry
                }

                # For instructions with immediate values
                if opcode == 0xE8 or opcode == 0xF8:
                    immediate = cpu.memory.read_byte(pc + 1)
                    signed_offset = immediate if immediate < 128 else immediate - 256
                else:
                    signed_offset = None

                # Execute the instruction
                cpu.step()

                # Get state AFTER execution
                sp_after = cpu.registers._sp
                hl_after = cpu.registers.hl
                flags_after = {
                    'Z': cpu.registers.flags.zero,
                    'N': cpu.registers.flags.subtract,
                    'H': cpu.registers.flags.half_carry,
                    'C': cpu.registers.flags.carry
                }

                # Print detailed trace (only first 10 of each to avoid spam)
                if instruction_counts[opcode] <= 10:
                    print(f"\n[{cpu.total_cycles:>10}] PC=0x{pc:04X}: {sp_hl_opcodes[opcode]}")
                    if signed_offset is not None:
                        print(f"  Offset: {signed_offset:+d} (0x{immediate:02X})")
                    print(f"  Before: SP=0x{sp_before:04X}, HL=0x{hl_before:04X}")
                    print(f"  After:  SP=0x{sp_after:04X}, HL=0x{hl_after:04X}")
                    print(f"  Flags:  {flags_before} -> {flags_after}")
            else:
                cpu.step()

            # Check for test completion
            serial_output = cpu.memory.get_serial_output()
            if len(serial_output) > last_serial_len:
                new_chars = serial_output[last_serial_len:]
                print(f"\n[SERIAL] {repr(new_chars)}", end='', flush=True)
                last_serial_len = len(serial_output)

            if 'Passed' in serial_output or 'Failed' in serial_output:
                print(f"\n\n[TEST COMPLETE]")
                break

        print(f"\n\n{'='*60}")
        print(f"Test completed at {cpu.total_cycles:,} cycles")
        print(f"Final PC: 0x{cpu.registers._pc:04X}")
        print(f"Halted: {cpu.halted}")

        print(f"\n{'='*60}")
        print("SP/HL Instruction Counts:")
        print(f"{'='*60}")
        for opcode, name in sp_hl_opcodes.items():
            count = instruction_counts[opcode]
            print(f"  0x{opcode:02X} {name:15s}: {count:,}")

        print(f"\n{'='*60}")
        print("SERIAL OUTPUT:")
        print(f"{'='*60}")
        print(cpu.memory.get_serial_output())
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n[ERROR] Exception at PC=0x{cpu.registers._pc:04X}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test_03_instrumented()
