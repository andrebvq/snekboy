"""Memory bank controllers, checked against Pan Docs "MBCs"."""

from src.cartridge import MBC3, make_cartridge
from src.memory import Memory


def _rom(kind, banks, ram_code=0x00):
    """ROM where the first byte of every 16 KB bank holds its bank number."""
    rom = bytearray(banks * 0x4000)
    for b in range(banks):
        rom[b * 0x4000] = b & 0xFF
        rom[b * 0x4000 + 1] = b >> 8
    rom[0x147], rom[0x149] = kind, ram_code
    return bytes(rom)


def _mem(rom):
    mem = Memory()
    mem.load_rom(rom)
    mem.write_byte(0xFF50, 0x01)          # unmap the boot ROM, as at the end of boot
    return mem


def _bank_at_4000(mem):
    return mem.read_byte(0x4000) | (mem.read_byte(0x4001) << 8)


def test_header_selects_mapper():
    assert make_cartridge(_rom(0x00, 2)).name == "ROM only"
    assert make_cartridge(_rom(0x03, 4, 0x03)).name == "MBC1"
    assert make_cartridge(_rom(0x06, 4)).name == "MBC2"
    assert make_cartridge(_rom(0x10, 4, 0x03)).name == "MBC3"
    assert make_cartridge(_rom(0x1B, 4, 0x03)).name == "MBC5"


def test_mbc1_rom_banking():
    mem = _mem(_rom(0x01, 128))           # 2 MB
    assert _bank_at_4000(mem) == 1
    mem.write_byte(0x2000, 0x05)
    assert _bank_at_4000(mem) == 5
    mem.write_byte(0x2000, 0x00)          # 0 selects bank 1
    assert _bank_at_4000(mem) == 1
    mem.write_byte(0x2000, 0x01)
    mem.write_byte(0x4000, 0x02)          # upper bits -> bank 0x41
    assert _bank_at_4000(mem) == 0x41
    assert mem.read_byte(0x0000) == 0     # mode 0: bank 0 fixed
    mem.write_byte(0x6000, 0x01)          # mode 1: upper bits also move 0x0000
    assert mem.read_byte(0x0000) == 0x40


def test_mbc1_bank_number_wraps_to_rom_size():
    mem = _mem(_rom(0x01, 4))             # 64 KB = 4 banks
    mem.write_byte(0x2000, 0x07)
    assert _bank_at_4000(mem) == 3


def test_mbc1_ram_enable_and_banks():
    mem = _mem(_rom(0x03, 4, 0x03))       # 32 KB RAM
    mem.write_byte(0xA000, 0x12)
    assert mem.read_byte(0xA000) == 0xFF  # disabled: writes ignored, reads 0xFF
    mem.write_byte(0x0000, 0x0A)
    mem.write_byte(0xA000, 0x12)
    assert mem.read_byte(0xA000) == 0x12
    mem.write_byte(0x6000, 0x01)
    mem.write_byte(0x4000, 0x02)          # RAM bank 2
    assert mem.read_byte(0xA000) == 0x00   # fresh bank is empty
    mem.write_byte(0xA000, 0x34)
    mem.write_byte(0x4000, 0x00)
    assert mem.read_byte(0xA000) == 0x12
    mem.write_byte(0x0000, 0x00)
    assert mem.read_byte(0xA000) == 0xFF


def test_mbc2_rom_bank_and_nibble_ram():
    mem = _mem(_rom(0x06, 16))
    mem.write_byte(0x2100, 0x03)          # address bit 8 set: ROM bank
    assert _bank_at_4000(mem) == 3
    mem.write_byte(0x0000, 0x0A)          # bit 8 clear: RAM enable
    mem.write_byte(0xA005, 0xAB)
    assert mem.read_byte(0xA005) == 0xFB  # only 4 bits stored, upper read as 1
    assert mem.read_byte(0xA205) == 0xFB  # 512 bytes, mirrored


def test_mbc3_rom_bank_7_bits():
    mem = _mem(_rom(0x13, 128, 0x03))
    mem.write_byte(0x2000, 0x45)
    assert _bank_at_4000(mem) == 0x45
    mem.write_byte(0x2000, 0x00)
    assert _bank_at_4000(mem) == 1


def test_mbc3_rtc_latch():
    now = [1000.0]
    cart = MBC3(_rom(0x10, 4, 0x03), 0x8000, battery=True, rtc=True, clock=lambda: now[0])
    cart.write_rom(0x0000, 0x0A)
    now[0] += 3 * 86400 + 2 * 3600 + 5 * 60 + 7
    cart.write_rom(0x6000, 0x00)
    cart.write_rom(0x6000, 0x01)          # latch
    regs = []
    for reg in range(0x08, 0x0D):
        cart.write_rom(0x4000, reg)
        regs.append(cart.read_ram(0xA000))
    assert regs == [7, 5, 2, 3, 0]
    now[0] += 60
    cart.write_rom(0x4000, 0x08)
    assert cart.read_ram(0xA000) == 7     # latched value doesn't move


def test_mbc5_bank_zero_and_ninth_bit():
    mem = _mem(_rom(0x19, 512))           # 8 MB
    mem.write_byte(0x2000, 0x00)
    assert _bank_at_4000(mem) == 0        # MBC5 allows bank 0 here
    mem.write_byte(0x2000, 0x23)
    mem.write_byte(0x3000, 0x01)
    assert _bank_at_4000(mem) == 0x123


def test_battery_ram_round_trip(tmp_path):
    rom = _rom(0x03, 4, 0x02)
    mem = _mem(rom)
    mem.write_byte(0x0000, 0x0A)
    mem.write_byte(0xA123, 0x5A)
    path = str(tmp_path / "game.sav")
    mem.cartridge.save(path)
    mem2 = _mem(rom)
    mem2.cartridge.load(path)
    mem2.write_byte(0x0000, 0x0A)
    assert mem2.read_byte(0xA123) == 0x5A
