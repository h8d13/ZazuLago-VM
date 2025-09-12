#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import uuid
import getpass
import hashlib
import datetime
import random
import re

from config import *

# Global state
username = getpass.getuser()
session_uuid = uuid.uuid4()
short_uuid = str(session_uuid.int)[:6]

def ensure_executable(path):
    """Ensure file is executable"""
    if not os.access(path, os.X_OK):
        subprocess.run(f'chmod +x {path}', shell=True, capture_output=True)

def ensure_dir(path):
    """Ensure directory exists"""
    if not os.path.exists(path):
        os.makedirs(path)

def spin_animation(duration=10):
    """Show spinning animation"""
    chars = ['\\', '|', '/', '-']
    start = time.time()
    i = 0
    while time.time() - start < duration:
        sys.stdout.write(f"\r{chars[i]}")
        sys.stdout.flush()
        i = (i + 1) % 4
        time.sleep(0.1)
    sys.stdout.flush()

def run_with_vnc(command):
    """Run QEMU with auto VNC viewer"""
    try:
        # Start QEMU
        qemu_proc = subprocess.Popen(command, shell=True)
        time.sleep(3)
        
        # Connect VNC viewer with retries
        for attempt in range(5):
            vnc_proc = subprocess.Popen(["vncviewer", ":0"])
            time.sleep(1)
            
            if vnc_proc.poll() is None:
                print("VNC connected!")
                break
            print(f"VNC attempt {attempt + 1} failed, retrying...")
            time.sleep(2)
        else:
            print("VNC failed to connect")
            qemu_proc.terminate()
            qemu_proc.wait()
            return
            
        # Wait for VNC to close
        while vnc_proc.poll() is None:
            time.sleep(0.5)
        print("VNC closed, continuing...")
        
        # Clean up
        qemu_proc.terminate()
        qemu_proc.wait()
        
    except Exception as e:
        print(f"Error: {e}")
        if 'qemu_proc' in locals():
            qemu_proc.terminate()
            qemu_proc.wait()

def run_headless(command):
    """Run QEMU headless (for serial log VMs)"""
    try:
        subprocess.run(command, shell=True)
    except Exception as e:
        print(f"Error: {e}")

def get_magic_number():
    """Generate encryption key"""
    return random.randint(9999, 4294967295)

def save_key(key):
    """Save encryption key"""
    with open(".vmkey.local", "w") as f:
        f.write(str(key))

def load_key():
    """Load encryption key"""
    try:
        with open(".vmkey.local", "r") as f:
            return int(f.read().splitlines()[0].strip())
    except FileNotFoundError:
        print("Encryption key not found.")
        sys.exit(1)

def verify_integrity():
    """Verify VM integrity before decryption"""
    if not os.path.exists(".vmkey.local") or not os.path.exists(".hash.local"):
        return
        
    with open(".vmkey.local", "r") as f:
        key_data = f.read()
    with open(".hash.local", "r") as f:
        hash_data = f.read()
    
    out_times = re.findall(r'#O([\d-]+ [\d:]+)', key_data)
    if not out_times:
        return
        
    last_shutdown = out_times[-1]
    modify_match = re.search(r'Modify: ([\d-]+ [\d:]+)\.', hash_data)
    
    if modify_match:
        file_time = modify_match.group(1)
        try:
            key_dt = datetime.datetime.strptime(last_shutdown, "%Y-%m-%d %H:%M:%S")
            hash_dt = datetime.datetime.strptime(file_time, "%Y-%m-%d %H:%M:%S")
            time_diff = abs((key_dt - hash_dt).total_seconds())
            
            if time_diff > 5:
                print(f"WARNING: Integrity check failed ({time_diff:.1f}s difference)")
                if input("Continue? (y/n): ").lower() != 'y':
                    sys.exit(1)
        except ValueError:
            print("WARNING: Could not verify timestamps")

