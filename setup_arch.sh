#!/bin/sh
# Main packages needed
sudo pacman -S qemu-full virt-manager libvirt ebtables dnsmasq bridge-utils

# Verify KVM is available
lsmod | grep kvm

sudo systemctl enable libvirtd.service
sudo systemctl start libvirtd.service
