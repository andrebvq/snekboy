"""Memory-map behaviour checked against DMG hardware (Pan Docs, "Memory Map")."""

from src.cpu import CPU


def _cpu_with_rom(size=0x8000, fill=0x00):
    cpu = CPU()
    cpu.memory.load_rom(bytes([fill]) * size)
    cpu.simulate_boot()
    return cpu


def test_rom_writes_are_ignored():
    cpu = _cpu_with_rom(fill=0x20)
    mem = cpu.memory
    # Tetris writes 0x01 to 0x2000 (an MBC bank-select write); ROM must not change.
    mem.write_byte(0x2000, 0x01)
    mem.write_byte(0x0000, 0xFF)
    mem.write_byte(0x7FFF, 0xFF)
    assert mem.read_byte(0x2000) == 0x20
    assert mem.read_byte(0x0000) == 0x20
    assert mem.read_byte(0x7FFF) == 0x20


def test_echo_ram_writes_reach_wram():
    cpu = _cpu_with_rom()
    mem = cpu.memory
    mem.write_byte(0xFDFF, 0x80)          # echo of 0xDDFF
    assert mem.read_byte(0xDDFF) == 0x80
    mem.write_byte(0xC123, 0x42)
    assert mem.read_byte(0xE123) == 0x42


def test_unusable_area_reads_zero_and_ignores_writes():
    cpu = _cpu_with_rom()
    mem = cpu.memory
    cpu.memory._data[0xFF40] = 0x00       # LCD off, so OAM is never locked
    mem.write_byte(0xFEF9, 0xFC)
    assert mem.read_byte(0xFEF9) == 0x00
    assert mem.read_byte(0xFEA0) == 0x00


def test_io_unused_bits_read_as_one():
    cpu = _cpu_with_rom()
    mem = cpu.memory
    mem.write_byte(0xFF0F, 0x00)
    assert mem.read_byte(0xFF0F) == 0xE0      # IF: bits 5-7 unused
    mem.write_byte(0xFF07, 0x00)
    assert mem.read_byte(0xFF07) == 0xF8      # TAC: bits 3-7 unused
    assert mem.read_byte(0xFF41) & 0x80       # STAT: bit 7 unused
    assert mem.read_byte(0xFF4D) == 0xFF      # KEY1 does not exist on DMG
    assert mem.read_byte(0xFF03) == 0xFF      # unmapped
    assert mem.read_byte(0xFF7F) == 0xFF      # unmapped
    mem.write_byte(0xFFFF, 0x00)
    assert mem.read_byte(0xFFFF) == 0x00      # IE keeps all 8 bits


def test_ff50_unmaps_boot_rom_on_bit0():
    from src.memory import Memory
    mem = Memory()
    rom = bytearray(0x8000)
    rom[0x0010] = 0xAB
    mem.load_rom(bytes(rom))
    assert mem.boot_rom_enabled
    mem.write_byte(0xFF50, 0xFF)              # MGB boot ROM writes 0xFF; only bit 0 matters
    assert not mem.boot_rom_enabled
    assert mem.read_byte(0x0010) == 0xAB
    assert mem.read_byte(0xFF50) == 0xFF


def test_post_boot_p1_and_div():
    cpu = _cpu_with_rom()
    mem = cpu.memory
    assert mem.read_byte(0xFF00) == 0xCF
    assert mem.read_byte(0xFF04) == 0xAB
    for _ in range(4):
        cpu.step()                            # 4 NOPs = 16 T-cycles
    assert mem.read_byte(0xFF04) == 0xAB      # DIV keeps counting from 0xAB, not 0x00
