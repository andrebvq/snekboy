"""
Detect where test 03 gets stuck in an infinite loop

Strategy:
- Track PC history over a sliding window
- If PC repeats the same small set of addresses for too long, we're in a loop
- Report the loop location and instruction sequence
"""
import sys
sys.path.insert(0, '.')

from src.cpu import CPU
from collections import deque, Counter

def detect_loop():
    cpu = CPU()

    rom_path = "test_roms/cpu_instrs.gb"
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Load ROM correctly - don't overwrite I/O registers!
    rom_size = min(len(rom_data), 0x8000)
    for i in range(rom_size):
        cpu.memory.write_byte(i, rom_data[i])

    print("Running test ROM with infinite loop detection...")
    print()

    # Track PC history
    pc_history = deque(maxlen=100000)  # Last 100k instructions
    check_interval = 10000  # Check every 10k instructions
    instruction_count = 0

    # Track serial output to know test progress
    last_serial_len = 0

    max_cycles = 30_000_000
    loop_detected = False

    try:
        while cpu.total_cycles < max_cycles:
            pc_before = cpu.registers._pc

            # Execute instruction
            cpu.step()

            pc_history.append(pc_before)
            instruction_count += 1

            # Check for serial output (test progress)
            current_serial_len = len(cpu.memory._serial_output)
            if current_serial_len > last_serial_len:
                new_bytes = cpu.memory._serial_output[last_serial_len:]
                new_str = ''.join(chr(b) if 32 <= b < 127 else f'[{b:02X}]' for b in new_bytes)
                print(f"[{cpu.total_cycles:>12,}] Serial: {repr(new_str)}")
                last_serial_len = current_serial_len

            # Periodically check for infinite loop
            if instruction_count % check_interval == 0:
                if len(pc_history) >= 10000:
                    # Count unique PCs in recent history
                    recent_pcs = list(pc_history)[-10000:]
                    pc_counter = Counter(recent_pcs)
                    unique_pcs = len(pc_counter)

                    # If only a few unique PCs dominate the recent history, we're likely in a loop
                    if unique_pcs <= 20:
                        print()
                        print("=" * 80)
                        print(f"INFINITE LOOP DETECTED at cycle {cpu.total_cycles:,}")
                        print(f"Instruction count: {instruction_count:,}")
                        print(f"Unique PCs in last 1000 instructions: {unique_pcs}")
                        print("=" * 80)
                        print()
                        print("Most common PCs:")
                        for pc, count in pc_counter.most_common(10):
                            print(f"  0x{pc:04X}: {count:4d} times")

                        print()
                        print("=" * 80)
                        print("LOOP INSTRUCTION SEQUENCE:")
                        print("=" * 80)

                        # Get the loop PCs
                        loop_pcs = [pc for pc, _ in pc_counter.most_common(10)]

                        # Disassemble the loop
                        from src.opcodes import OPCODES
                        for pc in sorted(set(loop_pcs)):
                            opcode = cpu.memory.read_byte(pc)
                            instr_info = OPCODES.get(opcode, ["UNKNOWN", 1, 4, (0,0,0,0)])
                            instr_name = instr_info[0]
                            instr_len = instr_info[1]

                            # Read operands if any
                            operands = []
                            for i in range(1, instr_len):
                                operands.append(cpu.memory.read_byte(pc + i))

                            operand_str = ' '.join([f'{b:02X}' for b in operands])
                            print(f"  0x{pc:04X}: {opcode:02X} {operand_str:8s} {instr_name}")

                        print()
                        print("=" * 80)
                        print("CURRENT CPU STATE:")
                        print("=" * 80)
                        print(f"PC: 0x{cpu.registers._pc:04X}")
                        print(f"SP: 0x{cpu.registers._sp:04X}")
                        print(f"AF: 0x{cpu.registers.af:04X} (A=0x{cpu.registers._a:02X}, F=0x{cpu.registers.flags.to_byte():02X})")
                        print(f"BC: 0x{cpu.registers.bc:04X} (B=0x{cpu.registers._b:02X}, C=0x{cpu.registers._c:02X})")
                        print(f"DE: 0x{cpu.registers.de:04X} (D=0x{cpu.registers._d:02X}, E=0x{cpu.registers._e:02X})")
                        print(f"HL: 0x{cpu.registers.hl:04X} (H=0x{cpu.registers._h:02X}, L=0x{cpu.registers._l:02X})")
                        print(f"Flags: Z={int(cpu.registers.flags.zero)} N={int(cpu.registers.flags.subtract)} "
                              f"H={int(cpu.registers.flags.half_carry)} C={int(cpu.registers.flags.carry)}")
                        print(f"IME: {cpu.ime}")
                        print(f"Halted: {cpu.halted}")
                        print()

                        # Check interrupt registers
                        ie = cpu.memory.read_byte(0xFFFF)
                        if_reg = cpu.memory.read_byte(0xFF0F)
                        print(f"IE (0xFFFF): 0x{ie:02X}")
                        print(f"IF (0xFF0F): 0x{if_reg:02X}")

                        print("=" * 80)

                        loop_detected = True
                        break

                # Progress indicator every 1M cycles
                if cpu.total_cycles % 1_000_000 == 0:
                    print(f"[{cpu.total_cycles:>12,}] Still running... PC=0x{cpu.registers._pc:04X}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    if loop_detected:
        print("RESULT: Infinite loop detected and analyzed")
    elif cpu.total_cycles >= max_cycles:
        print("RESULT: Timeout - reached 30M cycles")
    else:
        print("RESULT: Test completed or interrupted")
    print(f"Final cycle count: {cpu.total_cycles:,}")
    print("=" * 80)

if __name__ == "__main__":
    detect_loop()
