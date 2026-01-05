"""
Trace execution when test 03 starts to fail
"""

from src.cpu import CPU

def trace_test_03():
    cpu = CPU()

    # Load ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Running until test 03 starts...")

    # Run until test 03 prints
    while cpu.total_cycles < 15_000_000:
        cpu.step()
        serial = cpu.memory.get_serial_output()
        if "03" in serial:
            print(f"Test 03 started at cycle {cpu.total_cycles}")
            print(f"Serial so far: {repr(serial)}")
            break

    print("\nEnabling detailed trace...")
    print("=" * 70)

    trace_count = 0
    max_trace = 500000  # Trace up to 100 instructions

    while cpu.total_cycles < 30_000_000 and trace_count < max_trace:
        pc = cpu.registers._pc
        opcode = cpu.memory.read_byte(pc)
        sp = cpu.registers._sp
        hl = cpu.registers.hl

        # Only print if we're in the interesting area (0xC2F0-0xC320)
        if 0xC2F0 <= pc <= 0xC320:
            flags = f"Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}"
            print(f"[{cpu.total_cycles:>10}] PC=0x{pc:04X} OP=0x{opcode:02X} SP=0x{sp:04X} HL=0x{hl:04X} {flags}")

            # If we hit the error message area, something went wrong
            if pc == 0xC302:
                print("\n!!! PC is at 0xC302 - ERROR MESSAGE DATA !!!")
                print("This should never be executed!")
                break
            if pc >= 0xC303 and pc <= 0xC314:
                print(f"\n!!! PC is in error message data (0xC303-0xC314) !!!")
                break

        cpu.step()
        trace_count += 1

        # Check if halted in the danger zone
        if cpu.halted and 0xC300 <= cpu.registers._pc <= 0xC320:
            print(f"\n[HALTED] at PC=0x{cpu.registers._pc:04X}")
            break

        # Check serial output
        new_serial = cpu.memory.get_serial_output()
        if new_serial != serial:
            new_chars = new_serial[len(serial):]
            print(f"\n[SERIAL] {repr(new_chars)}")
            serial = new_serial

    print("\n" + "=" * 70)
    print(f"Trace stopped at {cpu.total_cycles:,} cycles")
    print(f"Final PC: 0x{cpu.registers._pc:04X}")
    print(f"Halted: {cpu.halted}")
    print("\nFinal serial output:")
    print(cpu.memory.get_serial_output())

if __name__ == '__main__':
    trace_test_03()
