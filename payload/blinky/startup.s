.text
.global start
.code 16

start: 
    @ zero out .bss section
    ldr     r4, =__bss_start__
    ldr     r5, =__bss_end__
    mov     r6, #0

_bss_loop:
    str     r6, [r4]
    add     r4, #4
    cmp     r4, r5
    blt     _bss_loop

    @ set stack + function pointer
    # ldr     r0, =__stack_end__
    # mov     sp, r0
    ldr     r0, =main
    mov     lr, pc
    blx     main

_loop:
    b       _loop
