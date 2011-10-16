#!/usr/bin/env python

import argparse
import os
import subprocess
import sys
import tempfile

DEFAULT_KERNEL = "kernels/maverick-server-uec-amd64-vmlinuz-virtual"
DEFAULT_IMAGE = "images/maverick-server-uec-amd64.img"

DOMAIN_EXISTS_ERROR = """Domain already exists (and could be running)! Manually shutdown and remove it with:
    virsh shutdown %(name)s (force with: virsh destroy %(name)s)
    virsh undefine %(name)s"""

def execute(args):
    with open(os.devnull, "r+") as f:
        subprocess.call(args, stdout=f, stderr=f)

def write_template(input_path, output_path, replacements):
    with open(input_path, "r") as input_file:
        with open(output_path, "w") as output_file:
            output_file.write(input_file.read() % replacements)

TTY_COLORS = {
	"blue":   34,
	"red":    31,
	"white":  39,
	"yellow": 33,
}
def tty_format(str, color="red", bold=True):
	tty_color = TTY_COLORS.get(color, TTY_COLORS["white"])
	tty_format = "1" if bold else "0"
	return "\033[%s;%sm%s\033[0m" % (tty_format, tty_color, str)

def log(msg):
	print(tty_format(msg, "blue", True))

def err(msg):
	print(tty_format(msg, "red", True))

# FIXME: Add global exception handler which prints exception value using err and stacktrace after that

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
		description='Builds a domain (= virtual machine) from a UEC image and deploys it to an LVM volume and libvirt',
		formatter_class=argparse.ArgumentDefaultsHelpFormatter
	)
    parser.add_argument('name', help='hostname and external name of domain')
    parser.add_argument('--vg', default='vms', help='name of LVM volume group')
    parser.add_argument('--size', default='5G', help='size of root partition, e.g., 1000M, 5G')
    parser.add_argument('--memory', default=1048576, help='size of RAM in bytes, e.g., 1048576, 2097152')
    parser.add_argument('--vcpus', default=2, help='number of virtual CPUs')
    parser.add_argument('--image', default=DEFAULT_IMAGE, help='reference root image file')
    parser.add_argument('--kernel', default=DEFAULT_KERNEL, help='kernel image to use')
    args = parser.parse_args()

    lv_path = os.path.join("/dev", args.vg, args.name)
    lv_mount = tempfile.mkdtemp("-uecbuild-%s-root" % args.name)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    replacements = {
        "name": args.name,
        "memory": args.memory,
        "vcpus": args.vcpus,
        "kernel": os.path.join(base_dir, args.kernel),
        "lv_path": lv_path,
    }

    # check preconditions
    if os.getuid() != 0:
        raise Exception("Root privileges required")

    if os.path.exists(lv_path):
        raise Exception("LV already exists! Manually remove it with: umount %s; lvremove %s" % (lv_path, lv_path))

    if execute(["virsh", "domstate", args.name]) == 0:
        raise Exception(DOMAIN_EXISTS_ERROR % {"name": args.name})

    # create lv
    log("Creating LV at %s" % lv_path)
    execute(["lvcreate", "-n", args.name, "-L", args.size, args.vg])

    # copy root to lv
    log("Copying root image to LV")
    execute(["dd", "if=%s" % args.image, "of=%s" % lv_path, "bs=1M"])

    # check & resize lv
    log("Checking and resizing LV")
    execute(["e2fsck", "-f", lv_path])
    execute(["resize2fs", lv_path])

    # mount lv
    log("Mounting LV")
    execute(["mount", lv_path, lv_mount])

    # write hostname
    log("Writing hostname to LV's /etc/hostname")
    with open(os.path.join(lv_mount, "etc", "hostname"), "w") as f:
        f.write(args.name + "\n")
    
    # write user-data & meta-data
    log("Writing user-data & meta-data to LV")
    nocloud_dir = os.path.join(lv_mount, "var", "lib", "cloud", "data", "cache", "nocloud")
    os.makedirs(nocloud_dir)
    for template in ["user-data", "meta-data"]:
        write_template(
            input_path=os.path.join(base_dir, "templates", template),
            output_path=os.path.join(nocloud_dir, template),
            replacements=replacements
        )

    # unmount LV & remove tempdir
    log("Unmounting LV")
    execute(["umount", lv_mount])
    execute(["rmdir", lv_mount])
    
    # create domain xml
    log("Adding domain to libvirt")
    domain_xml = tempfile.mkstemp("-uecbuild-%s.xml" % args.name)
    write_template(
        input_path=os.path.join(base_dir, "templates", "domain.xml"),
        output_path=domain_xml[1],
        replacements=replacements
    )

    # define domain xml
    execute(["virsh", "define", domain_xml[1]])

    # remove domain xml
    os.remove(domain_xml[1])

    # start domain
    log("Starting domain %s" % args.name)
    execute(["virsh", "start", args.name])
