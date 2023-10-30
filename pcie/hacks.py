#!/usr/bin/env python3

import os, mmap, struct

RP1_BAR1 = 0x1f00000000
RP1_BAR1_LEN = 0x400000

RP1_BAR2 = 0x1f00400000
PR1_BAR2_LEN = 64*1024

SYSINFO_CHIP_ID_OFFSET  = 0x00000000
SYSINFO_PLATFORM_OFFSET = 0x00000004

RP1_SYSINFO_BASE = 0x000000
RP1_TBMAN_BASE = 0x004000
RP1_SYSCFG_BASE = 0x008000
RP1_OTP_BASE = 0x00c000
RP1_POWER_BASE = 0x010000
RP1_RESETS_BASE = 0x014000
RP1_ROSC0_BASE = 0x168000
RP1_PIO_APBS_BASE = 0x178000
RP1_RAM_BASE = 0x1c0000
RP1_RAM_SIZE = 0x020000

RP1_PCIE_APBS_BASE = 0x108000
RP1_IO_BANK0_BASE = 0x0d0000
RP1_SYS_RIO0_BASE = 0x0e0000
RP1_PROC_RIO_MAYBE_BASE = 0x0e8000      #Not documented, but datasheet show a convenient 0x4000 bytes hole after SYS_RIO2 and PROC_RIO is nowhere documented
RP1_PADS_BANK0_BASE = 0x0f0000

MAGIC_BOOT_PTR_OFFSET = 0x59d8


#LED on GPIO17
GPIO17_CTRL = 0x8c
PAD_GPIO17 = (17*4)+4

#SYS_RIO offsets
SYS_RIO_OUT_OFF = 0x00
SYS_RIO_OE_OFF = 0x04
SYS_RIO_IN_OFF = 0x08



def main():
    fd_periph = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    mem_periph = mmap.mmap(fd_periph, RP1_BAR1_LEN, offset=RP1_BAR1)

    fd_sram = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    mem_sram = mmap.mmap(fd_sram, PR1_BAR2_LEN, offset=RP1_BAR2)

    def reg_read(dev, reg, l=4):
        mem_periph.seek(dev + reg)
        if l == 4:
            return struct.unpack("<I", mem_periph.read(4))[0]
        else:
            return mem_periph.read(l)
    
    def reg_write(dev, reg, val):
        mem_periph.seek(dev + reg)
        mem_periph.write(struct.pack("<I", val))
    
    print("Chip ID:", hex(reg_read(RP1_SYSINFO_BASE, SYSINFO_CHIP_ID_OFFSET)))
    print("Platform", hex(reg_read(RP1_SYSINFO_BASE, SYSINFO_PLATFORM_OFFSET)))

    mem_sram.seek(MAGIC_BOOT_PTR_OFFSET)
    ptr1, ptr2 = struct.unpack("<II", mem_sram.read(8))
    print(hex(ptr1), hex(ptr2))



    # # code for led on:
    # #0x400d008c = 0x85
    # #0x400e0004 = 1 << 17
    # #0x400e0000 = 1 << 17
    # #pads to 0x56??

    print(hex(reg_read(RP1_IO_BANK0_BASE, GPIO17_CTRL)))
    print(hex(reg_read(RP1_PADS_BANK0_BASE, PAD_GPIO17)))


    # turn LED on
    print(hex(reg_read(RP1_IO_BANK0_BASE, GPIO17_CTRL)))
    reg_write(RP1_IO_BANK0_BASE, GPIO17_CTRL, 0x85) #func: SYS_RIO, output and output enable from peripheral
    reg_write(RP1_PADS_BANK0_BASE, PAD_GPIO17, 0x56)

    # output enable
    oe = reg_read(RP1_SYS_RIO0_BASE, SYS_RIO_OE_OFF)
    reg_write(RP1_SYS_RIO0_BASE, SYS_RIO_OE_OFF, oe | (1 << 17))

    # toggle pin
    out = reg_read(RP1_SYS_RIO0_BASE, SYS_RIO_OUT_OFF)
    reg_write(RP1_SYS_RIO0_BASE, SYS_RIO_OUT_OFF, out ^ (1 << 17))



    #print(hex(reg_read(RP1_SYS_RIO0_BASE, SYS_RIO_OUT_OFF)))

    #print(hexdump(reg_read(0x4000, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_SYSINFO_BASE, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_SYSCFG_BASE, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_TBMAN_BASE, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_POWER_BASE, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_RESETS_BASE, 0, l=0x4000)))


    #print(hexdump(reg_read(RP1_IO_BANK0_BASE+0*0x4000, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_SYS_RIO0_BASE+0*0x4000, 0, l=0x4000)))
    #print(hexdump(reg_read(RP1_PADS_BANK0_BASE+0*0x4000, 0, l=0x4000)))

    #print(hexdump(reg_read(RP1_PIO_APBS_BASE, 0, l=0x8000)))
    #print(hexdump(reg_read(RP1_ROSC0_BASE, 0, l=0x4000)))


class hexdump:
    def __init__(self, buf, off=0):
        self.buf = buf
        self.off = off

    def __iter__(self):
        last_bs, last_line = None, None
        for i in range(0, len(self.buf), 16):
            bs = bytearray(self.buf[i : i + 16])
            line = "{:08x}  {:23}  {:23}  |{:16}|".format(
                self.off + i,
                " ".join(("{:02x}".format(x) for x in bs[:8])),
                " ".join(("{:02x}".format(x) for x in bs[8:])),
                "".join((chr(x) if 32 <= x < 127 else "." for x in bs)),
            )
            if bs == last_bs:
                line = "*"
            if bs != last_bs or line != last_line:
                yield line
            last_bs, last_line = bs, line
        yield "{:08x}".format(self.off + len(self.buf))

    def __str__(self):
        return "\n".join(self)

    def __repr__(self):
        return "\n".join(self)

if __name__ == "__main__":
    main()
