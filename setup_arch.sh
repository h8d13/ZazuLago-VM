#!/bin/sh
# Main packages needed
pacman -S qemu-full virt-manager libvirt ebtables dnsmasq bridge-utils

# Verify KVM is available
lsmod | grep kvm

systemctl enable libvirtd.service
systemctl start libvirtd.service
