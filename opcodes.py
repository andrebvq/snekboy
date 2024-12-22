# Game Boy CPU Opcodes
# Structure:
# opcode: [Instruction name, instruction length in bytes, machine cyc`les, flags affected]
# Flags: Z N H C (in that order)
# 0 = flag not affected
# 1 = flag is affected
# - = flag is reset
# + = flag is set

OPCODES = {
    # 8-bit loads
    0x06: ["LD B,n", 2, 8, (0,0,0,0)],    # Load immediate into B
    0x0E: ["LD C,n", 2, 8, (0,0,0,0)],    # Load immediate into C
    0x16: ["LD D,n", 2, 8, (0,0,0,0)],    # Load immediate into D
    0x1E: ["LD E,n", 2, 8, (0,0,0,0)],    # Load immediate into E
    0x26: ["LD H,n", 2, 8, (0,0,0,0)],    # Load immediate into H
    0x2E: ["LD L,n", 2, 8, (0,0,0,0)],    # Load immediate into L
    0x3E: ["LD A,n", 2, 8, (0,0,0,0)],    # Load immediate into A
    
    # Register to register loads
    0x7F: ["LD A,A", 1, 4, (0,0,0,0)],
    0x78: ["LD A,B", 1, 4, (0,0,0,0)],
    0x79: ["LD A,C", 1, 4, (0,0,0,0)],
    0x7A: ["LD A,D", 1, 4, (0,0,0,0)],
    0x7B: ["LD A,E", 1, 4, (0,0,0,0)],
    0x7C: ["LD A,H", 1, 4, (0,0,0,0)],
    0x7D: ["LD A,L", 1, 4, (0,0,0,0)],
    
    # 16-bit loads
    0x01: ["LD BC,nn", 3, 12, (0,0,0,0)],  # Load 16-bit immediate into BC
    0x11: ["LD DE,nn", 3, 12, (0,0,0,0)],  # Load 16-bit immediate into DE
    0x21: ["LD HL,nn", 3, 12, (0,0,0,0)],  # Load 16-bit immediate into HL
    0x31: ["LD SP,nn", 3, 12, (0,0,0,0)],  # Load 16-bit immediate into SP
    
    # Load from/to memory
    0x02: ["LD (BC),A", 1, 8, (0,0,0,0)],
    0x12: ["LD (DE),A", 1, 8, (0,0,0,0)],
    0x77: ["LD (HL),A", 1, 8, (0,0,0,0)],
    0x0A: ["LD A,(BC)", 1, 8, (0,0,0,0)],
    0x1A: ["LD A,(DE)", 1, 8, (0,0,0,0)],
    0x7E: ["LD A,(HL)", 1, 8, (0,0,0,0)],
    
    # Stack operations
    0xC5: ["PUSH BC", 1, 16, (0,0,0,0)],
    0xD5: ["PUSH DE", 1, 16, (0,0,0,0)],
    0xE5: ["PUSH HL", 1, 16, (0,0,0,0)],
    0xF5: ["PUSH AF", 1, 16, (0,0,0,0)],
    0xC1: ["POP BC", 1, 12, (0,0,0,0)],
    0xD1: ["POP DE", 1, 12, (0,0,0,0)],
    0xE1: ["POP HL", 1, 12, (0,0,0,0)],
    0xF1: ["POP AF", 1, 12, (1,1,1,1)],    # Flags affected when popping AF
    
    # 8-bit arithmetic/logic
    0x80: ["ADD A,B", 1, 4, (1,0,1,1)],
    0x81: ["ADD A,C", 1, 4, (1,0,1,1)],
    0x82: ["ADD A,D", 1, 4, (1,0,1,1)],
    0x83: ["ADD A,E", 1, 4, (1,0,1,1)],
    0x84: ["ADD A,H", 1, 4, (1,0,1,1)],
    0x85: ["ADD A,L", 1, 4, (1,0,1,1)],
    0x86: ["ADD A,(HL)", 1, 8, (1,0,1,1)],
    0x87: ["ADD A,A", 1, 4, (1,0,1,1)],
    0xC6: ["ADD A,n", 2, 8, (1,0,1,1)],
    
    # Subtract
    0x90: ["SUB B", 1, 4, (1,1,1,1)],
    0x91: ["SUB C", 1, 4, (1,1,1,1)],
    0x92: ["SUB D", 1, 4, (1,1,1,1)],
    0x93: ["SUB E", 1, 4, (1,1,1,1)],
    0x94: ["SUB H", 1, 4, (1,1,1,1)],
    0x95: ["SUB L", 1, 4, (1,1,1,1)],
    0x96: ["SUB (HL)", 1, 8, (1,1,1,1)],
    0x97: ["SUB A", 1, 4, (1,1,1,1)],
    0xD6: ["SUB n", 2, 8, (1,1,1,1)],
    
    # Increment/Decrement
    0x04: ["INC B", 1, 4, (1,0,1,0)],
    0x0C: ["INC C", 1, 4, (1,0,1,0)],
    0x14: ["INC D", 1, 4, (1,0,1,0)],
    0x1C: ["INC E", 1, 4, (1,0,1,0)],
    0x24: ["INC H", 1, 4, (1,0,1,0)],
    0x2C: ["INC L", 1, 4, (1,0,1,0)],
    0x3C: ["INC A", 1, 4, (1,0,1,0)],
    0x05: ["DEC B", 1, 4, (1,1,1,0)],
    0x0D: ["DEC C", 1, 4, (1,1,1,0)],
    0x15: ["DEC D", 1, 4, (1,1,1,0)],
    0x1D: ["DEC E", 1, 4, (1,1,1,0)],
    0x25: ["DEC H", 1, 4, (1,1,1,0)],
    0x2D: ["DEC L", 1, 4, (1,1,1,0)],
    0x3D: ["DEC A", 1, 4, (1,1,1,0)],
    
    # Jump instructions
    0xC3: ["JP nn", 3, 16, (0,0,0,0)],     # Jump to immediate address
    0xC2: ["JP NZ,nn", 3, 16, (0,0,0,0)],  # Jump if not zero
    0xCA: ["JP Z,nn", 3, 16, (0,0,0,0)],   # Jump if zero
    0xD2: ["JP NC,nn", 3, 16, (0,0,0,0)],  # Jump if no carry
    0xDA: ["JP C,nn", 3, 16, (0,0,0,0)],   # Jump if carry
    0x18: ["JR n", 2, 12, (0,0,0,0)],      # Relative jump
    0x20: ["JR NZ,n", 2, 12, (0,0,0,0)],   # Relative jump if not zero
    0x28: ["JR Z,n", 2, 12, (0,0,0,0)],    # Relative jump if zero
    0x30: ["JR NC,n", 2, 12, (0,0,0,0)],   # Relative jump if no carry
    0x38: ["JR C,n", 2, 12, (0,0,0,0)],    # Relative jump if carry
    
    # Call and return
    0xCD: ["CALL nn", 3, 24, (0,0,0,0)],   # Call subroutine
    0xC4: ["CALL NZ,nn", 3, 24, (0,0,0,0)],# Call if not zero
    0xCC: ["CALL Z,nn", 3, 24, (0,0,0,0)], # Call if zero
    0xD4: ["CALL NC,nn", 3, 24, (0,0,0,0)],# Call if no carry
    0xDC: ["CALL C,nn", 3, 24, (0,0,0,0)], # Call if carry
    0xC9: ["RET", 1, 16, (0,0,0,0)],       # Return from subroutine
    0xC0: ["RET NZ", 1, 20, (0,0,0,0)],    # Return if not zero
    0xC8: ["RET Z", 1, 20, (0,0,0,0)],     # Return if zero
    0xD0: ["RET NC", 1, 20, (0,0,0,0)],    # Return if no carry
    0xD8: ["RET C", 1, 20, (0,0,0,0)],     # Return if carry
    
    # Restart vectors
    0xC7: ["RST 00H", 1, 16, (0,0,0,0)],
    0xCF: ["RST 08H", 1, 16, (0,0,0,0)],
    0xD7: ["RST 10H", 1, 16, (0,0,0,0)],
    0xDF: ["RST 18H", 1, 16, (0,0,0,0)],
    0xE7: ["RST 20H", 1, 16, (0,0,0,0)],
    0xEF: ["RST 28H", 1, 16, (0,0,0,0)],
    0xF7: ["RST 30H", 1, 16, (0,0,0,0)],
    0xFF: ["RST 38H", 1, 16, (0,0,0,0)],
    
    # Rotates and shifts
    0x07: ["RLCA", 1, 4, (0,0,0,1)],       # Rotate A left
    0x17: ["RLA", 1, 4, (0,0,0,1)],        # Rotate A left through carry
    0x0F: ["RRCA", 1, 4, (0,0,0,1)],       # Rotate A right
    0x1F: ["RRA", 1, 4, (0,0,0,1)],        # Rotate A right through carry
    
    # Control
    0x00: ["NOP", 1, 4, (0,0,0,0)],        # No operation
    0x76: ["HALT", 1, 4, (0,0,0,0)],       # Halt until interrupt
    0x10: ["STOP", 2, 4, (0,0,0,0)],       # Stop processor
    0xF3: ["DI", 1, 4, (0,0,0,0)],         # Disable interrupts
    0xFB: ["EI", 1, 4, (0,0,0,0)],         # Enable interrupts
}

