import subprocess
import random
import os
import sys
import os.path
import time
import uuid
import getpass
import re
import datetime
import hashlib

is_admin = os.getuid() == 0
print(f'Elevated: {is_admin}')
## Nice
username = getpass.getuser()
## Mark the local .vmkey.local with session user (ie: sharing image to users, common in VM setups)
y = uuid.uuid4()
short_uuid = str(y).replace('-', '')[:6]
## User might have to enable hidden files to see key file.

## Okay wild we have to make a C sript executable
### You have to into the /lib directory with a terminal and run ##"chmod +x hedgen2c" in this case we check if done or do it. #

file_path = './lib/hedgen2c'
if os.access(file_path, os.X_OK):
    print("HEDGEN2C 1.3.1")
else:
    subprocess.run('chmod +x ./lib/hedgen2c', shell=True, capture_output=True)
    print(f"Made {file_path} executable.")

# Uses the magic number and can be used standalone for ANY file using any value between 0 and 4294967295

### CONFIG HERE ##############
image_name = "./c/myvm2.qcow2"
## Use more descriptive names especially to recognize later.
iso_name = "./d/antix.iso"
size = "60G"
ram = 8096
cores = 8

def create_reset_disk(image_name, size):
    # Create a qcow2 image
    command = f"qemu-img create -f qcow2 {image_name} {size}"
    subprocess.run(command, shell=True)

def boot_vm(image_name, iso_name):
    # Boot the VM from the ISO
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -cdrom {iso_name} -boot d"
    subprocess.run(command, shell=True)

def run_vm(image_name):
    # Run the VM
    print(f'Starting {image_name}, with {cores} cores and {ram} m')
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -boot c"
    subprocess.run(command, shell=True)


