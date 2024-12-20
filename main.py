from cpu import CPU, Instruction, InstructionType, ArithmeticTarget
from tests import run_all_tests

def main():
    # Initialize CPU
    cpu = CPU()
    
    # Example: Execute an ADD instruction
    instruction = Instruction(InstructionType.ADD, ArithmeticTarget.B)
    
    print("Initial CPU state:")
    print(cpu)
    
    cpu.execute(instruction)
    
    print("\nFinal CPU state:")
    print(cpu)

if __name__ == "__main__":
    # Choose whether to run tests or main program
    RUN_TESTS = False
    
    if RUN_TESTS:
        run_all_tests()
    else:
        main()