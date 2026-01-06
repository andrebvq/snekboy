"""
Trace ONLY test 03 execution with detailed SP/HL tracking
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run until test 03 starts
print("Fast-forwarding to test 03...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        print(f"Test 03 started at cycle {cpu.total_cycles:,}")
        print(f"Serial: {repr(serial)}\n")
        break

# Now do detailed tracing
print("Detailed trace of test 03:")
print("=" * 70)

sp_hl_ops = {
    0x39: "ADD HL,SP",
    0xF9: "LD SP,HL",
    0xE8: "ADD SP,n",
    0xF8: "LD HL,SP+n"
}

# Also track 16-bit ADD HL operations for comparison
add_hl_ops = {
    0x09: "ADD HL,BC",
    0x19: "ADD HL,DE",
    0x29: "ADD HL,HL",
    0x39: "ADD HL,SP"
}

trace_count = 0
max_trace = 500000

start_cycle = cpu.total_cycles
last_serial = serial

while cpu.total_cycles < 30_000_000 and trace_count < max_trace:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Trace SP/HL instructions
    if opcode in sp_hl_ops:
        trace_count += 1

        # Get instruction details
        if opcode in [0xE8, 0xF8]:
            imm = cpu.memory.read_byte(pc + 1)
            signed = imm if imm < 128 else imm - 256
            instr_str = f"{sp_hl_ops[opcode]} {signed:+d} (0x{imm:02X})"
        else:
            instr_str = sp_hl_ops[opcode]

        sp_before = cpu.registers._sp
        hl_before = cpu.registers.hl
        a_before = cpu.registers._a

        # Execute
        cpu.step()

        sp_after = cpu.registers._sp
        hl_after = cpu.registers.hl
        flags_after = f"Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}"

        print(f"\n[{cpu.total_cycles:>10}] PC=0x{pc:04X}: {instr_str}")
        print(f"  SP: 0x{sp_before:04X} -> 0x{sp_after:04X}")
        print(f"  HL: 0x{hl_before:04X} -> 0x{hl_after:04X}")
        print(f"  A:  0x{a_before:02X}")
        print(f"  Flags: {flags_after}")

        # Show some context
        if trace_count == 1:
            print(f"  ^^^ FIRST SP/HL instruction in test 03!")

    # Trace ADD HL,rr to see the pattern
    elif opcode in add_hl_ops and opcode != 0x39:
        hl_before = cpu.registers.hl
        cpu.step()
        hl_after = cpu.registers.hl
        flags_after = f"Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}"

        if trace_count < 20:  # Only print first few
            print(f"\n[{cpu.total_cycles:>10}] PC=0x{pc:04X}: {add_hl_ops[opcode]}")
            print(f"  HL: 0x{hl_before:04X} -> 0x{hl_after:04X}, Flags: {flags_after}")
    else:
        cpu.step()

    # Check for serial output changes
    serial = cpu.memory.get_serial_output()
    if serial != last_serial:
        new = serial[len(last_serial):]
        print(f"\n{'='*70}")
        print(f"[{cpu.total_cycles:>10}] SERIAL OUTPUT: {repr(new)}")
        print(f"{'='*70}")
        last_serial = serial

        # Check for test result
        if ":ok" in new or ("03:" in serial and serial.index("03:") > serial.rindex("02:")):
            print("\nTest 03 completed with result!")
            break

    # Check for halt
    if cpu.halted and cpu.total_cycles - start_cycle > 5_000_000:
        print(f"\n{'='*70}")
        print(f"CPU HALTED at {cpu.total_cycles:,}")
        print(f"PC: 0x{cpu.registers._pc:04X}")
        print(f"{'='*70}")
        break

print(f"\n{'='*70}")
print(f"Trace summary:")
print(f"  Total SP/HL instructions: {trace_count}")
print(f"  Final cycle: {cpu.total_cycles:,}")
print(f"  Duration: {cpu.total_cycles - start_cycle:,} cycles")
print(f"\nFinal serial:")
print(cpu.memory.get_serial_output())
print(f"{'='*70}")
