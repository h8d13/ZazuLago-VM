# ZazuLago-VM

### Prereqs

KVM, Qemu, Iso Image

Run elevated as the nature of the script.

## Get it running:

Create a `d` folder for your ISOs 
And a `c` folder for your disk (`myvm0.qcow2,...`). 

Point to the right names in the config section of `vm.py` script. 

Use relative paths: 

```
image_name = "./c/myvm.qcow2"
iso_name = "./d/deb.iso"
```

Launch the script and type: `rdisk`. 

This creates a 60GB disk and exits (it will not take 60gb, only a provision number.)

Launch the script again and `brick` this boots the ISO, when done with install you can close the Qemu window. 
Program then boots you off C drive automatically. 

It will open again! We want to be on the disk instead of ISO after initial-install. This let's you do post-install basics. 

Finally, now you can use these options or just any input to skip and run the normal encryption/decryption mechanisms. 
Program detects automatically if it's encrypted or not using the `.bin` format.

----

## How does it encrypt?

./lib/hedgen2c usage:

```
- e/d flag
- source
- destination
- magic n°
```

```
./hedgen2c e hello.png helogoencrypted.png 420 && ./hedgen2c d helogoencrypted.png helogogodecrypted.png 420 && ./hedgen2c d helogoencrypted.png helogogocorruptedonpurpose.png 6969
``` 

## Demo

https://github.com/user-attachments/assets/dfe4d7fa-962c-4f8a-a551-0506bdbe4219

### How it works

1. Bit level manipulation to encrypt at rest based on a local secret

(15 Instructions; 5 XOR, 10 Custom instructions like reverse, shift, rotate; also bitmasking, jumping and a random sequence generated at encryption qnd decryption) 
With the only way to reverse is using the same magic number (`.key.local` file). 

```
Elevated: True
HEDGEN2C 1.3.1
Enrypted ./c/myvm2.qcow2.bin detected.
Individual sessions on key:
5
VM intcheck: Time matches: (1.00s difference).
Decrypting file: ./c/myvm2.qcow2.bin to ./c/myvm2.qcow2
Total size: 9327.25 MB
Progress: [====================] 100.0% (605.67 MB/s)
Finished! Processed 9327.25 MB in 15.40 seconds (605.67 MB/s)

 ```

2. Performs great on larger disks too:

```
Encrypting file: ./c/myvm.qcow2 to ./c/myvm.qcow2.bin
Total size: 11225.75 MB
Progress: [====================] 100.0% (601.74 MB/s)
Finished! Processed 11225.75 MB in 18.66 seconds (601.74 MB/s)
 ```


----
3. Backtacing
Works off any number between 0 and 4294967295. And logs on the same file. 
If you were to encrypt something and delete this file make sure to remember your magic number. 

        # Example #I for in #O for out : KEY AT THE TOP #####
        """
        3902745918
        #O2025-02-27 18:07:16
        #2d27ddbb-16f5-4f30-9647-d4ab62833c4e
        #hadeon
        """

Started off as a project where I wanted to see how it's possible to secure VMs through configuration. 
I will be posting more settings to do soon. 
Like tailing network, etc 

Uses simple shell scripting to be configurable (thanks to Qemu commands):
``` 
## Illustrative replace with your own values.
# d for ISOs
# c for Disks
# e for external

######## SPECS CONFIG #########
arch="x86_64"
ram = 8096
cores = 8
# For rdisk command / avergae sized btw
size = "60G"
# For vnck command
port = ":0"
# Sometimes depeding on your iso (can make smaller/larger, just pre-allocation, doesnt take the space directly)
###############################
iso_dir_path = "./d/"
###############################
iso_name = "./d/freebsd.iso"
###############################
disks_dir_path = "./c/"
###############################
# You can run 'rdisk' to format / create, destructive but useful. 
#image_name = "./c/myvm5.qcow2"                 # > alpine
#image_name = "./c/myvm4.qcow2"                 # > arch    
image_name = "./c/myvm3.qcow2"             # > alma
#image_name = "./c/myvm2.qcow2"                 # > deb
#image_name = "./c/myvm1.qcow2"                 # > tiny11
#image_name = "./c/myvm0.qcow2"                 # > freebsd

######### EXTERIOR (Optional) #
# For second disk, enable and check paths I mounted one up (relative)
enable_mp=False
mount_point="/media/usr/nvme/"

# If this is disabled mention an image above.
#image_name = f'{mount_point}myvm5.qcow2'    # > alpine ext

target_name = "sda1"
target=f'/dev/{target_name}'
########
```

## Full output examples with optional features
``` 
  └──╼ $sudo python3 vm.py
  Elevated: True
  HEDGEN2C 1.3.1
  Directory '../VMs/e' checked.
  Directory './c/' checked.
  Directory './d/' checked.
  DEBUG: ../VMs/e/myvm4.qcow2 C and ./d/alpine.iso D
  Enrypted ../VMs/e/myvm4.qcow2.bin detected.
  Individual normal sesh on key:
  45
  VM intcheck: Time matches: (0.00s difference).
  Decrypting file: ../VMs/e/myvm4.qcow2.bin to ../VMs/e/myvm4.qcow2
  Total size: 4390.69 MB
  Progress: [====================] 100.0% (711.31 MB/s)
  Finished! Processed 4390.69 MB in 6.17 seconds (711.31 MB/s)
  Prescription v1.3.1
  WARNING Options are shown bcs you <at rest> but
   can be dangerous! Press any key to boot normally.
  ##########################################
   r       : Refresh key and logs
   ilist   : Prints ISOs in dir
   dlist   : Prints disks in dir
   temk    : Print only temp disks
   cdisk   : Creates <name> <x_size>
   rdisk   : Resets current disk
   brick   : Boot off the ISO + Restart
   bootk   : Boot ISO headless w slogs
   taild   : Run headless w slogs
   vnck    : Run headless w slogs, VNC :0
   duck    : Temp disk from current
   mayk    : Maybe disk from current
   dupk    : Perm disk from current
   conk    : Boot ISO with attach /dev/sdb
   conkd   : Run with attach /dev/sdb
   potk    : Delete key and encrypt?!
   exit    : Without encrypting back
  ##########################################
  NOTE: For headless sesh make sure to shutdown
   properly using: 'poweroff' or similar dep on ISO.
  Any to continue normal DEC/ENC or choice:
   
  Continuing with boot then encryption...
  VM Running...
  Started VM, 8 cores and 8096 M.
```  
