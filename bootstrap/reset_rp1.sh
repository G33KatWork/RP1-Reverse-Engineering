#!/bin/bash

gpioset gpiochip2 2=0
sleep 0.5
gpioset gpiochip2 2=1

i2cdetect -y 10
