#!/usr/bin/env python
import subprocess
import sys
from threading import Timer
import os.path
import shelve
import sys

if len(sys.argv) < 4:
    print("Usage: qemu_check.py [<arch>] <worker#> <build#>")
    sys.exit(1)
#arch = "amd64" if len(sys.argv) < 4 else sys.argv[1]
arch   = sys.argv[1]
worker = sys.argv[2]
build  = sys.argv[3]

conf_var = "shelve"
d = shelve.open(conf_var)
vmlinuz_list = d["version"]
d.close()

qemu_timeout = 360
BaseURIamd64 = 'http://gentoo.osuosl.org/experimental/amd64/openstack/'\
          'gentoo-openstack-amd64-default-'
BaseURIarm = ''
SnapshotDate = 'latest'


def command(cmd, timeout_sec):
    work = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        for line in proc.stdout:
            a = line.strip()
            print(a)
            if 'This is localhost' in str(a):
                work = True
                break
    finally:
        timer.cancel()
    proc.kill()
    return work

if arch == 'amd64':
    vmimage = "/tmp/gentoo-amd64-w" + worker + ".qcow2"
    # + "-b" + build
    cmd_qemu = 'qemu-system-x86_64 -m 128M -kernel ' \
        'linux-amd64-build/arch/x86/boot/bzImage' \
        ' -nographic -serial mon:stdio -hda ' + vmimage + \
        ' -append "root=/dev/sda1 console=ttyS0,115200n8 console=tty0"'
elif arch == 'arm':
    vmimage = "/tmp/gentoo-arm-w" + worker + ".qcow2"
    # + "-b" + build + ".qcow2"
    cmd_qemu = 'qemu-system-arm -M vexpress-a9 -smp 2 -m 1G -kernel ' \
        'linux-arm-build/arch/arm/boot/zImage' \
        ' -dtb linux-arm-build/arch/arm/boot/dts/vexpress-v2p-ca9.dtb' \
        ' -sd ' + vmimage + ' -nographic -append "console=ttyAMA0,115200' \
        ' root=/dev/mmcblk0 rootwait"'

if not os.path.isfile(vmimage):
    if arch == 'amd64':
        ImageURI = BaseURIamd64 + SnapshotDate + '.qcow2'
    elif arch == 'arm':
        ImageURI = BaseURIarm + SnapshotDate + '.qcow2'
    cmd_wget = 'wget -N ' + ImageURI + ' -O ' + vmimage
    proc2 = subprocess.Popen(cmd_wget, stdout=subprocess.PIPE, shell=True)
    for line in proc2.stdout:
        a = line.strip()
        print(a)
    if not os.path.isfile(vmimage):
        print("Cannot download file: " + ImageURI)
        sys.exit(1)
else:
    print("vmimage present: " + vmimage)

print(vmlinuz_list)

if isinstance(vmlinuz_list, str):
    vmlinuz_list = [vmlinuz_list]

for vmlinuz in vmlinuz_list:
    print(vmlinuz)
    work = command(cmd_qemu, qemu_timeout)
    if work:
        print("worked")
    else:
        print("failed")
        sys.exit(1)