def decrypt_vm(image, key):
    """Decrypt VM image"""
    verify_integrity()
    cmd = f"./lib/hedgen2c d {image}.bin {image} {key}"
    subprocess.run(cmd, shell=True)
    os.remove(f'{image}.bin')
    
    # Log launch
    hashed_name = hashlib.sha256(str(image).encode()).hexdigest()[:8]
    with open(".vmkey.local", "a") as f:
        f.write(f"\n#I{time.strftime('%Y-%m-%d %H:%M:%S')}\n#{session_uuid}\n#{username}\n#{hashed_name}")

def encrypt_vm(image, key):
    """Encrypt VM image"""
    cmd = f"./lib/hedgen2c e {image} {image}.bin {key}"
    subprocess.run(cmd, shell=True)
    os.remove(image)
    
    # Save file info for integrity check
    file_info = subprocess.run(f'stat {image}.bin', shell=True, capture_output=True, text=True)
    with open(".hash.local", "w") as f:
        f.write(file_info.stdout)
    
    # Log exit
    with open(".vmkey.local", "a") as f:
        f.write(f"\n#O{time.strftime('%Y-%m-%d %H:%M:%S')}\n#{session_uuid}\n#{username}")

def copy_disk(image):
    """Create temporary disk copy"""
    temp_name = os.path.join(os.path.dirname(image), f"{short_uuid}{os.path.basename(image)}")
    print(f"Copying {image} > {temp_name}...")
    
    if not os.path.exists(image):
        print(f"Error: {image} not found")
        sys.exit(1)
    
    proc = subprocess.Popen(["cp", image, temp_name])
    chars = ['\\', '|', '/', '-']
    i = 0
    while proc.poll() is None:
        sys.stdout.write(f"\r{chars[i]}")
        sys.stdout.flush()
        i = (i + 1) % 4
        time.sleep(0.1)
    
    print(f"\nCopied to {temp_name}")
    return temp_name

def generate_mac():
    """Generate random MAC address"""
    mac = "52:54:00:" + ":".join(f"{random.randint(0, 255):02x}" for _ in range(3))
    print(f'Generated MAC: {mac}')
    return mac

def qemu_cmd(image, **opts):
    """Build QEMU command"""
    cmd = f"qemu-system-{arch} -enable-kvm -m {ram} -cpu host -smp {cores}"
    
    if opts.get('hda'):
        cmd += f" -hda {opts['hda']}"
    if opts.get('cdrom'):
        cmd += f" -cdrom {opts['cdrom']}"
    if opts.get('boot'):
        cmd += f" -boot {opts['boot']}"
    if opts.get('serial'):
        cmd += f" -serial {opts['serial']}"
    if opts.get('display'):
        cmd += f" -display {opts['display']}"
    if opts.get('vnc'):
        cmd += f" -vnc {opts['vnc']}"
    if opts.get('usb_drive'):
        cmd += f" -usb -device usb-storage,drive=mydrive -drive file={opts['usb_drive']},format=raw,if=none,id=mydrive"
    if opts.get('network'):
        mac = opts['network']
        cmd += f" -netdev user,id=mynet0 -device e1000,netdev=mynet0,mac={mac}"
    
    return cmd

def show_menu():
    """Display menu options"""
    print("#" * 40)
    print("# VM MANAGER 2.0")
    print("#" * 40)
    print(" r       : Refresh key")
    print(f" rdisk   : Reset {image_name}")
    print(" dupk    : Permanent copy")
    print(" duck    : Temporary copy")
    print(" mayk    : Maybe save copy")
    print("=" * 40)
    print(" brick   : Boot ISO + Run")
    print(f" cupkd   : Boot ISO w/ {target}")
    print(f" cupk    : Run w/ {target}")
    print(" taild   : Headless w/ logs")
    print(" bootk   : Boot headless w/ logs")
    print(" macg    : Generate MAC + run")
    print(f" conkd   : Boot ISO w/ {target}")
    print(f" conk    : Run w/ {target}")
    print(" potk    : Delete key + encrypt")
    print(" exit    : Exit without encrypt")
    print("#" * 40)

