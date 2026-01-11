"""
Real-time execution tracer for debugging
Logs to tracing.txt
"""

import os

class Tracer:
    """Traces emulator execution to file"""

    def __init__(self, filename="tracing.txt", enabled=True):
        self.filename = filename
        self.enabled = enabled
        self.file = None

        if self.enabled:
            try:
                # Create parent directories if they don't exist
                parent_dir = os.path.dirname(filename)
                if parent_dir:
                    print(f"[TRACER] Creating directory: {parent_dir}")
                    os.makedirs(parent_dir, exist_ok=True)

                # Clear existing file
                print(f"[TRACER] Opening file: {filename}")
                self.file = open(filename, 'w', encoding='utf-8')
                print(f"[TRACER] File opened successfully: {self.file}")
                self.file.write("="*80 + "\n")
                self.file.write("EMULATOR EXECUTION TRACE\n")
                self.file.write("="*80 + "\n\n")
                self.file.flush()
                print(f"[TRACER] Initial header written and flushed")
            except Exception as e:
                print(f"[TRACER ERROR] Failed to create trace file: {e}")
                import traceback
                traceback.print_exc()
                self.enabled = False

    def log(self, message):
        """Log a message"""
        if self.enabled and self.file:
            self.file.write(message + "\n")
            self.file.flush()

    def log_ly_read(self, cycle, pc, ly_value):
        """Log LY register read"""
        if self.enabled:
            self.log(f"[{cycle:10d}] PC=0x{pc:04X} READ LY: {ly_value}")

    def log_lcdc_write(self, cycle, pc, value):
        """Log LCDC register write"""
        if self.enabled:
            lcd_on = "ON" if (value & 0x80) else "OFF"
            self.log(f"[{cycle:10d}] PC=0x{pc:04X} WRITE LCDC: 0x{value:02X} (LCD {lcd_on})")

    def log_vram_write(self, cycle, pc, address, value):
        """Log VRAM write"""
        if self.enabled:
            self.log(f"[{cycle:10d}] PC=0x{pc:04X} WRITE VRAM [0x{address:04X}] = 0x{value:02X}")

    def log_dma_trigger(self, cycle, pc, source_page):
        """Log DMA transfer"""
        if self.enabled:
            self.log(f"[{cycle:10d}] PC=0x{pc:04X} DMA TRANSFER from 0x{source_page:02X}00")

    def log_vblank(self, cycle):
        """Log VBlank interrupt"""
        if self.enabled:
            self.log(f"[{cycle:10d}] *** VBLANK INTERRUPT ***")

    def log_state(self, cycle, ly, lcdc, pc):
        """Log current state"""
        if self.enabled:
            lcd_status = "ON" if (lcdc & 0x80) else "OFF"
            self.log(f"[{cycle:10d}] STATE: LY={ly:3d} LCDC=0x{lcdc:02X} (LCD {lcd_status}) PC=0x{pc:04X}")

    def log_section(self, title):
        """Log a section header"""
        if self.enabled:
            self.log("\n" + "="*80)
            self.log(title)
            self.log("="*80 + "\n")

    def close(self):
        """Close the trace file"""
        if self.file:
            self.file.close()
            self.file = None

    def __del__(self):
        """Ensure file is closed"""
        self.close()
