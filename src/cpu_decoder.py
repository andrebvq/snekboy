"""
CPU Instruction Decoder

Handles decoding opcodes into instruction parameters.
This file gets the opcode patterns and extracts target/source info.
"""

from enum import Enum, auto

class InstructionType(Enum):
    """All instruction types"""
    ADD = auto()
    SUB = auto()
    INC = auto()
    DEC = auto()
    LD = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    CP = auto()
    PUSH = auto()
    POP = auto()
    JP = auto()
    JP_HL = auto()
    JR = auto()
    CALL = auto()
    RET = auto()
    NOP = auto()
    HALT = auto()
    STOP = auto()
    DI = auto()
    EI = auto()
    SCF = auto()
    CCF = auto()
    CPL = auto()
    DAA = auto()
    RLCA = auto()
    RLA = auto()
    RRCA = auto()
    RRA = auto()
    INC_16 = auto()
    DEC_16 = auto()
    ADD_HL = auto()
    LDI = auto()
    LDD = auto()
    LDH = auto()
    LD_ADDR = auto()
    ADC = auto()
    SBC = auto()
    RETI = auto()
    RST = auto()
    LD_SP_HL = auto()
    LD_HL_SP_N = auto()
    LD_NN_SP = auto()
    # CB-prefixed instructions
    RLC = auto()    # Rotate Left Circular
    RRC = auto()    # Rotate Right Circular
    RL = auto()     # Rotate Left through carry
    RR = auto()     # Rotate Right through carry
    SLA = auto()    # Shift Left Arithmetic
    SRA = auto()    # Shift Right Arithmetic
    SRL = auto()    # Shift Right Logical
    SWAP = auto()   # Swap nibbles
    BIT = auto()    # Test bit
    RES = auto()    # Reset bit
    SET = auto()    # Set bit


