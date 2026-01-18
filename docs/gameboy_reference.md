# Game Boy Hardware Reference

Quick reference for Game Boy hardware specifications and emulation implementation.

## Memory Map
```
0x0000-0x3FFF  ROM Bank 0 (fixed)
0x4000-0x7FFF  ROM Bank 1-N (switchable)
0x8000-0x9FFF  VRAM
0xA000-0xBFFF  External RAM
0xC000-0xDFFF  Work RAM
0xFE00-0xFE9F  OAM (Sprites)
0xFF00-0xFF7F  I/O Registers
0xFF80-0xFFFE  High RAM
0xFFFF         IE Register
```

## Key I/O Registers
```
0xFF00  P1     Joypad
0xFF04  DIV    Divider (16384 Hz)
0xFF05  TIMA   Timer counter
0xFF06  TMA    Timer modulo
0xFF07  TAC    Timer control
0xFF0F  IF     Interrupt flags
0xFF40  LCDC   LCD control
0xFF41  STAT   LCD status
0xFF44  LY     LCD scanline
0xFFFF  IE     Interrupt enable
```

## CPU (Sharp LR35902)
- Modified Z80 with custom instruction set
- 8-bit data, 16-bit address bus
- Registers: A, B, C, D, E, H, L, SP, PC, F (flags)
- 256 base + 256 CB-prefixed opcodes
- Timing: 1 M-cycle = 4 T-cycles

### Critical Details
- F register lower 4 bits always 0
- Instruction timings in opcode table are T-cycles
- HALT continues timer/interrupt processing

## Timer System
Components:
- DIV (0xFF04): Increments every 256 T-cycles
- TIMA (0xFF05): Increments based on TAC frequency
- TMA (0xFF06): Reload value on TIMA overflow
- TAC (0xFF07): Enable + frequency (00=4096Hz, 01=262144Hz, 10=65536Hz, 11=16384Hz)

### Critical Behaviors
- Writing DIV resets internal counter
- TIMA overflow has 4-cycle delay
- TAC writes can trigger edge detection

## Interrupt System
Priority (high to low):
1. VBlank (0x0040)
2. LCD STAT (0x0048)
3. Timer (0x0050)
4. Serial (0x0058)
5. Joypad (0x0060)

### Instructions
- EI: Enable interrupts with 1-instruction delay
- DI: Disable interrupts immediately
- RETI: Return and enable interrupts immediately

## PPU (Graphics)
- Screen: 160x144 pixels, 4 colors
- Modes: OAM Search (80T) → Transfer (168-291T) → HBlank → VBlank
- One scanline: 456 T-cycles
- Full frame: 154 scanlines (~59.7 Hz)

## Joypad
P1 Register (0xFF00):
- Bit 5: Select buttons (0=selected)
- Bit 4: Select d-pad (0=selected)
- Bits 3-0: Button states (0=pressed, inverted logic)

## Common Implementation Gotchas
1. T-cycles vs M-cycles: Always verify which unit code expects
2. F register: Lower 4 bits must be masked to 0
3. HALT: Must continue stepping for timers
4. EI delay: 1 instruction before IME=true
5. RETI: No delay, sets IME=true immediately
6. Joypad: Inverted logic (0=pressed)

## Essential Resources
- [Pan Docs](https://gbdev.io/pandocs/) - Complete technical reference
- [GBEDG](https://github.com/Hacktix/GBEDG) - Timing edge cases
- [Opcode Table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html)
- [Blargg Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/)
- [r/EmuDev](https://www.reddit.com/r/EmuDev/) - Community support

## Reference Emulators
- BGB - Windows debugger
- SameBoy - Highly accurate
- Gambatte - Cycle-accurate
