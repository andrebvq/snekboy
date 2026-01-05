"""
Monitor changes to memory at 0xC300 during test execution
"""

from src.cpu import CPU

def monitor_c300():
    cpu = CPU()

    # Load ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom_data = f.read()
    for i, byte in enumerate(rom_data):
        cpu.memory._data[i] = byte

    print("Monitoring memory at 0xC300-0xC310...")
    print("=" * 70)

    last_c300_snapshot = None
    check_interval = 1_000_000
    next_check = check_interval

    while cpu.total_cycles < 20_000_000:
        cpu.step()

        # Periodic check
        if cpu.total_cycles >= next_check:
            # Take snapshot of 0xC300-0xC310
            snapshot = tuple(cpu.memory.read_byte(addr) for addr in range(0xC300, 0xC311))

            if snapshot != last_c300_snapshot:
                print(f"\n[{cpu.total_cycles:>10}] Memory at 0xC300 changed:")
                hex_dump = " ".join(f"{b:02X}" for b in snapshot)
                ascii_dump = "".join(chr(b) if 32 <= b < 127 else "." for b in snapshot)
                print(f"  Hex:   {hex_dump}")
                print(f"  ASCII: {ascii_dump}")
                last_c300_snapshot = snapshot

            next_check += check_interval

        # Check serial output for test milestones
        serial = cpu.memory.get_serial_output()
        if "03" in serial and "milestone_03" not in locals():
            milestone_03 = True
            snapshot = tuple(cpu.memory.read_byte(addr) for addr in range(0xC300, 0xC311))
            print(f"\n[{cpu.total_cycles:>10}] **TEST 03 STARTED**")
            hex_dump = " ".join(f"{b:02X}" for b in snapshot)
            print(f"  0xC300-0xC310: {hex_dump}")
            last_c300_snapshot = snapshot

if __name__ == '__main__':
    monitor_c300()
