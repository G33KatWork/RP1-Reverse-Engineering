#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
import struct

bus = SMBus(10)

def write_bytes(addr, data):
        write = i2c_msg.write(0x43, struct.pack(">I", addr) + data)
        bus.i2c_rdwr(write)

# reads don't seem to work :(
# def read_bytes(addr, length):
#         write = i2c_msg.write(0x43, struct.pack(">I", addr))
#         read = i2c_msg.read(0x43, length)
#         bus.i2c_rdwr(write, read)
#         return list(read)

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


# load original fw
# doesn't really come up
# fw = open("../reversing/of=rp1_fw_0x20000000.bin", "rb").read()

# for i in range(0, len(fw), 64):
#     chunk = fw[i:i+64]
#     write_bytes(0x20000000 + i, chunk)   

# write_bytes(0x4015400c, struct.pack("<I", 0xb007c0de))
# write_bytes(0x40154010, struct.pack("<I", 0xb007c0de ^ 0x20000141))
# write_bytes(0x40154018, struct.pack("<I", 0x100030d0))

# write_bytes(0x40010008, struct.pack("<I", 0x100))
# write_bytes(0x40154000, struct.pack("<I", 0x80000000))
