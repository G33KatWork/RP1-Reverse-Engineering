#include <stdint.h>

#define CORE_ID (((volatile uint32_t*)(0xe00ff01c)))

void main() {
    // Catch core 1 and just let it busy loop
    if (*CORE_ID != 0) {
        while(1);
    }

    // // Poke some resets, original FW does this too
    // *((volatile uint32_t*)(0x40014004)) |= 0x40000;
    // *((volatile uint32_t*)(0x40014000)) |= 0x1000;
    // *((volatile uint32_t*)(0x40014000)) = 0x4000000;
    // *((volatile uint32_t*)(0x40014004)) = 0;
    // *((volatile uint32_t*)(0x40014008)) = 0;

    // clear some reset, unknown yet what exactly this is, but it makes LED go blink
    *((volatile uint32_t*)(0x40017004)) = 1<<19;

    // func: SYS_RIO, output and output enable from peripheral
    *((volatile uint32_t*)(0x400d008c)) = 0x85;

    // pad control
    *((volatile uint32_t*)(0x400f0048)) = 0x56;

    // output enable = 1
    *((volatile uint32_t*)(0x400e0004)) |= (1 << 17);

    // set output to high
    *((volatile uint32_t*)(0x400e0000)) |= (1 << 17);

    while(1) {
        *((volatile uint32_t*)(0x400e0000)) |= (1 << 17);
        for(int i = 0; i < 100000; i++);
        *((volatile uint32_t*)(0x400e0000)) &= ~(1 << 17);
        for(int i = 0; i < 100000; i++);
    }
}
