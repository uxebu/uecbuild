# uecbuild

Depoy Ubuntu UEC images to KVM/LVM based infrastructures

## Setting up LVM & KVM

TBD

## Getting images & kernels

1. Download latest image from http://uec-images.ubuntu.com/ - i.e.
   Ubuntu 11.10 Oneiric Ocelot amd64: http://uec-images.ubuntu.com/oneiric/current/

2. Unpack archive

3. Move .img file to images/ and rename it to a unique, persistent name, i.e. the filename + the current date

4. Move -vmlinuz-virtual file to kernels/ and also rename it

5. Create a new virtual machine

~~~ sh
./uecbuild.py --image images/20111016-foo.img --kernel kernels/20111016-foo-vmlinuz-virtual foo
~~~

