#!/bin/bash

dtc -@ -I dts -O dtb -o rp1_bootstrap.dtbo rp1_bootstrap.dtso
mkdir -p /sys/kernel/config/device-tree/overlays/rp1
cat rp1_bootstrap.dtbo > /sys/kernel/config/device-tree/overlays/rp1/dtbo
modprobe i2c-dev
