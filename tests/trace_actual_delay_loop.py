"""
Trace the delay loop in the actual Blargg test to see why it doesn't exit
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU

def get_f_register(flags):
    f = 0
    if flags.zero: f |= 0x80
    if flags.subtract: f |= 0x40
    if flags.half_carry: f |= 0x20
    if flags.carry: f |= 0x10
    return f

def trace_delay():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    # Run until test 03 serial output
    last_serial_len = 0
    while cpu.total_cycles < 30_000_000:
        current_serial_len = len(cpu.memory._serial_output)
        if current_serial_len > last_serial_len:
            full_serial = ''.join(chr(b) if 32 <= b < 127 else '' for b in cpu.memory._serial_output)
            if '03' in full_serial:
                print(f"Test 03 started at cycle {cpu.total_cycles:,}")
                break
            last_serial_len = current_serial_len
        cpu.step()

    # Now trace until we enter the delay loop at 0x0213
    print("Tracing until we reach delay loop at 0x0213...")
    loop_count = 0
    while cpu.total_cycles < 30_000_000 and loop_count < 1000:
        pc = cpu.registers._pc
        if pc == 0x0213:
            loop_count += 1
        cpu.step()

    if loop_count == 0:
        print("Never entered delay loop!")
        return

    print(f"Entered delay loop {loop_count} times before timeout")
    print(f"Current state at delay loop entry:")
    print(f"  PC=0x{cpu.registers._pc:04X}")
    print(f"  A=0x{cpu.registers._a:02X} F=0x{get_f_register(cpu.registers.flags):02X}")
    print()

    # Now trace the delay loop execution in detail
    print("Detailed trace of delay loop (up to 200 iterations):")
    print("=" * 80)

    iterations = 0
    a_values = []

    while iterations < 200:
        pc = cpu.registers._pc

        if pc != 0x0213 and pc != 0x0215:
            print(f"\nExited delay loop at PC=0x{pc:04X} after {iterations} iterations")
            break

        a_before = cpu.registers._a
        cpu.step()
        a_after = cpu.registers._a
        f_after = get_f_register(cpu.registers.flags)

        z = int(cpu.registers.flags.zero)
        n = int(cpu.registers.flags.subtract)
        h = int(cpu.registers.flags.half_carry)
        c = int(cpu.registers.flags.carry)

        if pc == 0x0213:  # SUB instruction
            print(f"[{iterations:>3}] SUB: A=0x{a_before:02X}->0x{a_after:02X} F=0x{f_after:02X} (Z={z} N={n} H={h} C={c})")
            a_values.append(a_after)

            # Check if this should have exited
            if c == 1:
                print(f"  *** Carry SET, should exit loop! ***")

        iterations += 1

    if iterations >= 200:
        print(f"\n*** Loop did not exit after {iterations} iterations ***")
        print(f"Final A=0x{cpu.registers._a:02X}")
        print(f"A value pattern: {', '.join(f'0x{v:02X}' for v in a_values[-10:])}")

if __name__ == "__main__":
    trace_delay()
