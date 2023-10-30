#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
import struct

bus = SMBus(10)

def write_bytes(addr, data):
        write = i2c_msg.write(0x43, struct.pack(">I", addr) + data)
        bus.i2c_rdwr(write)

def read_bytes(addr, length):
        write = i2c_msg.write(0x43, struct.pack(">I", addr))
        bus.i2c_rdwr(write)
        read = i2c_msg.read(0x43, length)
        bus.i2c_rdwr(read)
        return bytes(list(read))


#original firmware clears some reset, after that, we can read the chip ID!
write_bytes(0x40017004, struct.pack("<I", 0x800000))
chipid = read_bytes(0x40000000, 4)
print("Chip ID:", hex(struct.unpack("<I", chipid)[0]))

# just clear all resets, there might be even more somewhere
write_bytes(0x40017000, struct.pack("<I", 0xffffffff))
write_bytes(0x40017004, struct.pack("<I", 0xffffffff))

# dump the bootrom
rom = open("bootrom.bin", "wb")

for i in range(0, 64*1024, 64):
    chunk = read_bytes(0 + i, 64)
    rom.write(chunk)

rom.close()

# # load some code that just spins endlessly
# write_bytes(0x20000000, b"\xfe\xe7")
# 
# write_bytes(0x4015400c, struct.pack("<I", 0xb007c0de))
# write_bytes(0x40154010, struct.pack("<I", 0xb007c0de ^ 0x20000001))
# write_bytes(0x40154018, struct.pack("<I", 0x100030d0))
# 
# write_bytes(0x40010008, struct.pack("<I", 0x100))
# write_bytes(0x40154000, struct.pack("<I", 0x80000000))


# load blinky binary
fw = open("../payload/blinky/blinky.bin", "rb").read()

for i in range(0, len(fw), 64):
    chunk = fw[i:i+64]
    write_bytes(0x20000000 + i, chunk)   

write_bytes(0x4015400c, struct.pack("<I", 0xb007c0de))
write_bytes(0x40154010, struct.pack("<I", 0xb007c0de ^ 0x20000001))
write_bytes(0x40154018, struct.pack("<I", 0x100030d0))

write_bytes(0x40010008, struct.pack("<I", 0x100))
write_bytes(0x40154000, struct.pack("<I", 0x80000000))


# # load original fw
# fw = open("../reversing/rp1_fw_0x20000000.bin", "rb").read()

# for i in range(0, len(fw), 64):
#     chunk = fw[i:i+64]
#     write_bytes(0x20000000 + i, chunk)   

# write_bytes(0x4015400c, struct.pack("<I", 0xb007c0de))
# write_bytes(0x40154010, struct.pack("<I", 0xb007c0de ^ 0x20000141))
# write_bytes(0x40154018, struct.pack("<I", 0x100030d0))

# write_bytes(0x40010008, struct.pack("<I", 0x100))
# write_bytes(0x40154000, struct.pack("<I", 0x80000000))
