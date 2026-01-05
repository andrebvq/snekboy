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
    # Add more as needed


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

    # === LD A,r (register to A) ===
    if 0x78 <= opcode <= 0x7F:
        sources = ['B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A']
        return (InstructionType.LD, 'A', sources[opcode - 0x78])

    # === LD rr,nn (16-bit immediate) ===
    if opcode in [0x01, 0x11, 0x21, 0x31]:
        immediate = fetch_word_func()
        targets = {0x01: 'BC', 0x11: 'DE', 0x21: 'HL', 0x31: 'SP'}
        return (InstructionType.LD, targets[opcode], immediate)

    # === LD (BC/DE/HL),A ===
    if opcode == 0x02:
        return (InstructionType.LD, '(BC)', 'A')
    if opcode == 0x12:
        return (InstructionType.LD, '(DE)', 'A')
    if opcode == 0x77:
        return (InstructionType.LD, '(HL)', 'A')

    # === LD A,(BC/DE/HL) ===
    if opcode == 0x0A:
        return (InstructionType.LD, 'A', '(BC)')
    if opcode == 0x1A:
        return (InstructionType.LD, 'A', '(DE)')
    if opcode == 0x7E:
        return (InstructionType.LD, 'A', '(HL)')

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

    # Unknown opcode
    return (None, None, None)
