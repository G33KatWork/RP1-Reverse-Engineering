#!/bin/bash

git clone https://github.com/raspberrypi/rpi-eeprom.git && cd rpi-eeprom && git checkout 5ec5c003bacc73847aadad712aa1fbdace8f1c4e && cd ..
#git clone https://git.venev.name/hristo/rpi-eeprom-compress.git

cd rpi-eeprom-compress && make && cd ..

mkdir extracted && cd extracted
../extract.py ../rpi-eeprom/firmware-2712/latest/pieeprom-2023-10-18.bin
cat 68272.bin | ../rpi-eeprom-compress/uncompress > ../loader.elf
cd ..

dd if=loader.elf of=rp1_fw_0x20000000.bin bs=1 skip=$((0x725f4)) count=$((0x6570))
