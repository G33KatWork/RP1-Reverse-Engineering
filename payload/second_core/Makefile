OBJ = startup.o main.o
BINARY = second_core

AS = arm-none-eabi-as
CC = arm-none-eabi-gcc
LD = arm-none-eabi-gcc
OBJCOPY  = arm-none-eabi-objcopy

ASFLAGS = -mcpu=cortex-m3 
CFLAGS = -mcpu=cortex-m3 -ffunction-sections -fdata-sections -O0 -mthumb
LDFLAGS = -mcpu=cortex-m3 -T linker.ld -nostartfiles 

all: $(BINARY).bin

%.o: %.c
	$(CC) -c -o $@ $< $(CFLAGS)

%.o: %.S
	$(CC) -c -o $@ $< $(CFLAGS)

$(BINARY).elf: $(OBJ)
	$(LD) $(LDFLAGS) -o $@ $^

$(BINARY).bin: $(BINARY).elf
	$(OBJCOPY) -O binary $< $@

clean:
	rm -rf $(OBJ) $(BINARY).elf $(BINARY).bin

load: all
	../load.py $(BINARY).bin

.PHONY: clean all load
