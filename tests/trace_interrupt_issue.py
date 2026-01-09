"""
Trace interrupt handling around the stuck delay loop at PC=0x0213

The emulator is stuck at PC=0x0213 (delay loop) with:
- IF=0x01 (VBlank interrupt pending)
- Should service interrupt but doesn't

This script traces:
1. IME (Interrupt Master Enable) state
2. IE (Interrupt Enable) register
3. IF (Interrupt Flags) register
4. Whether interrupts are being checked/serviced
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def trace_interrupts():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Load ROM correctly - don't overwrite I/O registers!
    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running to near stuck point...")
    print()

    # Run to just before the stuck point (cycle 600k)
    while cpu.total_cycles < 600_000:
        cpu.step()

    print(f"At cycle {cpu.total_cycles:,}")
    print()
    print("=" * 80)
    print("TRACING INTERRUPT STATE AROUND DELAY LOOP")
    print("=" * 80)
    print()

    last_serial_len = len(cpu.memory._serial_output)
    trace_count = 0
    max_trace = 500  # Trace 500 instructions

    try:
        while trace_count < max_trace:
            pc_before = cpu.registers._pc
            ime_before = cpu.ime
            ie = cpu.memory.read_byte(0xFFFF)
            if_reg = cpu.memory.read_byte(0xFF0F)

            # Execute
            cpu.step()

            ime_after = cpu.ime

            # Print state every instruction when near delay loop
            if 0x0200 <= pc_before <= 0x0230:
                from src.opcodes import OPCODES
                opcode = cpu.memory.read_byte(pc_before)
                instr_info = OPCODES.get(opcode, ["UNKNOWN", 1, 4, (0,0,0,0)])
                instr_name = instr_info[0]

                # Get instruction bytes
                instr_len = instr_info[1]
                instr_bytes = [f"{cpu.memory.read_byte(pc_before + i):02X}" for i in range(instr_len)]
                instr_hex = ' '.join(instr_bytes)

                # Highlight interrupt state
                interrupt_pending = (if_reg & ie) != 0
                ime_str = f"IME={int(ime_before)}"
                ie_str = f"IE=0x{ie:02X}"
                if_str = f"IF=0x{if_reg:02X}"

                marker = " <-- INTERRUPT SHOULD FIRE!" if (interrupt_pending and ime_before) else ""

                print(f"[{cpu.total_cycles:>9,}] PC=0x{pc_before:04X}: {instr_hex:8} {instr_name:20} | {ime_str} {ie_str} {if_str}{marker}")

                # Show if IME changed
                if ime_before != ime_after:
                    print(f"               ^^^ IME changed: {int(ime_before)} -> {int(ime_after)}")

            # Check serial
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                new_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in new_bytes)
                print()
                print(f"[{cpu.total_cycles:>9,}] >>> SERIAL: {repr(new_str)}")
                print()
                last_serial_len = current_serial_len

            trace_count += 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("FINAL STATE")
    print("=" * 80)
    ie = cpu.memory.read_byte(0xFFFF)
    if_reg = cpu.memory.read_byte(0xFF0F)
    print(f"IME: {cpu.ime}")
    print(f"IE:  0x{ie:02X}")
    print(f"IF:  0x{if_reg:02X}")
    print(f"PC:  0x{cpu.registers._pc:04X}")
    print()

    # Check if interrupts are enabled
    if ie == 0x00:
        print("PROBLEM: IE=0x00 - No interrupts are enabled!")
    if not cpu.ime:
        print("PROBLEM: IME=False - Interrupts are disabled!")
    if (if_reg & ie) != 0 and cpu.ime:
        print("PROBLEM: Interrupt pending and enabled but not serviced!")

if __name__ == "__main__":
    trace_interrupts()