def decode_instruction_params(opcode, fetch_byte_func, fetch_word_func):
    """
    Decode opcode and return (InstructionType, target, source/immediate)

    Args:
        opcode: The opcode byte
        fetch_byte_func: Function to fetch next byte
        fetch_word_func: Function to fetch next word

    Returns:
        (instruction_type, target, immediate_value)
    """

    # === CONTROL ===
    if opcode == 0x00:
        return (InstructionType.NOP, None, None)

    if opcode == 0x76:
        return (InstructionType.HALT, None, None)

    if opcode == 0x10:
        # STOP has 2-byte length (opcode + 0x00)
        fetch_byte_func()  # Consume the extra byte
        return (InstructionType.STOP, None, None)

    if opcode == 0xF3:
        return (InstructionType.DI, None, None)

    if opcode == 0xFB:
        return (InstructionType.EI, None, None)

    # === MISC ===
    if opcode == 0x37:
        return (InstructionType.SCF, None, None)

    if opcode == 0x3F:
        return (InstructionType.CCF, None, None)

    if opcode == 0x2F:
        return (InstructionType.CPL, None, None)

    if opcode == 0x27:
        return (InstructionType.DAA, None, None)

    # === ADD A,r ===
    if 0x80 <= opcode <= 0x87:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.ADD, targets[opcode - 0x80], None)

    if opcode == 0xC6:  # ADD A,n
        immediate = fetch_byte_func()
        return (InstructionType.ADD, 'IMMEDIATE', immediate)

    # === SUB r ===
    if 0x90 <= opcode <= 0x97:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.SUB, targets[opcode - 0x90], None)

    if opcode == 0xD6:  # SUB n
        immediate = fetch_byte_func()
        return (InstructionType.SUB, 'IMMEDIATE', immediate)

    # === AND r ===
    if 0xA0 <= opcode <= 0xA7:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.AND, targets[opcode - 0xA0], None)

    if opcode == 0xE6:  # AND n
        immediate = fetch_byte_func()
        return (InstructionType.AND, 'IMMEDIATE', immediate)

    # === OR r ===
    if 0xB0 <= opcode <= 0xB7:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.OR, targets[opcode - 0xB0], None)

    if opcode == 0xF6:  # OR n
        immediate = fetch_byte_func()
        return (InstructionType.OR, 'IMMEDIATE', immediate)

    # === XOR r ===
    if 0xA8 <= opcode <= 0xAF:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.XOR, targets[opcode - 0xA8], None)

    if opcode == 0xEE:  # XOR n
        immediate = fetch_byte_func()
        return (InstructionType.XOR, 'IMMEDIATE', immediate)

    # === CP r ===
    if 0xB8 <= opcode <= 0xBF:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.CP, targets[opcode - 0xB8], None)

    if opcode == 0xFE:  # CP n
        immediate = fetch_byte_func()
        return (InstructionType.CP, 'IMMEDIATE', immediate)

    # === INC r ===
    if opcode in [0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x34, 0x3C]:
        targets = {
            0x04: 'B', 0x0C: 'C', 0x14: 'D', 0x1C: 'E',
            0x24: 'H', 0x2C: 'L', 0x34: '(HL)', 0x3C: 'A'
        }
        return (InstructionType.INC, targets[opcode], None)

    # === DEC r ===
    if opcode in [0x05, 0x0D, 0x15, 0x1D, 0x25, 0x2D, 0x35, 0x3D]:
        targets = {
            0x05: 'B', 0x0D: 'C', 0x15: 'D', 0x1D: 'E',
            0x25: 'H', 0x2D: 'L', 0x35: '(HL)', 0x3D: 'A'
        }
        return (InstructionType.DEC, targets[opcode], None)

    # === LD r,n (immediate to register) ===
    if opcode in [0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x3E]:
        immediate = fetch_byte_func()
        targets = {
            0x06: 'B', 0x0E: 'C', 0x16: 'D', 0x1E: 'E',
            0x26: 'H', 0x2E: 'L', 0x3E: 'A'
        }
        return (InstructionType.LD, targets[opcode], immediate)

    # === LD (HL),n ===
    if opcode == 0x36:
        immediate = fetch_byte_func()
        return (InstructionType.LD, '(HL)', immediate)

    # === LD r,r (register to register) 0x40-0x7F ===
    if 0x40 <= opcode <= 0x7F:
        # Skip 0x76 which is HALT
        if opcode == 0x76:
            return (InstructionType.HALT, None, None)

        # Decode destination and source registers
        registers = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        dest_index = (opcode - 0x40) // 8
        src_index = (opcode - 0x40) % 8

        dest = registers[dest_index]
        src = registers[src_index]

        return (InstructionType.LD, dest, src)

    # === LD rr,nn (16-bit immediate) ===
    if opcode in [0x01, 0x11, 0x21, 0x31]:
        immediate = fetch_word_func()
        targets = {0x01: 'BC', 0x11: 'DE', 0x21: 'HL', 0x31: 'SP'}
        return (InstructionType.LD, targets[opcode], immediate)

    # === LD (BC/DE),A and LD A,(BC/DE) ===
    if opcode == 0x02:
        return (InstructionType.LD, '(BC)', 'A')
    if opcode == 0x12:
        return (InstructionType.LD, '(DE)', 'A')
    if opcode == 0x0A:
        return (InstructionType.LD, 'A', '(BC)')
    if opcode == 0x1A:
        return (InstructionType.LD, 'A', '(DE)')

    # === PUSH ===
    if opcode == 0xC5:
        return (InstructionType.PUSH, 'BC', None)
    if opcode == 0xD5:
        return (InstructionType.PUSH, 'DE', None)
    if opcode == 0xE5:
        return (InstructionType.PUSH, 'HL', None)
    if opcode == 0xF5:
        return (InstructionType.PUSH, 'AF', None)

    # === POP ===
    if opcode == 0xC1:
        return (InstructionType.POP, 'BC', None)
    if opcode == 0xD1:
        return (InstructionType.POP, 'DE', None)
    if opcode == 0xE1:
        return (InstructionType.POP, 'HL', None)
    if opcode == 0xF1:
        return (InstructionType.POP, 'AF', None)

    # === JP (Jump) ===
    if opcode == 0xC3:  # JP nn
        address = fetch_word_func()
        return (InstructionType.JP, address, None)
    if opcode == 0xC2:  # JP NZ,nn
        address = fetch_word_func()
        return (InstructionType.JP, address, 'NZ')
    if opcode == 0xCA:  # JP Z,nn
        address = fetch_word_func()
        return (InstructionType.JP, address, 'Z')
    if opcode == 0xD2:  # JP NC,nn
        address = fetch_word_func()
        return (InstructionType.JP, address, 'NC')
    if opcode == 0xDA:  # JP C,nn
        address = fetch_word_func()
        return (InstructionType.JP, address, 'C')
    if opcode == 0xE9:  # JP (HL)
        return (InstructionType.JP_HL, None, None)

    # === JR (Relative Jump) ===
    if opcode == 0x18:  # JR n
        offset = fetch_byte_func()
        return (InstructionType.JR, offset, None)
    if opcode == 0x20:  # JR NZ,n
        offset = fetch_byte_func()
        return (InstructionType.JR, offset, 'NZ')
    if opcode == 0x28:  # JR Z,n
        offset = fetch_byte_func()
        return (InstructionType.JR, offset, 'Z')
    if opcode == 0x30:  # JR NC,n
        offset = fetch_byte_func()
        return (InstructionType.JR, offset, 'NC')
    if opcode == 0x38:  # JR C,n
        offset = fetch_byte_func()
        return (InstructionType.JR, offset, 'C')

    # === CALL ===
    if opcode == 0xCD:  # CALL nn
        address = fetch_word_func()
        return (InstructionType.CALL, address, None)
    if opcode == 0xC4:  # CALL NZ,nn
        address = fetch_word_func()
        return (InstructionType.CALL, address, 'NZ')
    if opcode == 0xCC:  # CALL Z,nn
        address = fetch_word_func()
        return (InstructionType.CALL, address, 'Z')
    if opcode == 0xD4:  # CALL NC,nn
        address = fetch_word_func()
        return (InstructionType.CALL, address, 'NC')
    if opcode == 0xDC:  # CALL C,nn
        address = fetch_word_func()
        return (InstructionType.CALL, address, 'C')

    # === RET ===
    if opcode == 0xC9:  # RET
        return (InstructionType.RET, None, None)
    if opcode == 0xC0:  # RET NZ
        return (InstructionType.RET, 'NZ', None)
    if opcode == 0xC8:  # RET Z
        return (InstructionType.RET, 'Z', None)
    if opcode == 0xD0:  # RET NC
        return (InstructionType.RET, 'NC', None)
    if opcode == 0xD8:  # RET C
        return (InstructionType.RET, 'C', None)

    # === ROTATE/SHIFT ===
    if opcode == 0x07:  # RLCA
        return (InstructionType.RLCA, None, None)
    if opcode == 0x17:  # RLA
        return (InstructionType.RLA, None, None)
    if opcode == 0x0F:  # RRCA
        return (InstructionType.RRCA, None, None)
    if opcode == 0x1F:  # RRA
        return (InstructionType.RRA, None, None)

    # === 16-BIT ARITHMETIC ===
    if opcode == 0x03:  # INC BC
        return (InstructionType.INC_16, 'BC', None)
    if opcode == 0x13:  # INC DE
        return (InstructionType.INC_16, 'DE', None)
    if opcode == 0x23:  # INC HL
        return (InstructionType.INC_16, 'HL', None)
    if opcode == 0x33:  # INC SP
        return (InstructionType.INC_16, 'SP', None)

    if opcode == 0x0B:  # DEC BC
        return (InstructionType.DEC_16, 'BC', None)
    if opcode == 0x1B:  # DEC DE
        return (InstructionType.DEC_16, 'DE', None)
    if opcode == 0x2B:  # DEC HL
        return (InstructionType.DEC_16, 'HL', None)
    if opcode == 0x3B:  # DEC SP
        return (InstructionType.DEC_16, 'SP', None)

    if opcode == 0x09:  # ADD HL,BC
        return (InstructionType.ADD_HL, 'BC', None)
    if opcode == 0x19:  # ADD HL,DE
        return (InstructionType.ADD_HL, 'DE', None)
    if opcode == 0x29:  # ADD HL,HL
        return (InstructionType.ADD_HL, 'HL', None)
    if opcode == 0x39:  # ADD HL,SP
        return (InstructionType.ADD_HL, 'SP', None)

    # === MORE LD VARIANTS ===
    if opcode == 0x22:  # LDI (HL),A
        return (InstructionType.LDI, '(HL)', 'A')
    if opcode == 0x2A:  # LDI A,(HL)
        return (InstructionType.LDI, 'A', '(HL)')
    if opcode == 0x32:  # LDD (HL),A
        return (InstructionType.LDD, '(HL)', 'A')
    if opcode == 0x3A:  # LDD A,(HL)
        return (InstructionType.LDD, 'A', '(HL)')

    if opcode == 0xE0:  # LDH (n),A
        offset = fetch_byte_func()
        return (InstructionType.LDH, '(n)', offset)
    if opcode == 0xF0:  # LDH A,(n)
        offset = fetch_byte_func()
        return (InstructionType.LDH, offset, '(n)')
    if opcode == 0xE2:  # LDH (C),A
        return (InstructionType.LDH, '(C)', 'A')
    if opcode == 0xF2:  # LDH A,(C)
        return (InstructionType.LDH, 'A', '(C)')

    if opcode == 0xEA:  # LD (nn),A
        address = fetch_word_func()
        return (InstructionType.LD_ADDR, address, 'A')
    if opcode == 0xFA:  # LD A,(nn)
        address = fetch_word_func()
        return (InstructionType.LD_ADDR, 'A', address)

    # More special LD variants
    if opcode == 0x08:  # LD (nn),SP
        address = fetch_word_func()
        return (InstructionType.LD_NN_SP, address, None)

    if opcode == 0xF8:  # LD HL,SP+n
        offset = fetch_byte_func()
        return (InstructionType.LD_HL_SP_N, offset, None)

    if opcode == 0xF9:  # LD SP,HL
        return (InstructionType.LD_SP_HL, None, None)

    # === ADC (Add with carry) ===
    if 0x88 <= opcode <= 0x8F:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.ADC, targets[opcode - 0x88], None)

    if opcode == 0xCE:  # ADC A,n
        immediate = fetch_byte_func()
        return (InstructionType.ADC, 'IMMEDIATE', immediate)

    # === SBC (Subtract with carry) ===
    if 0x98 <= opcode <= 0x9F:
        targets = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.SBC, targets[opcode - 0x98], None)

    if opcode == 0xDE:  # SBC A,n
        immediate = fetch_byte_func()
        return (InstructionType.SBC, 'IMMEDIATE', immediate)

    # === RETI ===
    if opcode == 0xD9:  # RETI
        return (InstructionType.RETI, None, None)

    # === RST (Restart) ===
    if opcode in [0xC7, 0xCF, 0xD7, 0xDF, 0xE7, 0xEF, 0xF7, 0xFF]:
        # RST vectors: 00, 08, 10, 18, 20, 28, 30, 38
        vector_map = {
            0xC7: 0x00, 0xCF: 0x08, 0xD7: 0x10, 0xDF: 0x18,
            0xE7: 0x20, 0xEF: 0x28, 0xF7: 0x30, 0xFF: 0x38
        }
        return (InstructionType.RST, vector_map[opcode], None)

    # === CB PREFIX ===
    if opcode == 0xCB:
        # CB prefix - fetch next byte to determine actual instruction
        cb_opcode = fetch_byte_func()
        return decode_cb_instruction(cb_opcode)

    # Unknown opcode
    return (None, None, None)


