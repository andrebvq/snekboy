# Game Boy Hardware Reference

Quick reference for Game Boy hardware specifications and emulation implementation.

## Memory Map
```
0x0000-0x3FFF  ROM bank 0 (writes go to the mapper)
0x4000-0x7FFF  ROM bank 1-N (switchable)
0x8000-0x9FFF  VRAM (CPU locked out in mode 3)
0xA000-0xBFFF  Cartridge RAM / MBC3 clock
0xC000-0xDFFF  Work RAM
0xE000-0xFDFF  Echo of 0xC000-0xDDFF
0xFE00-0xFE9F  OAM, sprite attributes (locked in modes 2-3 and during DMA)
0xFEA0-0xFEFF  Unusable
0xFF00-0xFF7F  I/O registers (unused bits read 1)
0xFF80-0xFFFE  High RAM (usable during OAM DMA)
0xFFFF         IE register
```

## Key I/O Registers
```
0xFF00  P1     Joypad (group select + inverted button bits)
0xFF01  SB     Serial data
0xFF02  SC     Serial control (bit 7 start, bit 0 internal clock)
0xFF04  DIV    Divider: upper byte of the 16-bit system counter
0xFF05  TIMA   Timer counter
0xFF06  TMA    Timer modulo (reload value)
0xFF07  TAC    Timer control (bit 2 enable, bits 0-1 rate)
0xFF0F  IF     Interrupt flags
0xFF40  LCDC   LCD control
0xFF41  STAT   LCD status: interrupt sources, LY=LYC flag, mode
0xFF42  SCY    Background scroll Y
0xFF43  SCX    Background scroll X
0xFF44  LY     Current line (read-only)
0xFF45  LYC    LY compare
0xFF46  DMA    OAM DMA source page
0xFF47  BGP    Background palette
0xFF48  OBP0   Sprite palette 0
0xFF49  OBP1   Sprite palette 1
0xFF4A  WY     Window Y
0xFF4B  WX     Window X + 7
0xFF50  BOOT   Boot ROM disable
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
- TIMA ticks on a falling edge of one system-counter bit, so writes to DIV or TAC can tick it
- TIMA overflow: TIMA reads 0 for 4 cycles, then reloads from TMA and requests the interrupt

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
- Modes: OAM search (80 dots) → pixel transfer (172-289 dots, longer with scroll, window and sprites) → HBlank → VBlank (lines 144-153)
- STAT interrupt fires on the rising edge of the ORed sources, not once per source
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
- [mooneye-test-suite](https://github.com/Gekkio/mooneye-test-suite)
- [Blargg Test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/)
- [r/EmuDev](https://www.reddit.com/r/EmuDev/) - Community support

## Reference Emulators
- BGB - Windows debugger
- SameBoy - Highly accurate
- Gambatte - Cycle-accurate