def main():
    print(f'Elevated: {os.getuid() == 0}')
    
    # Setup
    ensure_executable('./lib/hedgen2c')
    ensure_dir('./c/')
    ensure_dir('./d/')
    
    # Load or create key
    if os.path.exists(f"{image_name}.bin"):
        print(f"Encrypted {image_name}.bin detected")
        key = load_key()
        decrypt_vm(image_name, key)
    elif os.path.exists(".vmkey.local"):
        key = load_key()
    else:
        key = get_magic_number()
        save_key(key)
        print("Created new key")
    
    # Show menu
    show_menu()
    choice = input("Choice (any key for default): ").strip().lower()
    
    # Handle choices
    if choice == 'r':
        key = get_magic_number()
        save_key(key)
        print("Key refreshed")
        return
        
    elif choice == 'rdisk':
        subprocess.run(f"qemu-img create -f qcow2 {image_name} {size}", shell=True)
        print(f"Reset disk {image_name}")
        return
        
    elif choice == 'potk':
        encrypt_vm(image_name, key)
        os.remove(".vmkey.local")
        print("Encrypted and deleted key")
        return
        
    elif choice == 'exit':
        print("Exiting without encryption")
        return
            
    elif choice == 'brick':
        print("Booting from ISO...")
        cmd = qemu_cmd(image_name, hda=image_name, cdrom=iso_name, boot='d', vnc=':0')
        run_with_vnc(cmd)
        print("Running VM...")
        cmd = qemu_cmd(image_name, hda=image_name, boot='c', vnc=':0')
        run_with_vnc(cmd)
        print("Setup complete")
        return
        
    elif choice == 'bootk':
        print("Headless boot...")
        cmd = qemu_cmd(image_name, hda=image_name, cdrom=iso_name, boot='d', 
                      serial='mon:stdio', display='none', vnc=':0')
        run_headless(cmd)
        cmd = qemu_cmd(image_name, hda=image_name, boot='c', 
                      serial='mon:stdio', display='none', vnc=':0')
        run_headless(cmd)
        
    elif choice == 'taild':
        print("Headless run...")
        cmd = qemu_cmd(image_name, hda=image_name, boot='c', 
                      serial='mon:stdio', display='none', vnc=':0')
        run_headless(cmd)
            
    elif choice == 'duck':
        temp_name = copy_disk(image_name)
        cmd = qemu_cmd(temp_name, hda=temp_name, boot='c', vnc=':0')
        run_with_vnc(cmd)
        os.remove(temp_name)
        print("Temp disk removed")
        
    elif choice == 'dupk':
        temp_name = copy_disk(image_name)
        cmd = qemu_cmd(temp_name, hda=temp_name, boot='c', vnc=':0')
        run_with_vnc(cmd)
        print(f"Permanent copy: {temp_name}")
        
    elif choice == 'mayk':
        temp_name = copy_disk(image_name)
        cmd = qemu_cmd(temp_name, hda=temp_name, boot='c', vnc=':0')
        run_with_vnc(cmd)
        save = input("Save? (enc/raw/no): ").lower()
        if save == 'enc':
            encrypt_vm(temp_name, key)
        elif save != 'raw':
            os.remove(temp_name)
                
    elif choice == 'macg':
        mac = generate_mac()
        cmd = qemu_cmd(image_name, hda=image_name, boot='c', vnc=':0', network=mac)
        run_with_vnc(cmd)
        
    elif choice == 'cupk':
        cmd = qemu_cmd(image_name, hda=image_name, boot='c', vnc=':0', usb_drive=target)
        run_with_vnc(cmd)
        
    elif choice == 'cupkd':
        cmd = qemu_cmd(image_name, hda=image_name, cdrom=iso_name, boot='d', vnc=':0', usb_drive=target)
        run_with_vnc(cmd)
        
    elif choice == 'conk':
        cmd = qemu_cmd(None, boot='c', vnc=':0', usb_drive=target)
        run_with_vnc(cmd)
        return
        
    elif choice == 'conkd':
        cmd = qemu_cmd(None, cdrom=iso_name, boot='d', vnc=':0', usb_drive=target)
        run_with_vnc(cmd)
        return
        
    else:
        # Default run
        print("Running VM...")
        cmd = qemu_cmd(image_name, hda=image_name, boot='c', vnc=':0')
        run_with_vnc(cmd)
    
    # Encrypt after use
    encrypt_vm(image_name, key)
    print("Done.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
