#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
import gpiod
import struct
import time

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

def main():
    reset_rp1()

    #original firmware clears some reset, after that, we can read the chip ID!
    write_bytes(0x40017004, struct.pack("<I", 0x800000))
    chipid = read_bytes(0x40000000, 4)
    print("Chip ID:", hex(struct.unpack("<I", chipid)[0]))

    # clear all the resets
    write_reg(0x40000000 + 0x017000 + 0, 0xffffffff)
    write_reg(0x40000000 + 0x017000 + 4, 0xffffffff)
    write_reg(0x40000000 + 0x017000 + 8, 0xffffffff)

    # dump the bootrom
    rom = open("bootrom.bin", "wb")

    # dump 32K bootrom
    # the window is 64K, but after 32K the ROM repeats
    # we dump the upper 32K, because the first 8 bytes are always 0? might be some controls there
    # also we dump 4 bytes at a time. dumping 64 byte chunks yields randomly flipped bits
    for i in range(0, 32*1024, 4):
        chunk = read_bytes(0x8000 + i, 4)
        rom.write(chunk)

    rom.close()

if __name__ == "__main__":
    main()
