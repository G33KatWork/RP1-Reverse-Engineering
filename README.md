Raspberry Pi RP1 reverse engineering
====================================

This repo contains some code that I wrote when playing around with the new RP1
I/O coprocessor found on the Raspberry Pi 5.

Firmware
--------

The RP1 has two Cortex-M3 cores and runs firmware that gets loaded by the first
stage bootloader running on the videocore. The code is located on an SPI-EEPROM
on the board.

The EEPROM images can be found in an [offical repo here](https://github.com/raspberrypi/rpi-eeprom)

The image contains multiple partitions of which one is a compressed ELF file
which then contains the boot code. In this ELF embedded in the .rodata section
is the RP1 firmware.

The firmware gets loaded by the videocore over I2C.

There are three pins available for Host <-> RP1 bootstrap communication:

    RP1_SDA     AON_GPIO_00
    RP1_SCL     AON_GPIO_01
    RP1_RUN     AON_GPIO_02

[Source](https://github.com/raspberrypi/linux/blob/rpi-6.1.y/arch/arm/boot/dts/bcm2712-rpi-5-b.dts#L644-L646)

SCL and SDA are the usual I2C lines and RP1_RUN is a GPIO that is an inverted
reset pin. Pull it down, the RP1 is in reset, pull it up again, it boots.

Prerequisites
-------------

If you want to run any commands in there, install the following packages.
Preferrably before you kill the RP1 and lose the ethernet link.

    apt install dtc gpiod python3-smbus2 gcc-arm-none-eabi

Accessing the bootstrap hardware
--------------------------------

The bootstrapping hardware, the I2C interface and the RUN GPIO, is not by
default accessible from linux. That can be fixed by loading a [device tree overlay](overlay/rp1_bootstrap.dtso).

When [loading the overlay](overlay/load_overlay.sh), `i2c10` and the formerly
hogged RUN GPIO is exposed to the userspace.

Resetting the RP1
-----------------

**CAREFUL!** When resetting the RP1, all peripherals and the PCIe link will die.
The only way to communicate with the system after this is by using the debug
UART between the two HDMI ports. You can use the Pico debug probe for this.

Also the system might become unstable, because we are ripping out the PCIe
device out of the Linux kernel without properly unbinding any modules. I tried
to play nice here, but the first `rmmod rp1_adc` failed miserably with a
segmentation fault and a pretty kernel stack trace.

[This script](bootstrap/reset_rp1.sh) resets the RP1 and enumerates all I2C
devices on i2c10. You should see a device at address 0x43.

Loading new code
----------------

The I2C protocol is relatively easy judging from the reverse engineered
bootstrapping code in the videocore bootloader.

Registers and memory can be written by performing an I2C write of the address to
write to in big endian, followed by up to 64 bytes of data.

The bootloader first loads the firmware into the SRAM at `0x20000000`.

Then a bunch of Watchdog scratch registers are set to the following values:

* `0x4015400c` = `0xb007c0de`
* `0x40154010` = `0xb007c0de ^ pc` where PC is the entrypoint. Don't forget the thumb bit!
* `0x40154018` = `initial stackpointer`

After the scratch registers have been written, a watchdog reset of the CPU is
performed. The first write sets the bit for the peripheral that should be reset
by the watchdog, presumably this is PROC0, but it's just a guess. Then, a
watchdog reset is triggered by setting the trigger bit.

* `0x40010008` = `0x100`
* `0x40154000` = `0x80000000`

[This script](bootstrap/load_firmware.py) performs these steps.

The protocol is similar, but still a bit different than on the [RP2040](https://github.com/raspberrypi/pico-sdk/blob/master/src/rp2_common/hardware_watchdog/watchdog.c#L77-L97).

I [wrote some code](payload/blinky/main.c) that makes an LED on GPIO17 blink.

Original firmware
-----------------

Reloading the original firmware doesn't work. I don't know why.

The firmware itself doesn't even do that much. It configures clocks, a few pads
for high speed peripherals, sets up the PCIe link and then performs some power
management and general interrupt handling to care for the PCIe link.

Reverse engineering it isn't exactly hard. The problem is, a lot of the reset
and power bits are undocumented at the current time. Since we can execute code
now, it might be possible to perform some detective work and figure out what
certain bits mean.

For videocore reverse engineering, I used [this](https://github.com/NationalSecurityAgency/ghidra/pull/1147)
sleigh processor definition for Ghidra.

Starting the second core
------------------------

Before completely reconfiguring the RP1, I tried starting the second core that
currently lies dormant. The second core is caught in the reset vector of the
firmware and then waits for a pointer in the SRAM to jump to.

However, it also executes a `wfe` instruction and now stops spinning. To make it
execute code again, you need to send it an event. You should be able to do that
by executing an `sev` instruction on the OTHER core. I tried hijacking interrupt
vectors and other things to make the first core do this, but didn't manage to
start the second core. I might have screwed something up along the way.

PCIe access on the original firmware
------------------------------------

The exposed PCIe BARs of the original firmware allow more or less complete
control over the chip. BAR1 maps the peripheral region at 0x40000000 and BAR2
maps the complete SRAM at 0x20000000. [I succesfully controlled some LEDs](pcie/hacks.py)
by poking the right registers over `/dev/mem`.

Dumping the bootrom
-------------------

~~I'd like to dump the boot ROM and look at it. For this, we need something like
a working clock tree, I guess, because we ideally want to spit it out over a
UART with a certain baud rate. We could also set some baud rate, check the
result on a scope and then adjust the baud rate divider until we have something
we can work with.

This is a TODO.~~

Thanks to Michael, we figured out how to perform I2C reads. We were also missing
some resets. `load_firmware.py` now also dumps the boot ROM. Have fun!

Sources of Intel
----------------

A very important source for registers and pinouts is the Linux kernel. I used
the device trees and a bunch of kernel drivers in the official Linux kernel tree
published by the Raspberry Pi foundation.

* [RP1 device-tree](https://github.com/raspberrypi/linux/blob/rpi-6.1.y/arch/arm/boot/dts/rp1.dtsi)
* [RP1 bootstrap pins](https://github.com/raspberrypi/linux/blob/rpi-6.1.y/arch/arm/boot/dts/bcm2712-rpi-5-b.dts#L644-L646)
* [RP1 pinout](https://github.com/raspberrypi/linux/blob/rpi-6.1.y/arch/arm/boot/dts/bcm2712-rpi-5-b.dts#L682-L737)
* [Pinctrl driver](https://github.com/raspberrypi/linux/blob/rpi-6.1.y/drivers/pinctrl/pinctrl-rp1.c)
* [RP1 peripherals datasheet](https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf)
* The pico-sdk. A few things are similar or at least give you an idea about how things could look on the RP1, but not everything is applicable 1:1.

How to make the LED blink
------------------------

    cd payload/blinky
    make

    cd overlay
    ./load_overlay.sh
    cd ..

    cd bootstrap
    ./reset_rp1.sh
    ./load_firmware.py


A plea
------

Please, Raspberry Pi foundation, release a few header files. It doesn't even
need to be full documentation. Just give us a few register descriptions for the
missing bits in the preliminary datasheet.

Oh and a way to attach via SWD would be nice!

Thanks
------

Thanks to the Raspberry Pi foundation. I had some fun this weekend. And the chip
seems to be super versatile and flexible. Please help us nerds use it!

Also thanks go out to Thea! She travelled to Cambridge for business reasons and
offered to buy a Raspberry Pi in the official shop and bring it back for me.
Without her, I still wouldn't have any hardware.
