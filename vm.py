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

## PRECONFIG CHECK OR HELPERS
def ensure_dir_exists(directory):
    """Ensure that the directory exists, if not, create it."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory '{directory}' created.")
    else:
        print(f"Directory '{directory}' checked.")

def check_file_exists(file_path):
    """Check if a specific file exists."""
    return os.path.exists(file_path)

## Illustrative replace with your own values.
######## CONFIG HERE ##########
iso_dir_path = "./d/"
###############################
iso_name = "./d/alpine.iso"
#iso_name = "./d/antix.iso"
###############################
disks_dir_path = "./c/" # Used to list images
###############################
#image_name = "./c/myvm5.qcow2"     # > cachyos
image_name = "./c/myvm4.qcow2"      # > alpine
#image_name = "./c/myvm3.qcow2"     # > popos
#image_name = "./c/myvm2.qcow2"     # > antix
#image_name = "./c/myvm.qcow2"      # > deb

## Use more descriptive names for disks especially to recognize later or use right column. ## On linux file extensions don't mean shit, user could just mention ex: 'disk1' should still work.

size = "60G" ## Pre-alocation, will not take full size.
ram = 8096
cores = 8


###############################

def create_reset_disk(image_name, size):
    # Reset the current disk path
    command = f"qemu-img create -f qcow2 {image_name} {size}"
    subprocess.run(command, shell=True)

def create_disk(chosen_name, csize):
    # Create a new disk in C
    command = f"qemu-img create -f qcow2 ./c/{chosen_name} {csize}"
    subprocess.run(command, shell=True)

def boot_vm(image_name, iso_name):
    # Boot the VM from the ISO
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -cdrom {iso_name} -boot d"
    subprocess.run(command, shell=True)

def run_vm(image_name):
    # Run the VM
    print(f'Started {image_name}, with {cores} cores and {ram} M.')
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -boot c"
    ##
    subprocess.run(command, shell=True)

def boot_tailvm(image_name, iso_name):
    # Boot the VM from the ISO
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -cdrom {iso_name} -boot d  -serial mon:stdio -display none"
    subprocess.run(command, shell=True)

import signal

def run_tailvm(image_name):
    # Run the VM
    print(f"Started {image_name}, {cores} cores {ram} MB RAM.")
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -boot c -serial mon:stdio -display none"

    try:
        # Start the QEMU process
        process = subprocess.Popen(command, shell=True)

        # Poll the process for any interruptions or completion
        while True:
            # Check if the QEMU process is still running
            retcode = process.poll()
            if retcode is not None:  # If process has finished or terminated
                process.terminate()
                process.wait() # Wait for proper close
                break

            # Sleep for a bit to allow for periodic checks
            time.sleep(0.5)

    except Exception as e:
        print(f"Error while running QEMU: {e}")
    finally:
        print("Continuing with the script.")

def run_vncvm(image_name):
    # Run the VM
    print(f"Started {image_name}, with {cores} cores and {ram} MB of RAM.")
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -boot c -serial mon:stdio -display none -vnc :0"
    try:
        # Start the QEMU process
        process = subprocess.Popen(command, shell=True)

        # Poll the process for any interruptions or completion
        while True:
            # Check if the QEMU process is still running
            retcode = process.poll()
            if retcode is not None:  # If process has finished or terminated
                process.terminate()
                process.wait() # Wait for proper close
                break

            # Sleep for a bit to allow for periodic checks
            time.sleep(0.5)

    except Exception as e:
        print(f"Error while running QEMU: {e}")
    finally:
        print("Continuing with the script.")

def temp_disk(image_name):
    spec_chars = ['\\', '|', '/', '-']
    i = 0
    try:
        # Get the directory and filename separately
        dir_name = os.path.dirname(image_name)  # Directory part of the original path
        base_name = os.path.basename(image_name)  # Filename part of the original path

        # Create a temporary name by adding the random number to the base name
        temp_name = os.path.join(dir_name, f"{short_uuid}{base_name}")

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
                time.sleep(0.1)

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

def list_disks():
    files = os.listdir(disks_dir_path)

    for file in files:
        file_path = os.path.join(disks_dir_path, file)
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            size = file_info.st_size
            print(f"{file} - Size: {size} bytes")

def list_isos():
    files = os.listdir(iso_dir_path)

    # Loop through all files (`ls -l`)
    for file in files:
        file_path = os.path.join(iso_dir_path, file)
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            size = file_info.st_size
            print(f"{file} - Size: {size} bytes")

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

    print("Individual normal sesh on key:")
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

## Use I/O nice flags for performance

def decrypt_launch(image_name, x):
    predecrypt()

    command = f"ionice -c 1 -n 0 ./lib/hedgen2c d {image_name}.bin {image_name} {x}"
    subprocess.run(command, shell=True)
    os.remove(f'{image_name}.bin')


    hashed_image_name = hashlib.sha256(str(image_name).encode('utf-8')).hexdigest()[:8]

    # Launch signature
    with open(".vmkey.local", "a") as f:
        f.write(f"\n#I{time.strftime('%Y-%m-%d %H:%M:%S')}\n#{y}\n#{username}\n#{hashed_image_name}")

def encrypt_exit(image_name, x):
    command = f"ionice -c 1 -n 0 ./lib/hedgen2c e {image_name} {image_name}.bin {x}"
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
        ensure_dir_exists(disks_dir_path)
        ensure_dir_exists('./d')
        check_file_exists(image_name)

        # Check if .bin if yes load key and decrypt
        if os.path.exists(f"{image_name}.bin"):
            print(f"Enrypted {image_name}.bin detected.")
            x = load_key()
            decrypt_launch(image_name, x)
            # Record the decryption operation
        else:
            # VM is not .bin (canceled midway) or deleted files
            if os.path.exists(".vmkey.local"):
                print (f"No encrypted image detected.")

                ## Just load the key and proceed
                x = load_key()
            else:
                print (f"No key detected but found {image_name}.")
                ## Actual first run
                x = get_magic_number()
                print("Creating original key")
                save_key(x)

        print("Prescription v1.3.1")
        print(f"WARNING Options are shown bcs you <at rest> but\n can be dangerous! Press any key to boot normally.")
        print ("##########################################")
        print(" r       : Refresh key and logs")
        print(" ilist   : Prints ISOs in dir")
        print(" dlist   : Prints disks in dir")
        print(" cdisk   : Creates <name> <x_size>")
        print(" rdisk   : Resets current disk.")
        print(" brick   : Boot off the ISO + Restart")
        print(" taild   : Run headless w/ serial logs")
        print(" bootk   : Boot headless w/ serial logs")
        print(" vnck    : Boot headless w/ serial logs + VNC")
        print(" duck    : Temp disk from current")
        print(" dupk    : Perm disk from current")
        print(" potk    : Delete key and encrypt?!")
        print(" exit    : Without encrypting back")
        print ("##########################################")
        print (f"NOTE: For headless sesh make sure to shutdown\n properly using: 'poweroff' or similar dep on ISO.")

        choice = input(f"Any to continue or choice:\n")
        if choice.lower() == 'r':
            x = refresh_key()
            ## This is chill, we unencrypted and we can refresh key/logs safely, unless user fucked his configs, then it's corrupted lol. Try again loser.

        if choice.lower() == 'ilist':
            list_isos()
            sys.exit()

        if choice.lower() == 'dlist':
            list_disks()
            sys.exit()

        if choice.lower() == 'cdisk':
            # Ask the user for input in the format <name> <number>
            user_input = input("Enter name and size (ex:'myvm2 60'): ")

            # Split the input into name and number
            try:
                chosen_name, number = user_input.split()

                csize = f'"{number}G"'

                # Create the disk with the formatted size
                create_disk(chosen_name, csize)
                print(f"Disk {chosen_name} with size {csize} created.")
                sys.exit()

            except ValueError:
                print("Error: Please enter both name and size (e.g., 'disk1 60').")

        # User just wants to reset disk without specifying name/size
        # Destructive :D
        if choice.lower() =='rdisk':
            create_reset_disk(image_name, size)
            print(f"Formated disk {image_name} with {size}.")
            sys.exit()

        if choice.lower() == 'potk':
            encrypt_exit(image_name, x)
            print(f'Key {x} This your last chance.')
            os.remove(".vmkey.local")
            print("Encrypted and deleted key and exiting. Hopefully you wrote it down. Whisper in your house alone, you might remember the numbers another day, Mason.")
            sys.exit()
            ## We cannot encrypt anymore without key, house is on fire.
            ## Its also left encrypted which makes it funnier.

        # For this one we don't encrypt yet'
        if choice.lower() == 'brick':
            print(f"Boot: {iso_name}. Might trigger restart, auto boot to C on end.")
            boot_vm(image_name, iso_name)
            print(f"Run: {image_name}. For initial config.")
            run_vm(image_name)
            print(f"Initial config done. Exiting.")
            sys.exit()

##### Headless modes > Redirect to shell > Make sure user closes using poweroff/shutdown/reboot.

        if choice.lower() =='bootk':
            print(f"VM Bootk Boot Running... Waiting for restart.")
            boot_tailvm(image_name)
            print(f"Run: {image_name}. For initial config.")
            run_tailvm(image_name)
            sys.exit()

        if choice.lower() =='taild':
            print(f"VM Taild Running...")
            run_tailvm(image_name)
            encrypt_exit(image_name, x)
            sys.exit()

        if choice.lower() =='vnck':
            print(f"VM Vnck Running...")
            print(f"Use any VNC Viewer on :0")
            run_vncvm(image_name)
            encrypt_exit(image_name, x)
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

        # Same but do not delete
        if choice.lower() == "dupk":
            print("Running dupk command...")
            # Call temp_disk to copy the disk and get a name
            temp_name = temp_disk(image_name)
            print (f'Generating perm disk. Make sure to adapt Config after use.')
            print("VM Dupk Running...")
            run_vm(temp_name)
            print("VM Dupk Stopped.")
            #Encrypt the original again
            encrypt_exit(image_name, x)
            sys.exit()

        if choice.lower() =='exit':
            print("Exiting without encrypting.")
            sys.exit()

        print("Continuing with boot then encryption...")
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
## use fdisk, guestfish, partprobe, to probe the partitions
# and unmount when done, but this is useful to examine files.
# or using qemu image directly:
#qemu-img convert -O raw myvm.qcow2 myvm.raw
# or create a snapshot
#qemu-img create -f myvm.qcow2 myvmsnapshot.img 20G


## other useful qemu launch commands:
# run in bg: -daemonize
# redirect ouput: -serial mon:stdio
# redirect pulseaudio: -soundhw ac97


