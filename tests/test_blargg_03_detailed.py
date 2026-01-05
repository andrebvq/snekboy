"""
Very detailed trace of test 03 execution near the end
"""

from src.cpu import CPU

def run_test_03_detailed():
    cpu = CPU()

    # Load ROM
    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Running test 03 with detailed execution trace near completion...")
    print("=" * 70)

    max_cycles = 30_000_000
    last_serial = ""
    trace_window = []  # Keep last 20 instructions

    try:
        while cpu.total_cycles < max_cycles:
            pc = cpu.registers._pc
            opcode = cpu.memory.read_byte(pc)

            # Track execution
            trace_entry = f"PC=0x{pc:04X} OP=0x{opcode:02X}"
            trace_window.append(trace_entry)
            if len(trace_window) > 20:
                trace_window.pop(0)

            # Check serial output
            serial = cpu.memory.get_serial_output()
            if serial != last_serial:
                new_chars = serial[len(last_serial):]
                print(f"\n[{cpu.total_cycles:>10}] SERIAL: {repr(new_chars)}")
                last_serial = serial

                # If we just printed "03", start detailed tracing
                if serial.endswith("03"):
                    print("\n" + "=" * 70)
                    print("Test 03 started - enabling detailed trace")
                    print("=" * 70)
                    trace_enabled = True
                else:
                    trace_enabled = False
            else:
                trace_enabled = False

            # Step CPU
            cpu.step()

            # Check if halted
            if cpu.halted:
                print(f"\n[{cpu.total_cycles:>10}] CPU HALTED at PC=0x{pc:04X}")
                print("\nLast 20 instructions before halt:")
                for entry in trace_window:
                    print(f"  {entry}")

                # Check CPU state
                print(f"\nCPU State:")
                print(f"  IME: {cpu.ime}")
                print(f"  IE:  0x{cpu.memory.read_byte(0xFFFF):02X}")
                print(f"  IF:  0x{cpu.memory.read_byte(0xFF0F):02X}")
                print(f"  SP:  0x{cpu.registers._sp:04X}")
                print(f"  HL:  0x{cpu.registers.hl:04X}")

                # Check if there's more serial output pending
                serial_after_halt = cpu.memory.get_serial_output()
                if serial_after_halt != last_serial:
                    print(f"\nSerial output after halt: {repr(serial_after_halt)}")

                # Try to continue for a bit to see if interrupt wakes it
                print(f"\nContinuing for 1000 more cycles to check for wake...")
                for _ in range(1000):
                    cpu.step()
                    if not cpu.halted:
                        print(f"  CPU woke up at cycle {cpu.total_cycles}")
                        break
                else:
                    print(f"  CPU still halted after 1000 cycles")
                    break

            # Check for test completion
            if 'Passed' in serial or 'Failed' in serial:
                print(f"\n[TEST COMPLETE]")
                break

        print(f"\n{'='*70}")
        print(f"Stopped at {cpu.total_cycles:,} cycles")
        print(f"Final PC: 0x{cpu.registers._pc:04X}")
        print(f"Halted: {cpu.halted}")

        print(f"\n{'='*70}")
        print("SERIAL OUTPUT:")
        print(f"{'='*70}")
        print(cpu.memory.get_serial_output())
        print(f"{'='*70}")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test_03_detailed()
