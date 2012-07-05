# uecbuild

Depoy Ubuntu UEC images to KVM/LVM based infrastructures.

## Setting up LVM & KVM

TBD

## Getting images & kernels

1. Download latest image from http://uec-images.ubuntu.com/ - i.e.
   [latest Ubuntu 12.04](http://uec-images.ubuntu.com/precise/current/precise-server-cloudimg-amd64.tar.gz)

2. Unpack archive in `/path/to/images` (don't change without changing libvirt domain configs, too)

3. Rename extracted folder to uec site's build date, i.e., "20120623"

4. Create a new virtual machine

~~~
./uecbuild.py --image /path/to/images/20120623/precise-server-cloudimg-amd64.img \
              --kernel /path/to/images/20120623/precise-server-cloudimg-amd64-vmlinuz-virtual \
              <name>
~~~
