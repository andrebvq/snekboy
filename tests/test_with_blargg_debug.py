"""
Debug version of Blargg test with last instruction tracking
"""

from src.cpu import CPU

def run_blargg_debug():
    cpu = CPU()

    # Load ROM
    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    print(f"Loaded {len(rom_data)} bytes of ROM at address 0x0000")

    # Copy ROM to memory
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("ROM loaded, running...")

    max_cycles = 30_000_000
    last_pcs = []  # Track last few PCs to detect loops
    instruction_count = 0
    last_serial_len = 0

    try:
        while cpu.total_cycles < max_cycles:
            pc_before = cpu.registers._pc
            opcode = cpu.memory.read_byte(pc_before)

            # Track last 100 PCs
            last_pcs.append(pc_before)
            if len(last_pcs) > 100:
                last_pcs.pop(0)

            # Detect infinite loops - DISABLED for debugging
            # if len(last_pcs) == 100 and len(set(last_pcs[-50:])) <= 2:
            #     print(f"\n[INFINITE LOOP DETECTED]")
            #     break

            cpu.step()
            instruction_count += 1

            # Check if we've printed final result
            serial_output = cpu.memory.get_serial_output()
            if 'Passed' in serial_output or 'Failed' in serial_output:
                print(f"\n[TEST COMPLETE]")
                break

    except Exception as e:
        print(f"\n[ERROR] Exception at PC=0x{cpu.registers._pc:04X}: {e}")
        print(f"  Opcode: 0x{cpu.memory.read_byte(cpu.registers._pc):02X}")
        import traceback
        traceback.print_exc()

    print(f"\n[DONE] Completed {cpu.total_cycles:,} cycles, {instruction_count:,} instructions")
    print(f"  Final PC: 0x{cpu.registers._pc:04X}")
    print(f"  Halted: {cpu.halted}")
    print(f"  IME: {cpu.ime}")
    print(f"  IE: 0x{cpu.memory.read_byte(0xFFFF):02X}")
    print(f"  IF: 0x{cpu.memory.read_byte(0xFF0F):02X}")

    # Print serial output
    serial_output = cpu.memory.get_serial_output()
    print(f"\n{'='*50}")
    print("SERIAL OUTPUT:")
    print(f"{'='*50}")
    print(serial_output)
    print(f"{'='*50}")

if __name__ == '__main__':
    run_blargg_debug()
