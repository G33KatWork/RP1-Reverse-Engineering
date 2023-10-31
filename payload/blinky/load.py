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

reset_rp1()

#original firmware clears some reset, after that, we can read the chip ID!
write_bytes(0x40017004, struct.pack("<I", 0x800000))
chipid = read_bytes(0x40000000, 4)
print("Chip ID:", hex(struct.unpack("<I", chipid)[0]))

# just clear all resets, there might be even more somewhere
#write_bytes(0x40017000, struct.pack("<I", 0xffffffff))
#write_bytes(0x40017004, struct.pack("<I", 1<<19))

# load binary
fw = open(sys.argv[1], "rb").read()

for i in range(0, len(fw), 64):
    chunk = fw[i:i+64]
    write_bytes(0x20000000 + i, chunk)

write_bytes(0x4015400c, struct.pack("<I", 0xb007c0de))
write_bytes(0x40154010, struct.pack("<I", 0xb007c0de ^ 0x20000001))
write_bytes(0x40154018, struct.pack("<I", 0x100030d0))

write_bytes(0x40010008, struct.pack("<I", 0x100))
write_bytes(0x40154000, struct.pack("<I", 0x80000000))
