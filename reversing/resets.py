#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
import gpiod
import struct
import time
import sys

bus = SMBus(10)

chip = gpiod.Chip("gpiochip2")
run = chip.find_line("RP1_RUN")
run.request(consumer="RP1_Loader", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])

def write_bytes(addr, data):
        write = i2c_msg.write(0x43, struct.pack(">I", addr) + data)
        bus.i2c_rdwr(write)

def read_bytes(addr, length):
        write = i2c_msg.write(0x43, struct.pack(">I", addr))
        bus.i2c_rdwr(write)
        read = i2c_msg.read(0x43, length)
        bus.i2c_rdwr(read)
        return bytes(list(read))

def reset_rp1():
    run.set_value(0)
    time.sleep(0.1)
    run.set_value(1)
    time.sleep(0.1)

def read_reg(addr):
    reg = read_bytes(addr, 4)
    return struct.unpack("<I", reg)[0]

def write_reg(addr, val):
    write_bytes(addr, struct.pack("<I", val))

def reg_print(addr):
    print(hex(read_reg(addr)))

def dump_reg_area(addr, l):
    regs = b""
    for i in range(0, l, 4):
        regs += read_bytes(addr + i, 4)
    print(hexdump(regs))

# reading from the commented out addresses causes weird responses to happen aferwards
peripherals = [
    {"name": "RP1_SYSINFO_BASE", "base": 0x000000, "tag_off": 0xa4, "tag": b'isys' },
    {"name": "RP1_TBMAN_BASE", "base": 0x004000 },
    {"name": "RP1_SYSCFG_BASE", "base": 0x008000, "tag_off": 0x3c, "tag": b'GFCS' },
    {"name": "RP1_OTP_BASE", "base": 0x00c000, "tag_off": 0x4c, "tag": b'PTOT' },
    {"name": "RP1_POWER_BASE", "base": 0x010000, "tag_off": 0x14, "tag": b'rwop' },
    #{"name": "RP1_RESETS_BASE", "base": 0x014000, "tag_off": 0x28, "tag": b'stsr' },                don't need that, we are poking it
    {"name": "RP1_CLOCKS_BANK_DEFAULT_BASE", "base": 0x018000 },
    {"name": "RP1_CLOCKS_BANK_VIDEO_BASE", "base": 0x01c000, "tag_off": 0x64, "tag": b'vklc' },
    {"name": "RP1_PLL_SYS_BASE", "base": 0x020000, "tag_off": 0x34, "tag": b'LLP\x00' },
    {"name": "RP1_PLL_AUDIO_BASE", "base": 0x024000, "tag_off": 0x34, "tag": b'LLP\x00' },
    {"name": "RP1_PLL_VIDEO_BASE", "base": 0x028000, "tag_off": 0x34, "tag": b'LLP\x00' },
    {"name": "RP1_UART0_BASE", "base": 0x030000 },
    {"name": "RP1_UART1_BASE", "base": 0x034000 },
    {"name": "RP1_UART2_BASE", "base": 0x038000 },
    {"name": "RP1_UART3_BASE", "base": 0x03c000 },
    {"name": "RP1_UART4_BASE", "base": 0x040000 },
    {"name": "RP1_UART5_BASE", "base": 0x044000 },
    {"name": "RP1_SPI8_BASE", "base": 0x04c000 },
    {"name": "RP1_SPI0_BASE", "base": 0x050000 },
    {"name": "RP1_SPI1_BASE", "base": 0x054000 },
    {"name": "RP1_SPI2_BASE", "base": 0x058000 },
    {"name": "RP1_SPI3_BASE", "base": 0x05c000 },
    {"name": "RP1_SPI4_BASE", "base": 0x060000 },
    {"name": "RP1_SPI5_BASE", "base": 0x064000 },
    {"name": "RP1_SPI6_BASE", "base": 0x068000 },
    {"name": "RP1_SPI7_BASE", "base": 0x06c000 },
    {"name": "RP1_I2C0_BASE", "base": 0x070000 },
    {"name": "RP1_I2C1_BASE", "base": 0x074000 },
    {"name": "RP1_I2C2_BASE", "base": 0x078000 },
    {"name": "RP1_I2C3_BASE", "base": 0x07c000 },
    {"name": "RP1_I2C4_BASE", "base": 0x080000 },
    {"name": "RP1_I2C5_BASE", "base": 0x084000 },
    {"name": "RP1_I2C6_BASE", "base": 0x088000 },
    {"name": "RP1_AUDIO_IN_BASE", "base": 0x090000, "tag_off": 0x34, "tag": b'\xa1dua' },
    {"name": "RP1_AUDIO_OUT_BASE", "base": 0x094000, "tag_off": 0x4C, "tag": b'ODUA' },
    {"name": "RP1_PWM0_BASE", "base": 0x098000, "tag_off": 0x64, "tag": b'AMWP' },
    {"name": "RP1_PWM1_BASE", "base": 0x09c000, "tag_off": 0x64, "tag": b'AMWP' },
    {"name": "RP1_I2S0_BASE", "base": 0x0a0000 },
    {"name": "RP1_I2S1_BASE", "base": 0x0a4000 },
    {"name": "RP1_I2S2_BASE", "base": 0x0a8000 },
    #{"name": "RP1_TIMER_BASE", "base": 0x0ac000, "tag_off": 0x44, "tag": b'RMIT' },                 #annoying because things are ticking
    {"name": "RP1_SDIO0_APBS_BASE", "base": 0x0b0000, "tag_off": 0x34, "tag": b'OIDS' },
    {"name": "RP1_SDIO1_APBS_BASE", "base": 0x0b4000, "tag_off": 0x34, "tag": b'OIDS' },
    {"name": "RP1_BUSFABRIC_MONITOR_BASE", "base": 0x0c0000 },
    {"name": "RP1_BUSFABRIC_AXISHIM_BASE", "base": 0x0c4000 },
    #{"name": "RP1_ADC_BASE", "base": 0x0c8000 },
    {"name": "RP1_IO_BANK0_BASE", "base": 0x0d0000 },
    {"name": "RP1_IO_BANK1_BASE", "base": 0x0d4000 },
    {"name": "RP1_IO_BANK2_BASE", "base": 0x0d8000 },
    {"name": "RP1_UNKNOWN_HOLE", "base": 0x0dc000 },
    {"name": "RP1_SYS_RIO0_BASE", "base": 0x0e0000, "tag_off": 0x10, "tag": b'POIR' },
    {"name": "RP1_SYS_RIO1_BASE", "base": 0x0e4000, "tag_off": 0x10, "tag": b'POIR' },
    {"name": "RP1_SYS_RIO2_BASE", "base": 0x0e8000, "tag_off": 0x10, "tag": b'POIR' },
    {"name": "RP1_PADS_BANK0_BASE", "base": 0x0f0000, "tag_off": 0x84, "tag": b'0dap' },
    {"name": "RP1_PADS_BANK1_BASE", "base": 0x0f4000, "tag_off": 0x1C, "tag": b'1dap' },
    {"name": "RP1_PADS_BANK2_BASE", "base": 0x0f8000, "tag_off": 0x54, "tag": b'2dap' },
    {"name": "RP1_PADS_ETH_BASE", "base": 0x0fc000, "tag_off": 0x40, "tag": b'edap' },
    {"name": "RP1_ETH_IP_BASE", "base": 0x100000 },
    {"name": "RP1_ETH_CFG_BASE", "base": 0x104000, "tag_off": 0x2C, "tag": b'HTEC' },
    {"name": "RP1_PCIE_APBS_BASE", "base": 0x108000, "tag_off": 0x1B8, "tag": b'EICP' },
    {"name": "RP1_MIPI0_CSIDMA_BASE", "base": 0x110000 },
    {"name": "RP1_MIPI0_CSIHOST_BASE", "base": 0x114000 },
    {"name": "RP1_MIPI0_DSIDMA_BASE", "base": 0x118000 },
    {"name": "RP1_MIPI0_DSIHOST_BASE", "base": 0x11c000 },
    {"name": "RP1_MIPI0_MIPICFG_BASE", "base": 0x120000, "tag_off": 0x38, "tag": b'IPIM' },
    #{"name": "RP1_MIPI0_ISP_BASE", "base": 0x124000 },
    {"name": "RP1_MIPI1_CSIDMA_BASE", "base": 0x128000 },
    {"name": "RP1_MIPI1_CSIHOST_BASE", "base": 0x12c000 },
    {"name": "RP1_MIPI1_DSIDMA_BASE", "base": 0x130000 },
    {"name": "RP1_MIPI1_DSIHOST_BASE", "base": 0x134000 },
    {"name": "RP1_MIPI1_MIPICFG_BASE", "base": 0x138000, "tag_off": 0x38, "tag": b'IPIM' },
    #{"name": "RP1_MIPI1_ISP_BASE", "base": 0x13c000 },
    {"name": "RP1_VIDEO_OUT_CFG_BASE", "base": 0x140000, "tag_off": 0x24, "tag": b'FCOV' },
    {"name": "RP1_VIDEO_OUT_VEC_BASE", "base": 0x144000 },
    {"name": "RP1_VIDEO_OUT_DPI_BASE", "base": 0x148000 },
    {"name": "RP1_XOSC_BASE", "base": 0x150000, "tag_off": 0x24, "tag": b'CSOX' },
    {"name": "RP1_WATCHDOG_BASE", "base": 0x154000, "tag_off": 0x2C, "tag": b'GODW' },
    #{"name": "RP1_DMA_TICK_BASE", "base": 0x158000, "tag_off": 0x10, "tag": b'TAMD' },
    {"name": "RP1_SDIO_CLOCKS_BASE", "base": 0x15c000 },
    {"name": "RP1_USBHOST0_APBS_BASE", "base": 0x160000, "tag_off": 0xA4, "tag": b'BSUS' },
    {"name": "RP1_USBHOST1_APBS_BASE", "base": 0x164000, "tag_off": 0xA4, "tag": b'BSUS' },
    {"name": "RP1_ROSC0_BASE", "base": 0x168000, "tag_off": 0x18, "tag": b'CSOR' },
    {"name": "RP1_ROSC1_BASE", "base": 0x16c000, "tag_off": 0x18, "tag": b'CSOR' },
    {"name": "RP1_VBUSCTRL_BASE", "base": 0x170000, "tag_off": 0x18, "tag": b'SUBV' },
    #{"name": "RP1_TICKS_BASE", "base": 0x174000, "tag_off": 0x60, "tag": b'kcit' },             #annoying because things are ticking
    {"name": "RP1_PIO_APBS_BASE", "base": 0x178000, "tag_off": 0x20, "tag": b'3oip' },
    {"name": "RP1_SDIO0_AHBLS_BASE", "base": 0x180000 },
    {"name": "RP1_SDIO1_AHBLS_BASE", "base": 0x184000 },
    #{"name": "RP1_DMA_BASE", "base": 0x188000 },
    #{"name": "RP1_RAM_BASE", "base": 0x1c0000 },
    #{"name": "RP1_USBHOST0_AXIS_BASE", "base": 0x200000 },
    #{"name": "RP1_USBHOST1_AXIS_BASE", "base": 0x300000 },
    {"name": "RP1_EXAC_BASE", "base": 0x400000 },
]

