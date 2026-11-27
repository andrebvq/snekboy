# SnekBoy

SnekBoy is an original Game Boy (DMG) emulator written in pure Python, with pygame for the display and input. It models the Sharp LR35902 CPU, the timer, the interrupts, the picture processing unit (PPU), OAM DMA, the serial port and the common cartridge mappers, timed to the individual memory access. It plays most of the commercial games tested, and every DMG-specific mooneye acceptance test passes. Audio is not emulated.

<img width="462" height="176" alt="SnekBoy" src="https://github.com/user-attachments/assets/cd4fc784-ecff-4798-a9d1-94cecba4cec5" />

The project is a learning exercise in hardware emulation: it aims to be correct first and readable second, and then as fast as pure Python allows. Its full development history, including what was wrong at each release, how it was found and why each fix is correct, is written up in the [Developer's Logbook](docs/developer_logbook.html).

<img width="306" height="276" alt="Tetris running in SnekBoy" src="https://github.com/user-attachments/assets/95abb3ab-3b99-4bba-a482-7d5468d314d6" />

## Status at a glance

| Area | State |
|---|---|
| CPU | All 245 defined opcodes and 256 CB opcodes; HALT bug, EI delay and interrupt dispatch as on hardware; the 11 undefined opcodes lock the CPU |
| Timing | Each memory access happens on its own M-cycle; the timer, PPU and DMA catch up before any access that can observe them |
| Graphics | Background, window and sprites; pixel-exact on dmg-acid2; mode-3 length varies with scroll, window and sprites |
| Cartridges | ROM only, MBC1, MBC2, MBC3 (with real-time clock), MBC5; battery saves |
| Other hardware | Timer with all edge cases tested by mooneye; OAM DMA; serial port timing (no link partner); joypad |
| Not implemented | Audio (APU), the DMG OAM corruption bug, MBC1 multicart, Game Boy Color |
| Speed | 5 of 11 tested games reach full speed (60 fps) in gameplay on Python 3.10; the rest run at 51-55 fps |

## Quick start

Requirements: Python 3.9 or newer (developed on 3.10) and pygame 2.

```bash
git clone https://github.com/andrebvq/snekboy.git
cd snekboy
pip install pygame
python -m src.emulator path/to/game.gb --no-trace
```

Without `--no-trace`, the emulator also writes a debug trace to `tracing/tracing.txt` (see [Debugging tools](#debugging-tools)). Run without a ROM, it shows a test pattern. Battery-backed games save to `<rom>.sav`, with the MBC3 clock in `<rom>.rtc`, when you quit with ESC or by closing the window.

### Controls

| Game Boy | Key | | Game Boy | Key |
|---|---|---|---|---|
| A | A | | Up | I |
| B | S | | Down | K |
| Start | Z | | Left | J |
| Select | X | | Right | L |
| Switch palette (green, classic, grey) | P | | Quit | ESC |

## Project structure

```
snekboy/
├── src/
│   ├── emulator.py           # entry point: window, frame loop, saves, tracing hooks
│   ├── cpu.py                # CPU core: dispatch, interrupts, timer, per-access timing, frame loop
│   ├── cpu_decoder.py        # opcode decoder (used once at start-up to build the dispatch table)
│   ├── instructions_impl.py  # generic instruction handlers
│   ├── fast_ops.py           # dedicated handlers for frequent opcodes, generated from templates
│   ├── opcodes.py            # opcode table: mnemonics, lengths, T-cycles, flags
│   ├── registers.py          # registers and the flag byte
│   ├── memory.py             # memory map, I/O registers, OAM DMA, serial, access locks
│   ├── cartridge.py          # ROM header, MBC1/2/3/5 mappers, real-time clock, battery saves
│   ├── ppu.py                # PPU: modes, STAT line, background, window, sprites
│   ├── joypad.py             # P1 register and joypad interrupt
│   ├── display.py            # pygame window, palettes, keyboard
│   ├── tracer.py             # trace file writer
│   ├── gameboy_doctor.py     # Gameboy Doctor log output
│   ├── version.py            # single source of the version number
│   └── utils.py
├── tests/                    # pytest unit tests and a Blargg ROM runner (see tests/README.md)
├── test_roms/                # Blargg's test ROMs with their sources
├── tools/disassemble_rom.py  # prints the first instructions at a ROM's entry point
├── docs/                     # documentation (see below)
├── CHANGELOG.md
└── pyproject.toml
```

### How a frame runs

The window loop asks the CPU to run 70,224 T-cycles, one frame, with `cpu.run_until_cycle()`. That loop runs instructions through a dispatch table built at start-up. The timer and PPU are brought up to date only when something could observe them: an I/O or video-memory access, a point where an interrupt could be raised, or the end of the frame. A halted CPU skips ahead to the next timer or PPU event. The PPU draws each line into a buffer, and the frame is shown and paced to 60 fps. [docs/architecture.md](docs/architecture.md) describes each part.

## Accuracy

| Test suite | Passing | What still fails, and why |
|---|---|---|
| Blargg `cpu_instrs` (combined and 11 singles) | 12 / 12 | — |
| Blargg `instr_timing`, `mem_timing`, `mem_timing-2`, `halt_bug` | 9 / 9 | — |
| Blargg `interrupt_time` | 0 / 1 | Needs Game Boy Color double speed |
| Blargg `oam_bug` | 3 / 9 | The DMG OAM corruption bug is not emulated |
| mooneye-test-suite (DMG-relevant set) | 93 / 111 | Every failure targets another model (DMG0, MGB, SGB, CGB, AGB) or the MBC1 multicart |
| dmg-acid2 | exact | 0 wrong pixels against the reference image |
| Unit tests (pytest) | 75 / 75 | — |

Blargg's sound tests are excluded, since there is no APU. The mooneye ROMs are not included in this repository.

### Games tested

These were measured on Python 3.10 over frames 700-1200, after getting into the game, with the frame cap removed. Full speed is 60 fps; the window caps at 60.

| Game | Mapper | Gameplay fps | | Game | Mapper | Gameplay fps |
|---|---|---|---|---|---|---|
| Final Fantasy Legend | MBC2 + battery | 118 | | Wario Land II | MBC5 + battery | 55 |
| Dr. Mario | ROM only | 99 | | Alleyway | ROM only | 54 |
| Super Mario Land | MBC1 | 83 | | Pokémon Gold | MBC3 + clock + battery | 54 |
| Super Mario Land 2 | MBC1 + battery | 82 | | Pokémon Red | MBC3 + battery | 52 |
| Zelda: Link's Awakening DX (Japan) | MBC5 + battery | 66 | | Kirby's Dream Land | MBC1 | 51 |
| | | | | Tetris | ROM only | 51 |

All 11 play correctly as far as they were tested by hand. Games that wait for the next frame with `HALT` run fastest. Games that busy-wait in a loop reading the LCD status cost the most per emulated frame. On v0.9, Python 3.11 ran SnekBoy about 1.9× faster than 3.10 (Tetris 36 → 72 fps over the intro); it has not yet been measured on the current version.

## Testing

```bash
pip install pytest
python -m pytest tests            # 75 unit tests, about a minute
python tests/run_all_test_roms.py # Blargg ROMs from test_roms/, reported through the serial port
```

The unit tests cover each component. Several are differential: the optimised paths are run against the generic code on random states, and each such test was checked by planting a bug and confirming that it fails. [tests/README.md](tests/README.md) lists what each file covers.

## Debugging tools

| Tool | How to use | What it gives |
|---|---|---|
| Trace file | on by default; `--no-trace` turns it off | `tracing/tracing.txt` with LCD on/off writes, sampled VRAM writes and LY reads, DMA starts and a state line each second ([docs/tracing.md](docs/tracing.md)) |
| Gameboy Doctor | `GAMEBOY_DOCTOR=1` | a CPU state log in the format of [Gameboy Doctor](https://github.com/robert/gameboy-doctor), for comparing against reference logs |
| Disassembler | `python tools/disassemble_rom.py rom.gb` | the first 50 instructions from 0x0100 |

## Documentation

| Document | Contents |
|---|---|
| [Developer's Logbook](docs/developer_logbook.html) | Every release from 0.1 to 0.9.2: the state of the emulator, the problems found and how, each fix with the hardware behaviour behind it, and how it was verified. Open it in a browser. |
| [docs/architecture.md](docs/architecture.md) | How the emulator is built: components, timing model, frame loop, optimisations |
| [docs/gameboy_reference.md](docs/gameboy_reference.md) | Compact Game Boy hardware reference: memory map, registers, timings |
| [docs/opcode_reference.md](docs/opcode_reference.md) | Instruction groups with cycles and flag effects |
| [docs/tracing.md](docs/tracing.md) | The trace file format |
| [tests/README.md](tests/README.md) | The test suite |
| [CHANGELOG.md](CHANGELOG.md) | All changes, release by release |

## Versioning

**Current version: 0.9.2 (Frame loop).** Each frame now runs in one inline loop for the common case: the CPU is running, code is in ROM or RAM, and no DMA or interrupt is pending. Anything else goes through the general `step()` path. Behaviour is unchanged (every executed instruction of 12 games matches 0.9.1). Gameplay speed of the slower games rose 6-33%, for example Kirby 39 → 51 fps and Zelda DX 53 → 66 fps.

Releases are numbered 0.x while features and accuracy are being built. From 0.9 onwards, performance and polish releases are numbered 0.9.1, 0.9.2 and so on until 1.0. Each release is a tagged merge of one pull request. [CHANGELOG.md](CHANGELOG.md) lists every release, and the [Developer's Logbook](docs/developer_logbook.html) explains each one in depth.

## References

| Resource | Used for |
|---|---|
| [Pan Docs](https://gbdev.io/pandocs/) | The main hardware reference |
| [GBEDG](https://github.com/Hacktix/GBEDG) | Timer, PPU and edge-case details |
| [Opcode table](https://www.pastraiser.com/cpu/gameboy/gameboy_opcodes.html) | Instruction lengths, cycles and flags |
| [Blargg's test ROMs](https://gbdev.gg8.se/files/roms/blargg-gb-tests/) (Shay Green) | CPU, timing and HALT tests |
| [mooneye-test-suite](https://github.com/Gekkio/mooneye-test-suite) (Joonas Javanainen) | Hardware edge cases per model |
| [dmg-acid2](https://github.com/mattcurrie/dmg-acid2) (Matt Currie) | PPU rendering test |
| [Gameboy Doctor](https://github.com/robert/gameboy-doctor) (Robert Heaton) | CPU log comparison |
| [SameBoy](https://sameboy.github.io/), [Gambatte](https://github.com/sinamas/gambatte), [BGB](https://bgb.bircd.org/) | Reference emulators for behaviour questions |
| [r/EmuDev](https://www.reddit.com/r/EmuDev/), [gbdev.io](https://gbdev.io/) | Community |

Thanks to the authors of these test ROMs and documents. This kind of project is not possible without them.

## License

MIT. See [LICENSE](LICENSE).
