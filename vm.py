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

## User might have to enable hidden files to see key file.

## Okay wild we have to make a C sript executable
## Its our main encryption function and it's fast
### You have to into the /lib directory with a terminal and run "chmod +x hedgen2c" in this case we check if done or do it. ##### Program will not work otherwise.

file_path = './lib/hedgen2c'
if os.access(file_path, os.X_OK):
    print("Already executable")
else:
    subprocess.run('chmod +x ./lib/hedgen2c', shell=True, capture_output=True)
    print(f"Made {file_path} executable.")

# Uses the magic number and can be used standalone for ANY file using any value between 0 and 4294967295
# Example usage: ./lib/hedgen2c d {image_name}.bin {image_name} {x}

# e/d for encryption/decryption
# source
# target (or inversely)
# x

### Now this is applied to a VM but you can truly do this for any file type as it works at lowest level.

### CONFIG HERE ##############
image_name = "./c/myvm.qcow2"
iso_name = "./d/deb.iso"
size = "60G"
ram = 8096
cores = 12

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
    command = f"qemu-system-x86_64 -enable-kvm -m {ram} -cpu host -smp {cores} -hda {image_name} -boot c"
    subprocess.run(command, shell=True)

###########################################
def get_magic_number():
    x = random.randint(9999, 4294967295)
    print(f'Magic number is: {x}')
    return x

y = uuid.uuid4()

def refresh_key():
    new_x = get_magic_number()
    save_key(new_x)
    print("Key has been refreshed successfully.")
    return new_x

def save_key(x):
    with open(".vmkey.local", "w") as f:
        f.write(str(x))

def load_key():
    with open(".vmkey.local", "r") as f:
        # Read only the first line (the key)
        return int(f.read().splitlines()[0].strip())

####################################################
# Basic integrity (checks stdout of: 'stat {image_name}')

def predecrypt():
    # Check if both files exist
    if not os.path.exists(".hash.local") or not os.path.exists(".vmkey.local"):
        print("Warning: Missing some files. First-time usage or files were deleted.")
        return

    # Load the key file data (contains launch/exit records)
    with open(".vmkey.local", "r") as f:
        key_data = f.read()

    # Load the hash file data (contains file stats from last encryption)
    with open(".hash.local", "r") as f:
        hash_data = f.read()

    in_times = re.findall(r'#I([\d-]+ [\d:]+)', key_data)
    out_times = re.findall(r'#O([\d-]+ [\d:]+)', key_data)
    uuids = re.findall(r'#([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', key_data)
    usernames = re.findall(r'#([a-zA-Z0-9_]+)(?=\n|$)', key_data)

    print("Individual sessions:")
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
                print(f"VM integrity verified: File timestamps match ({time_diff:.2f}s difference).")
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

        # Example #I for in #O for out
        """
        3902745918

        #I2025-02-27 18:05:59
        #2d27ddbb-16f5-4f30-9647-d4ab62833c4e
        #hadeon
        #O2025-02-27 18:07:16
        #2d27ddbb-16f5-4f30-9647-d4ab62833c4e
        #hadeon
        """

def postencrypt():
    # Get file information after encryption and save to .hash.local
    file_info = subprocess.run(f'stat {image_name}.bin', shell=True, capture_output=True, text=True)

    # Save this info to .hash.local for next integrity verification
    with open(".hash.local", "w") as f:
        f.write(file_info.stdout)
    print(f"Saved post encrypt hash information to .hash.local")

    # Close signature
    with open(".vmkey.local", "a") as f:
        f.write(f"\n#O{time.strftime('%Y-%m-%d %H:%M:%S')}\n#{y}\n#{username}")
    print(f"Saved post encrypt OUT signature to .vmkey.local")

def encrypt_exit(image_name, x):
    command = f"./lib/hedgen2c e {image_name} {image_name}.bin {x}"
    subprocess.run(command, shell=True)

    # Delete the unencrypted version after encryption
    os.remove(image_name)
    print(f"Removed unencrypted VM image: {image_name}")

    # Run post encrypt script
    postencrypt()


def main():
    if is_admin:
        # Check if .bin
        if os.path.exists(f"{image_name}.bin"):
            print(f"Enrypted {image_name}.bin detected.")
            # Load key and decrypt
            x = load_key()
            decrypt_launch(image_name, x)
            # Record the decryption operation
        else:
            # VM is not .bin (canceled midway) or first run
            if os.path.exists(".vmkey.local"):
                print (f"Non-encrypted {image_name} detected.")
                x = load_key()
            else:
                print (f"No key detected but found {image_name}. Creating original key")
                x = get_magic_number()
                save_key(x)

        print("WARNING Options are shown bcs you are <at rest> but can be dangerous!")
        print(" r  : Refresh the key and logs (usually for new machines)")
        print(" d  : Delete the key totally. (Write it down, if you wish to re-use)")
        print(" brick  : Boot off the iso but keeping same disk.")
        print(" rdisk  : Resets the disk totally.")
        print(" exit  : Without encrypting back.")

        choice = input("Any key to skip (boot normally) or choice: ")

        if choice.lower() == 'r':
            x = refresh_key()
            ## This is chill, we unencrypted and we can refresh key/logs safely.

        if choice.lower() == 'd':
            encrypt_exit(image_name, x)
            os.remove(".vmkey.local")
            print("Encrypted and deleted key and exiting. Hopefully you wrote it down. Whisper in your house alone, you might remember the numbers another day, Mason.")
            sys.exit()
            ## We cannot encrypt anymore without key, house is on fire.

        if choice.lower() == 'brick':
            boot_vm(image_name, iso_name)
            run_vm(image_name)
            sys.exit()

        if choice.lower() =='rdisk':
            create_reset_disk(image_name, size)
            sys.exit()

        # choice: snapshot machine > temp_name
            # duplicate disk
            # encrypt duplicated disk
            # launch temp_name

        if choice.lower() =='exit':
            sys.exit()

        # Run the VM
        run_vm(image_name)
        print ("VM Running...")

        # Encrypt the VM after use
        encrypt_exit(image_name, x)
        print("Fin.")
    else:
        print("Please run elevated.")

if __name__ == "__main__":
    main()