def main():
    reset_rp1()

    # clear all the resets
    write_reg(0x40000000 + 0x017000 + 0, 0xffffffff)
    write_reg(0x40000000 + 0x017000 + 4, 0xffffffff)
    write_reg(0x40000000 + 0x017000 + 8, 0xffffffff)

    # SPI8 seems to have been used by the bootrom, we should reset it once to reset all its registers
    write_reg(0x40000000 + 0x016000 + 4, (1 << 18))
    write_reg(0x40000000 + 0x017000 + 4, (1 << 18))

    skip_bits = [
        [
            1,          #AUDIO_IN
            2,          #AUDIO_OUT

            4,          #DMA_TICK
            5,          #ETH_IP
            6,          #makes RP1_EXAC_BASE differ and then fail reads
            7,          #I2C0
            8,          #I2C1
            9,          #I2C2
            10,         #I2C3,
            11,         #I2C4
            12,         #I2C5, is the bootstrap I2C interface
            13,         #I2C6
            14,         #I2S0
            15,         #I2S1
            16,         #I2S2
            17,         #IO_BANK0
            18,         #IO_BANK1, contains the I2C pins for bootstrap interface
            19,         #IO_BANK2
            20,         #MIPI0_CSIHOST, MIPI0_DSIDMA, MIPI0_DSIHOST, MIPI0_ISP
            21,         #MIPI1_CSIHOST, MIPI1_DSIDMA, MIPI1_DSIHOST, MIPI1_ISP
            22,         #PADS_BANK0
            23,         #PADS_BANK1, contains the I2C pins for bootstrap interface
            24,         #PADS_BANK1
            25,         #PADS_ETH
            26,         #PCIE_APBS
            27,         #PIO_APBS
            28,         #PLL_AUDIO
            29,         #PLL_SYS
            30,         #PLL_VIDEO
            31,         #PROC1, might also be another PLL
        ],
        [
            4,          #PWM0
            5,          #PWM1
            6,          #ROSC0
            7,          #ROSC1
            8,          #SDIO0_APBS
            9,          #SDIO1_APBS
            10,         #SPI0
            11,         #SPI1
            12,         #SPI2
            13,         #SPI3
            14,         #SPI4
            15,         #SPI5
            16,         #SPI6
            17,         #SPI7
            18,         #SPI8
            19,         #SYS_RIO0
            20,         #SYS_RIO1
            21,         #SYS_RIO2
            22,         #SYSCFG
            23,         #SYSINFO

            25,         #TIMER
            26,         #UART0
            27,         #UART1
            28,         #UART2
            29,         #UART3
            30,         #UART4
            31,         #UART5
        ],
        [
            0,          #USBHOST0
            1,          #USBHOST1
            2,          #VBUSCTRL
            3,          #VIDEO_OUT_DPI
        ],
    ]

    # try brute forcing with tags
    for offset in range(3):
        for bit in range(32):
            if bit in skip_bits[offset]:
                #print(f"Skipping reset bit {bit} in reset reg {offset}\n")
                continue

            print(f"{offset} {bit}")
            write_reg(0x40000000 + 0x016000 + offset*4, 1 << bit)

            for p in peripherals:
                if "tag_off" in p:
                    tag = read_bytes(0x40000000 + p["base"] + p["tag_off"], 4)
                    if p["tag"] != tag:
                        print(f"Reset bit {bit} in reset reg {offset} caused")
                        print(f"tag difference: {p['tag']} vs {tag}")

            write_reg(0x40000000 + 0x017000 + offset*4, 1 << bit)

    #sys.exit(0)

    # try random register offsets and compare read when not reset and reset
    for regcheck_offset in range(0, 1024, 4):
        print(f"reg_offset {regcheck_offset:02x}")
        vals = []
        for p in peripherals:
            #print(f"Reading {p['name']}")
            vals += [read_reg(0x40000000 + p["base"] + regcheck_offset)]

        for offset in range(3):
            for bit in range(32):
                if bit in skip_bits[offset]:
                    #print(f"Skipping reset bit {bit} in reset reg {offset}\n")
                    continue

                #print(f"Setting reset bit {bit} in reset reg {offset}")
                write_reg(0x40000000 + 0x016000 + offset*4, 1 << bit)

                vals2 = []
                for p in peripherals:
                    #print(f"Reading {p['name']}")
                    vals2 += [read_reg(0x40000000 + p["base"] + regcheck_offset)]

                for (i, (v1, v2)) in enumerate(zip(vals, vals2)):
                    if v1 != v2:
                        print(f"Reset bit {bit} in reset reg {offset} caused")
                        print(f"difference in {peripherals[i]['name']}: {v1:08x} {v2:08x}")

                write_reg(0x40000000 + 0x017000 + offset*4, 1 << bit)
                #print("")


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
