.global _start
.code 16

_start:
    b _start

# arm-none-eabi-as -o loop.o loop.S
# arm-none-eabi-objdump -d loop.o