def temp_disk(image_name):
    spec_chars = ['\\', '|', '/', '-']
    i = 0
    try:
        # Get the directory and filename separately
        dir_name = os.path.dirname(image_name)  # Directory part of the original path
        base_name = os.path.basename(image_name)  # Filename part of the original path

        # Create a temporary name by adding the random number to the base name
        temp_name = os.path.join(dir_name, f"{short_uuid}_{base_name}")

        print(f"Copying disk {image_name} to {temp_name}...")

        # Ensure that the image exists before attempting to copy it
        if not os.path.exists(image_name):
            print(f"Error: The disk image {image_name} does not exist.")
            sys.exit(1)
        else:
            process = subprocess.Popen(["cp", image_name, temp_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Spin animation during the copy process
            while process.poll() is None:
                sys.stdout.write(f"\r{spec_chars[i]}")
                sys.stdout.flush()
                i = (i + 1) % 4
                time.sleep(0.1)ˇ

        hashed_uuid = hashlib.sha256(str(y).encode('utf-8')).hexdigest()[:8]

        print(f"Disk copied successfully to {temp_name}.")
        with open(".vmkey.local", "a") as f:
            f.write(f"\n#C{hashed_uuid}{time.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"Saved post duck COPY sign to .vmkey.local")
        # Check if the copied image exists now
        if os.path.exists(temp_name):
            print(f"Confirmed: {temp_name} exists and ready.")
        else:
            print(f"Error: {temp_name} does not exist")

        return temp_name  # Return the name of the temporary disk

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while copying the disk: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


###########################################
def get_magic_number():
    x = random.randint(9999, 4294967295)
    print(f'Magic number is: {x}')
    return x

def save_key(x):
    with open(".vmkey.local", "w") as f:
        f.write(str(x))

def load_key():
    try:
        with open(".vmkey.local", "r") as f:
            # Read only the first line (the key)
            return int(f.read().splitlines()[0].strip())
    except FileNotFoundError:
        print("Could be that image is encrypted and key is not found.")
        sys.exit()

def refresh_key():
    new_x = get_magic_number()
    save_key(new_x)
    print("Key has been refreshed successfully.")
    return new_x
####################################################
# Basic integrity (checks stdout of: 'stat {image_name}')
### You can remove this and add any security feature you see fit.

def predecrypt():
    # Load the key file data (contains launch/exit records)
    with open(".vmkey.local", "r") as f:
        key_data = f.read()

    # Load the hash file data
    with open(".hash.local", "r") as f:
        hash_data = f.read()

    in_times = re.findall(r'#I([\d-]+ [\d:]+)', key_data)
    out_times = re.findall(r'#O([\d-]+ [\d:]+)', key_data)
    uuids = re.findall(r'#([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', key_data)
    usernames = re.findall(r'#([a-zA-Z0-9_]+)(?=\n|$)', key_data)

    print("Individual sessions on key:")
    print(len(out_times))

    if not out_times:
        print("INFO: No previous session closure found in key file.")
        return

    # Get the last VM shutdown time
    last_out_time = out_times[-1]

    # Extract the modification time from hash data
    modify_match = re.search(r'Modify: ([\d-]+ [\d:]+)\.', hash_data)

    if modify_match:
        file_modify_time = modify_match.group(1)

        # Convert string timestamps to datetime objects for comparison
        try:
            key_datetime = datetime.datetime.strptime(last_out_time, "%Y-%m-%d %H:%M:%S")
            hash_datetime = datetime.datetime.strptime(file_modify_time, "%Y-%m-%d %H:%M:%S")

            # Calculate time difference in seconds
            time_diff = abs((key_datetime - hash_datetime).total_seconds())

            # Allow a 5-second threshold for timestamp differences
            if time_diff > 5:
                print(f"WARNING: Hash timestamp ({file_modify_time}) differs from last VM shutdown ({last_out_time}) by {time_diff} seconds")
                print("The VM image may have been tampered with since last use.")
                proceed = input("Do you want to proceed anyway? (y/n): ")
                if proceed.lower() != 'y':
                    print("Operation aborted.")
                    exit(1)
            else:
                print(f"VM intcheck: Time matches: ({time_diff:.2f}s difference).")
        except ValueError as e:
            print(f"WARNING: Error parsing timestamps: {e}")
    else:
        print("WARNING: Could not parse modification time from hash file.")

def decrypt_launch(image_name, x):
    predecrypt()

    command = f"./lib/hedgen2c d {image_name}.bin {image_name} {x}"
    subprocess.run(command, shell=True)
    os.remove(f'{image_name}.bin')

    # Launch signature
    with open(".vmkey.local", "a") as f:
        f.write(f"\n#I{time.strftime('%Y-%m-%d %H:%M:%S')}\n#{y}\n#{username}")

def encrypt_exit(image_name, x):
    command = f"./lib/hedgen2c e {image_name} {image_name}.bin {x}"
    subprocess.run(command, shell=True)

    # Delete the unencrypted version after encryption
    os.remove(image_name)
    print(f"Removed unencrypted VM image: {image_name}")

    # Run post encrypt script
    postencrypt()

def postencrypt():
    # Get file information after encryption and save to .hash.local
    file_info = subprocess.run(f'stat {image_name}.bin', shell=True, capture_output=True, text=True)

    # Save this info to .hash.local for next integrity verification
    with open(".hash.local", "w") as f:
        f.write(file_info.stdout)
    print(f"Saved post enc info to .hash.local")

    # Close signature
    with open(".vmkey.local", "a") as f:
        f.write(f"\n#O{time.strftime('%Y-%m-%d %H:%M:%S')}\n#{y}\n#{username}")
    print(f"Saved post enc OUT sign to .vmkey.local")

############ FLOW CTRL

def main():
    if is_admin:
        # Check if .bin if yes load key and decrypt
        if os.path.exists(f"{image_name}.bin"):
            print(f"Enrypted {image_name}.bin detected.")
            x = load_key()
            decrypt_launch(image_name, x)
            # Record the decryption operation
        else:
            # VM is not .bin (canceled midway) or deleted files
            if os.path.exists(".vmkey.local"):
                print (f"Decrypted {image_name} detected.")

                ## Just load the key and proceed
                x = load_key()
            else:
                print (f"No key detected but found {image_name}.")
                ## Actual first run
                x = get_magic_number()
                print("Creating original key")
                save_key(x)

        print("WARNING Options are shown bcs you are <at rest> but can be dangerous! Press any key to just boot.")
        print ("##########################################")
        print(" r       : Refresh key and logs")
        print(" potk    : Delete key and encrypt?!")
        print(" rdisk   : Resets disk totally")
        print(" brick   : Boot off the iso, restart")
        print(" duck    : Temp disk from current")
        print(" exit    : Without encrypting back")
        print ("##########################################")

        choice = input(f"Any to continue or choice:\n")
        if choice.lower() == 'r':
            x = refresh_key()
            ## This is chill, we unencrypted and we can refresh key/logs safely, unless user fucked his configs, then it's corrupted lol. Try again loser.

        if choice.lower() == 'potk':
            encrypt_exit(image_name, x)
            print(f'{x} This your last chance.')
            os.remove(".vmkey.local")
            print("Encrypted and deleted key and exiting. Hopefully you wrote it down. Whisper in your house alone, you might remember the numbers another day, Mason.")
            sys.exit()
            ## We cannot encrypt anymore without key, house is on fire.
            ## Its also left encrypted which makes it funnier.

        # For this one we don't encrypt yet'
        if choice.lower() == 'brick':
            print(f"Boot: {iso_name}. Will trigger restart, will boot to C on close.")
            boot_vm(image_name, iso_name)
            print(f"Booting C {image_name}. Initial config.")
            run_vm(image_name)
            sys.exit()

        # Destructive :D
        if choice.lower() =='rdisk':
            create_reset_disk(image_name, size)
            print(f"Formated disk {image_name} with {size}.")
            sys.exit()

        # Cool asf
        if choice.lower() == "duck":
            print("Running duck command...")
            # Call temp_disk to copy the disk and get a name
            temp_name = temp_disk(image_name)
            print("VM Duck Running...")
            run_vm(temp_name)
            print("VM Duck Stopped.")
            os.remove(temp_name)
            print(f'Removed duck {temp_name} and exiting.')
            #Encrypt the original again
            encrypt_exit(image_name, x)
            sys.exit()

        if choice.lower() =='exit':
            print("Exiting without encrypting.")
            sys.exit()

        print("Continue with boot then encryption...")
        # No choice, run normally and encrypt.
        print ("VM Running...")
        run_vm(image_name)
        print ("VM Stopped.")

        # Encrypt the VM after use
        encrypt_exit(image_name, x)
        print("Fin.")
    else:
        print("Please run elevated.")

if __name__ == "__main__":
    main()


# Example #I for in #O for out. .key.local
"""
3902745918

#I2025-02-27 18:05:59
#2d27ddbb-16f5-4f30-9647-d4ab62833c4e
#hadeon
#O2025-02-27 18:07:16
#2d27ddbb-16f5-4f30-9647-d4ab62833c4e
#hadeon
"""


# Example usage: ./lib/hedgen2c d {image_name}.bin {image_name} {x}

# e/d for encryption/decryption
# source
# target (or inversely)
# x

### Now this is applied to a VM but you can truly do this for any file type as it works at lowest level.

# Some other useful commands:
#sudo tar -cf - ./c | zstd -o c.tar.zst
# └──╼ $zstd -d d.tar.zst --stdout | tar -xvf -
#./d/
#./d/antix.iso
#./d/deb.iso

### This is interesting for sharing and also keeps diretory structure healthy (in case there was multiple files) it's also incredibly fast.'

### You can also sudo apt-get install libguestfs-tools
### sudo guestmount -a myvm.qcow2 -m /dev/sdaX /mnt
# and unmount when done, but this is useful to examine files.
# or using qemu image directly:
#qemu-img convert -O raw myvm.qcow2 myvm.raw