def decode_cb_instruction(cb_opcode):
    """
    Decode CB-prefixed instructions

    CB opcodes follow a pattern:
    - 0x00-0x3F: Rotates and shifts (RLC, RRC, RL, RR, SLA, SRA, SWAP, SRL)
    - 0x40-0x7F: BIT b,r (test bit)
    - 0x80-0xBF: RES b,r (reset bit)
    - 0xC0-0xFF: SET b,r (set bit)

    For each group, the low 3 bits determine the register:
    000=B, 001=C, 010=D, 011=E, 100=H, 101=L, 110=(HL), 111=A
    """
    registers = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
    reg_index = cb_opcode & 0x07
    target = registers[reg_index]

    # Rotates and shifts (0x00-0x3F)
    if cb_opcode < 0x40:
        operation = (cb_opcode >> 3) & 0x07

        if operation == 0:  # RLC
            return (InstructionType.RLC, target, None)
        elif operation == 1:  # RRC
            return (InstructionType.RRC, target, None)
        elif operation == 2:  # RL
            return (InstructionType.RL, target, None)
        elif operation == 3:  # RR
            return (InstructionType.RR, target, None)
        elif operation == 4:  # SLA
            return (InstructionType.SLA, target, None)
        elif operation == 5:  # SRA
            return (InstructionType.SRA, target, None)
        elif operation == 6:  # SWAP
            return (InstructionType.SWAP, target, None)
        elif operation == 7:  # SRL
            return (InstructionType.SRL, target, None)

    # BIT b,r (0x40-0x7F)
    elif cb_opcode < 0x80:
        bit = (cb_opcode >> 3) & 0x07
        return (InstructionType.BIT, target, bit)

    # RES b,r (0x80-0xBF)
    elif cb_opcode < 0xC0:
        bit = (cb_opcode >> 3) & 0x07
        return (InstructionType.RES, target, bit)

    # SET b,r (0xC0-0xFF)
    else:
        bit = (cb_opcode >> 3) & 0x07
        return (InstructionType.SET, target, bit)

    return (None, None, None)
