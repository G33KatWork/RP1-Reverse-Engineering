#include <stdint.h>

#define CORE_ID (((volatile uint32_t*)(0xe00ff01c)))

void main() {
    // Catch core 1 and just let it busy loop
    if (*CORE_ID != 0) {
        while(1) {
            *((volatile uint32_t*)(0x400e0000)) |= (1 << 17);
            for(int i = 0; i < 100000; i++);
            *((volatile uint32_t*)(0x400e0000)) &= ~(1 << 17);
            for(int i = 0; i < 100000; i++);
        }
    }

    // Poke some resets, original FW does this too, this resets the peripherals used by the bootrom
    *((volatile uint32_t*)(0x40014004)) |= 0x40000;      // Reset SPI8
    *((volatile uint32_t*)(0x40014000)) |= 0x1000;       // Reset I2C5

    //*((volatile uint32_t*)(0x40014000)) = 0x4000000;     // Unreset everything but PCIE_APBS
    //*((volatile uint32_t*)(0x40014004)) = 0;             // Unreset everything
    //*((volatile uint32_t*)(0x40014008)) = 0;             // Unreset everything

    // Clear the reset bit for the 2nd core or its PLL, whatever it is, it makes the core go brrr
    *((volatile uint32_t*)(0x40014000)) &= ~(1<<31);

    // clear some resets:
    // 0:17     IO_BANK0
    // 0:22     PADS_BANK0
    // 1:19     SYS_RIO0
    *((volatile uint32_t*)(0x40017000)) = (1<<17) | (1<<22);
    *((volatile uint32_t*)(0x40017004)) = 1<<19;

    // func: SYS_RIO, output and output enable from peripheral on GPIO17
    *((volatile uint32_t*)(0x400d008c)) = 0x85;

    // pad control for GPIO17
    *((volatile uint32_t*)(0x400f0048)) = 0x56;

    // output enable = 1 for GPIO17
    *((volatile uint32_t*)(0x400e0004)) |= (1 << 17);

    // Core 1 should be stuck at a wfe in the bootrom
    // we can write two more watchdog scratch registers with a PC and SP and kick it off with an sev
    *((volatile uint32_t*)(0x40154014)) = 0x4FF83F2D ^ 0x20000001;
    *((volatile uint32_t*)(0x4015401C)) = 0x100030d0;
    asm volatile("sev");

    while(1) {
        // Execute a WFE to halt this core
        // Otherwise the blinking noticably slows down because of bus contention
        asm volatile("wfe");
    }
}
