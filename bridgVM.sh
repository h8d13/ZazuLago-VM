#!/bin/sh

# VM configuration
VM_NAME="alpine-vm"
VM_DISK="alpine.qcow2"
VM_MEMORY="1024"
BRIDGE_NAME="br0"
HOST_INTERFACE="eth0"  # CHANGE TO DESIRED
MAC_ADDRESS="52:54:00:$(openssl rand -hex 3 | sed 's/\(..\)/\1:/g; s/:$//')"

# Create TAP device
echo "Setting up networking..."
TAP_DEVICE="tap0"
ip tuntap add dev $TAP_DEVICE mode tap

# Create bridge if it doesn't exist
if ! ip link show $BRIDGE_NAME >/dev/null 2>&1; then
    echo "Creating bridge $BRIDGE_NAME..."
    ip link add name $BRIDGE_NAME type bridge
    ip link set $HOST_INTERFACE master $BRIDGE_NAME
    ip link set $HOST_INTERFACE up
    ip link set $BRIDGE_NAME up
    
    # Save the original IP configuration to restore later
    IP_ADDR=$(ip -4 addr show dev $HOST_INTERFACE | grep inet | awk '{print $2}')
    if [ ! -z "$IP_ADDR" ]; then
        # Move IP from interface to bridge
        ip addr del $IP_ADDR dev $HOST_INTERFACE
        ip addr add $IP_ADDR dev $BRIDGE_NAME
    fi
fi

# Add TAP to bridge
ip link set $TAP_DEVICE master $BRIDGE_NAME
ip link set $TAP_DEVICE up

# Function to clean up when VM exits
cleanup() {
    echo "Cleaning up network..."
    ip link set $TAP_DEVICE nomaster
    ip link set $TAP_DEVICE down
    ip tuntap del dev $TAP_DEVICE mode tap
    echo "Cleanup complete"
    exit 0
}

# Set trap to ensure cleanup on script termination
trap cleanup EXIT INT TERM

# Start 
echo "Starting VM $VM_NAME..."
qemu-system-x86_64 \
  -name $VM_NAME \
  -m $VM_MEMORY \
  -hda $VM_DISK \
  -enable-kvm \
  -netdev tap,id=net0,ifname=$TAP_DEVICE,script=no,downscript=no \
  -device virtio-net-pci,netdev=net0,mac=$MAC_ADDRESS \
  "$@"

