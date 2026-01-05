"""
Exactly replicate the delay loop to see if SUB works
"""

from src.cpu import CPU

def test_sub_loop():
    cpu = CPU()

    # Load the actual ROM
    with open("test_roms/cpu_instrs.gb", 'rb') as f:
        rom = f.read()
    for i, b in enumerate(rom):
        cpu.memory._data[i] = b

    # Set initial state - assume A starts at 0xDF like in Reddit post
    cpu.registers._a = 0xDF  # 223
    cpu.registers._pc = 0x0213

    print("Simulating the delay loop SUB A, 5; JR NC, -4")
    print("=" * 60)
    print(f"Initial A: 0x{cpu.registers._a:02X} ({cpu.registers._a})")

    for iteration in range(50):
        # Execute SUB A, 5 at 0x0213
        cpu.registers._pc = 0x0213
        cpu.step()  # Should execute SUB

        a_after_sub = cpu.registers._a
        carry_after_sub = cpu.registers.flags.carry

        print(f"Iteration {iteration}: A=0x{a_after_sub:02X} ({a_after_sub}), Carry={carry_after_sub}")

        if carry_after_sub:
            print(f"  → Carry set! Loop should exit.")
            break

        # Manually reset PC for next iteration (simulating the JR)
        cpu.registers._pc = 0x0213

    print("=" * 60)

if __name__ == '__main__':
    test_sub_loop()