# CB-prefixed instructions (accessed via 0xCB prefix)
CB_OPCODES = {
    0x00: ["RLC B", 2, 8, (1,0,0,1)],      # Rotate left
    0x01: ["RLC C", 2, 8, (1,0,0,1)],
    0x02: ["RLC D", 2, 8, (1,0,0,1)],
    0x03: ["RLC E", 2, 8, (1,0,0,1)],
    0x04: ["RLC H", 2, 8, (1,0,0,1)],
    0x05: ["RLC L", 2, 8, (1,0,0,1)],
    0x06: ["RLC (HL)", 2, 16, (1,0,0,1)],
    0x07: ["RLC A", 2, 8, (1,0,0,1)],
    
    # Bit operations
    0x40: ["BIT 0,B", 2, 8, (1,0,1,0)],    # Test bit 0
    0x41: ["BIT 0,C", 2, 8, (1,0,1,0)],
    0x42: ["BIT 0,D", 2, 8, (1,0,1,0)],
    0x43: ["BIT 0,E", 2, 8, (1,0,1,0)],
    0x44: ["BIT 0,H", 2, 8, (1,0,1,0)],
    0x45: ["BIT 0,L", 2, 8, (1,0,1,0)],
    0x46: ["BIT 0,(HL)", 2, 12, (1,0,1,0)],
    0x47: ["BIT 0,A", 2, 8, (1,0,1,0)],
    
    # Set operations
    0xC0: ["SET 0,B", 2, 8, (0,0,0,0)],    # Set bit 0
    0xC1: ["SET 0,C", 2]
}
