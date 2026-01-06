"""
Find where 0x6000 (failure marker) was pushed onto the stack
"""

from src.cpu import CPU

cpu = CPU()

# Load ROM
with open("test_roms/cpu_instrs.gb", 'rb') as f:
    rom_data = f.read()
for i, byte in enumerate(rom_data):
    cpu.memory._data[i] = byte

# Run to test 03
print("Running to test 03...")
while cpu.total_cycles < 15_000_000:
    cpu.step()
    serial = cpu.memory.get_serial_output()
    if " 03" in serial:
        print(f"Test 03 started at cycle {cpu.total_cycles:,}\n")
        break

# Monitor stack writes
print("Monitoring stack for writes of 0x60 or 0x53 (path selection)...")
print("=" * 70)

# Track stack operations
stack_operations = []

while cpu.total_cycles < 13_000_000:
    pc = cpu.registers._pc
    sp_before = cpu.registers._sp

    cpu.step()

    sp_after = cpu.registers._sp

    # Check if SP decreased (PUSH/CALL)
    if sp_after < sp_before:
        # Read what was pushed
        bytes_pushed = []
        for addr in range(sp_after, sp_before):
            bytes_pushed.append(cpu.memory.read_byte(addr))

        # Check if this contains 0x60 or 0x53
        if len(bytes_pushed) >= 2:
            word_pushed = bytes_pushed[1] << 8 | bytes_pushed[0]  # Little-endian

            if (word_pushed & 0xFF00) == 0x6000 or (word_pushed & 0xFF00) == 0x5300:
                print(f"\n[{cpu.total_cycles:>10}] PC=0x{pc:04X}: Pushed 0x{word_pushed:04X} to stack")
                print(f"  SP: 0x{sp_before:04X} -> 0x{sp_after:04X}")
                print(f"  Bytes: {' '.join(f'0x{b:02X}' for b in bytes_pushed)}")

                if word_pushed == 0x6000:
                    print("  ^^^ FAILURE PATH MARKER!")
                    print(f"  A=0x{cpu.registers._a:02X}")
                    print(f"  Flags=Z{int(cpu.registers.flags.zero)} N{int(cpu.registers.flags.subtract)} H{int(cpu.registers.flags.half_carry)} C{int(cpu.registers.flags.carry)}")

                    # This is it! Let's see what happened before this
                    print(f"\n  Let's trace back a bit...")
                    break
                elif word_pushed == 0x5300:
                    print("  ^^^ SUCCESS PATH MARKER!")

    # Stop at POP DE
    if pc == 0x0877:
        print(f"\n{'='*70}")
        print(f"Reached POP DE at cycle {cpu.total_cycles}")
        break

print(f"\n{'='*70}")
print("Now let's see what instruction pushed 0x6000...")
