ENTRY(start)

MEMORY
  {
    RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
    IRAM (rwx): ORIGIN = 0x10000000, LENGTH = 8K
    DRAM (rw): ORIGIN = 0x10002000, LENGTH = 8K
  }

SECTIONS
{
  .text : 
  {
    startup.o(.text*)
    *(.text*)
    *(.rodata .rodata.*)
    . = ALIGN(4);
  } > RAM

  .bss :
  {
      __bss_start__ = .;
      *(.bss*)
      *(COMMON)
      . = ALIGN(4);
      __bss_end__ = .;
  } > RAM

  .heap :
  {
    __heap_start__ = .;
    PROVIDE(end = __heap_start__);
    PROVIDE(_heap_start = __heap_start__);
    . = . + ((LENGTH(RAM) - (. - (ORIGIN(RAM)))) / 2);
    . = ALIGN(4);
    __heap_end__ = .;
    PROVIDE(_heap_end = __heap_end__);
  } > RAM

  .stack :
  {
    __stack_start__ = .;
    . = . + LENGTH(DRAM) - (. - ORIGIN(DRAM));
    . = ALIGN(4);
    __stack_end__ = .;
    STACK_SIZE = __stack_end__ - __stack_start__;
  } > DRAM
}
