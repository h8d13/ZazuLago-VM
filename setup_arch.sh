#!/bin/sh
# Main packages needed
pacman -S qemu-system-x86 qemu-img libvirt tigervnc
#qemu-full for other architectures 
# Verify KVM is available
lsmod | grep kvm
# Perms
usermod -a -G kvm $USER 

systemctl enable libvirtd.service
systemctl start libvirtd.service
