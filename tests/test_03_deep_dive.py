"""
Deep dive into test 03 - trace execution from the start
"""

from src.cpu import CPU
from src.opcodes import OPCODES

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

print("Running until test 03 starts, then tracing SP/HL operations...")
print("=" * 70)

# Run until test 03 starts
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial and "test_03_started" not in locals():
        test_03_started = True
        print(f"Test 03 started at cycle {cpu.total_cycles:,}")
        print(f"Current serial: {repr(serial)}")
        break

# Now trace all SP/HL related operations
print("\nTracing SP/HL instructions and register changes...")
print("=" * 70)

sp_hl_opcodes = {
    0x39: "ADD HL,SP",
    0xF9: "LD SP,HL",
    0xE8: "ADD SP,n",
    0xF8: "LD HL,SP+n"
}

last_sp = cpu.registers._sp
last_hl = cpu.registers.hl
instruction_count = 0
max_instructions = 100000

while cpu.total_cycles < 30_000_000 and instruction_count < max_instructions:
    pc = cpu.registers._pc
    opcode = cpu.memory.read_byte(pc)

    # Track SP/HL changes from ANY instruction
    sp_before = cpu.registers._sp
    hl_before = cpu.registers.hl

    # Execute
    cpu.step()
    instruction_count += 1

    sp_after = cpu.registers._sp
    hl_after = cpu.registers.hl

    # Check for SP/HL specific instructions
    if opcode in sp_hl_opcodes:
        flags = f"Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}"

        if opcode == 0xE8 or opcode == 0xF8:
            immediate = cpu.memory.read_byte(pc + 1)
            signed = immediate if immediate < 128 else immediate - 256
            print(f"\n[{cpu.total_cycles:>10}] 0x{pc:04X}: {sp_hl_opcodes[opcode]} {signed:+d}")
        else:
            print(f"\n[{cpu.total_cycles:>10}] 0x{pc:04X}: {sp_hl_opcodes[opcode]}")

        print(f"  SP: 0x{sp_before:04X} -> 0x{sp_after:04X}")
        print(f"  HL: 0x{hl_before:04X} -> 0x{hl_after:04X}")
        print(f"  Flags: {flags}")

    # Check for unexpected SP/HL changes from other instructions
    elif sp_after != sp_before or hl_after != hl_before:
        # Filter out expected changes (PUSH, POP, INC/DEC, LD, etc.)
        expected_sp_change = opcode in [
            0xC5, 0xD5, 0xE5, 0xF5,  # PUSH
            0xC1, 0xD1, 0xE1, 0xF1,  # POP
            0x33, 0x3B,               # INC/DEC SP
            0xCD,                      # CALL
            0xC9, 0xD9,               # RET
            0xC4, 0xCC, 0xD4, 0xDC,   # CALL cc
            0xC0, 0xC8, 0xD0, 0xD8,   # RET cc
        ]

        expected_hl_change = opcode in [
            0x21,  # LD HL,nn
            0x2A,  # LDI A,(HL) / LD A,(HL+)
            0x23,  # INC HL
            0x2B,  # DEC HL
            0x22,  # LDI (HL),A
            0x32,  # LDD (HL),A
            0x3A,  # LDD A,(HL)
        ] or (opcode & 0xF0 == 0x60 or opcode & 0xF0 == 0x70)  # LD (HL),r / LD r,(HL)

        if not expected_sp_change and sp_after != sp_before:
            print(f"\n[{cpu.total_cycles:>10}] UNEXPECTED SP change at 0x{pc:04X} (opcode 0x{opcode:02X})")
            print(f"  SP: 0x{sp_before:04X} -> 0x{sp_after:04X}")

    # Check serial output
    serial = cpu.memory.get_serial_output()
    if ":" in serial and serial.count(":") > serial.count(":ok"):
        # Got a result code (error number)
        print(f"\n\n{'='*70}")
        print(f"Test 03 reported error!")
        print(f"Serial: {repr(serial)}")
        print(f"{'='*70}")
        break

    if cpu.halted and cpu.total_cycles > 15_000_000:
        print(f"\n\n{'='*70}")
        print(f"CPU halted at {cpu.total_cycles:,} cycles")
        print(f"PC: 0x{cpu.registers._pc:04X}")
        print(f"{'='*70}")
        break

print(f"\n{'='*70}")
print(f"Final state:")
print(f"  Cycles: {cpu.total_cycles:,}")
print(f"  PC: 0x{cpu.registers._pc:04X}")
print(f"  SP: 0x{cpu.registers._sp:04X}")
print(f"  HL: 0x{cpu.registers.hl:04X}")
print(f"  Halted: {cpu.halted}")
print(f"\nSerial output:")
print(cpu.memory.get_serial_output())
print(f"{'='*70}")
