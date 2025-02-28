# ZazuLago-VM

### Prereqs

KVM, Qemu, Iso Image

Run elevated as the nature of the script.

### How it works

1. Bit level manipulation to encrypt at rest based on a local secret

(15 Instructions; 5 XOR, 10 Custom instructions like reverse, shift, rotate; also bitmasking, jumping and a random sequence generated at encryption qnd decryption) 
With the only way to reverse is using the same magic number (`.key.local` file). 

```
Elevated: True
Already executable
Enrypted ./c/myvm.qcow2.bin detected.
Individual sessions:
10
File timestamps match (0.00s difference).
Decrypting file: ./c/myvm.qcow2.bin to ./c/myvm.qcow2
Total size: 3446.88 MB
Progress: [====================] 100.0% (740.66 MB/s)
Finished! Processed 3446.88 MB in 4.65 seconds (740.66 MB/s)
 ```

2. Performs great on larger disks too:

```
Encrypting file: ./c/myvm.qcow2 to ./c/myvm.qcow2.bin
Total size: 11225.75 MB
Progress: [====================] 100.0% (601.74 MB/s)
Finished! Processed 11225.75 MB in 18.66 seconds (601.74 MB/s)
 ```

3. Custom thoughtful features
``` 
("WARNING Options are shown bcs you are <at rest> but can be dangerous!")

(" r  : Refresh the key and logs (usually for new machines)")
(" d  : Delete the key totally. (Write it down, if you wish to re-use)")
(" brick  : Boot off the iso but keeping same disk, then restart on C.")
(" rdisk  : Resets the disk totally.")
(" exit  : Without encrypting back.")

("Any key to skip (boot normally) or choice: ")
``` 

----
4. Backtacing
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
image_name = "./c/myvm.qcow2"
iso_name = "./d/deb.iso"
size = "60G"
ram = 8096
cores = 12
```

## Get it running:

Create a `d` folder for your ISOs and a `c` folder for your disk (`qcow2,...`). 

Point to the right names in the config section of `vm.py` script. (Use relative: `image_name = "./c/myvm.qcow2"
iso_name = "./d/deb.iso"`

Launch the script and type: `rdisk`. This creates a 60GB disk and exits (it will not take 60gb, only a provision number.)

Launch the script again and `brick` this boots the ISO, when done with install you can close the Qemu window. 
Program then boots you off C drive automatically. 

It will open again! We want to be on the disk instead of ISO after initial-install. This let's you do post-install basics. 

Finally, now you can use these options or just any input to skip and run the normal encryption/decryption mechanisms. 
Program detects automatically if it's encrypted or not using the `.bin` format.

----

## How does it encrypt?

hedgen2c usage:
- e/d flag
- source
- destination
- magic n°

```
./hedgen2c e hello.png helogoencrypted.png 420 && ./hedgen2c d helogoencrypted.png helogogodecrypted.png 420 && ./hedgen2c d helogoencrypted.png helogogocorruptedonpurpose.png 6969
``` 

## Demo

https://github.com/user-attachments/assets/dfe4d7fa-962c-4f8a-a551-0506bdbe4219
