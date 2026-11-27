# Instruction reference

The Sharp SM83 (LR35902) instruction set by group, with lengths, T-cycles and flag effects. Cycles are T-cycles (4 per M-cycle). Where two values are given, they are taken / not taken. `r` is one of B, C, D, E, H, L, A; `(HL)` is the byte at address HL; `n` is an immediate byte, `nn` an immediate word, `e` a signed byte.

In SnekBoy, these values come from `src/opcodes.py`. The dispatch table is built from the decoder at start-up, and the frequent instructions have dedicated handlers in `src/fast_ops.py`.

## Flags

F holds Z (bit 7, zero), N (bit 6, subtract), H (bit 5, half carry: a carry out of bit 3, or bit 11 for 16-bit adds) and C (bit 4, carry). The low 4 bits always read 0, which `POP AF` must respect.

In the tables, `Z` means set from the result, `0`/`1` means always cleared or set, and `-` means unchanged.

## 8-bit loads

| Instruction | Bytes | Cycles | Flags |
|---|---|---|---|
| LD r,r' | 1 | 4 | - |
| LD r,n | 2 | 8 | - |
| LD r,(HL) / LD (HL),r | 1 | 8 | - |
| LD (HL),n | 2 | 12 | - |
| LD A,(BC) / (DE); LD (BC),A / (DE),A | 1 | 8 | - |
| LD A,(HL+) / (HL-); LD (HL+),A / (HL-),A | 1 | 8 | - |
| LD A,(nn) / LD (nn),A | 3 | 16 | - |
| LDH A,(n) / LDH (n),A (address 0xFF00+n) | 2 | 12 | - |
| LDH A,(C) / LDH (C),A | 1 | 8 | - |

## 16-bit loads and stack

| Instruction | Bytes | Cycles | Flags |
|---|---|---|---|
| LD rr,nn (BC, DE, HL, SP) | 3 | 12 | - |
| LD (nn),SP | 3 | 20 | - |
| LD SP,HL | 1 | 8 | - |
| LD HL,SP+e | 2 | 12 | 0 0 H C (from the low byte) |
| PUSH rr | 1 | 16 | - |
| POP rr | 1 | 12 | - (POP AF loads F) |

## 8-bit arithmetic and logic

Each takes the source as `r` (4 cycles, 1 byte), `(HL)` (8, 1) or `n` (8, 2).

| Instruction | Z | N | H | C |
|---|---|---|---|---|
| ADD A,x / ADC A,x | Z | 0 | H | C |
| SUB x / SBC A,x | Z | 1 | H | C |
| AND x | Z | 0 | 1 | 0 |
| XOR x / OR x | Z | 0 | 0 | 0 |
| CP x (SUB without storing) | Z | 1 | H | C |
| INC r / DEC r (4); INC (HL) / DEC (HL) (12) | Z | 0 / 1 | H | - |
| DAA | Z | - | 0 | C |
| CPL | - | 1 | 1 | - |
| SCF / CCF | - | 0 | 0 | 1 / inverted |

## 16-bit arithmetic

| Instruction | Bytes | Cycles | Flags |
|---|---|---|---|
| ADD HL,rr | 1 | 8 | - 0 H C (H from bit 11) |
| ADD SP,e | 2 | 16 | 0 0 H C (from the low byte) |
| INC rr / DEC rr | 1 | 8 | - |

## Rotates, shifts and bit operations

| Instruction | Bytes | Cycles | Flags |
|---|---|---|---|
| RLCA / RLA / RRCA / RRA | 1 | 4 | 0 0 0 C (Z always 0) |
| CB: RLC, RL, RRC, RR, SLA, SRA, SRL r | 2 | 8 | Z 0 0 C |
| CB: SWAP r | 2 | 8 | Z 0 0 0 |
| CB: BIT b,r | 2 | 8 | Z 0 1 - |
| CB: SET b,r / RES b,r | 2 | 8 | - |
| CB: any of the above on (HL) | 2 | 16 (BIT: 12) | as above |

## Jumps, calls and returns

| Instruction | Bytes | Cycles |
|---|---|---|
| JP nn | 3 | 16 |
| JP cc,nn (NZ, Z, NC, C) | 3 | 16 / 12 |
| JP HL | 1 | 4 |
| JR e | 2 | 12 |
| JR cc,e | 2 | 12 / 8 |
| CALL nn | 3 | 24 |
| CALL cc,nn | 3 | 24 / 12 |
| RET | 1 | 16 |
| RET cc | 1 | 20 / 8 |
| RETI (RET, then IME = 1 at once) | 1 | 16 |
| RST n (0x00, 0x08 … 0x38) | 1 | 16 |

None of these change flags.

## Control

| Instruction | Bytes | Cycles | Behaviour |
|---|---|---|---|
| NOP | 1 | 4 | |
| DI | 1 | 4 | IME = 0 at once; also cancels a pending EI |
| EI | 1 | 4 | IME = 1 after the next instruction |
| HALT | 1 | 4 | Waits for IE & IF ≠ 0. With IME = 0 and an interrupt already pending, it doesn't halt and the next byte is read twice (the HALT bug) |
| STOP | 2 | 4 | Resets DIV; the CPU and timer stop until a selected joypad line goes low |
| D3 DB DD E3 E4 EB EC ED F4 FC FD | 1 | — | Undefined: the CPU locks up for good |

An interrupt dispatch takes 20 cycles: 2 internal M-cycles, 2 pushes of PC, and 1 to set PC to the vector. The vectors are 0x40 VBlank, 0x48 STAT, 0x50 timer, 0x58 serial and 0x60 joypad, in that priority order.

## Memory-access timing

Each access happens on its own M-cycle, in this order: the opcode fetch first, then the operand bytes, then the data read or write. Internal delays sit where the hardware has them. For example, `PUSH` spends one internal M-cycle before its two writes, and `RET cc` spends one to evaluate the condition. Blargg's `mem_timing` tests check exactly these positions for reads and writes of I/O registers. SnekBoy passes them because the timer catches up to each access's own cycle (see [architecture.md](architecture.md#per-access-timing)).

For full per-opcode detail, see the [gbdev opcode table](https://gbdev.io/gb-opcodes/optables/) and [Pan Docs](https://gbdev.io/pandocs/CPU_Instruction_Set.html).
