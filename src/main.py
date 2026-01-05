from snekboy.src.cpu import CPU, Instruction, InstructionType, ArithmeticTarget

def main():
    # Initialize CPU
    cpu = CPU()
    
    # Example: Execute an ADD instruction
    instruction = Instruction(InstructionType.ADD, ArithmeticTarget.E)
    
    print("Initial CPU state:")
    print(cpu)
    
    cpu.execute(instruction)
    
    print("\nFinal CPU state:")
    print(cpu)

if __name__ == "__main__":
    main()