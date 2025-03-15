# Main needed
sudo apt install micro vncviewer qemu-system qemu-utils qemu-kvm libvirt-daemon-system libvirt-clients

# Info
lsmod | grep kvm
egrep -c '(vmx|svm)' /proc/cpuinfo
