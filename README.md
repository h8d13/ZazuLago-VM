# ZazuLago-VM

### Prereqs

KVM, Qemu, Iso Image

Run elevated as the nature of the script.

### How it works

1. Bit level manipulation to encrypt at rest based on a local secret

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

3. Custom features

        print("WARNING Options are shown bcs you are <at rest> but can be dangerous!")
        print(" r  : Refresh the key and logs (usually for new machines)")
        print(" d  : Delete the key totally. (Write it down, if you wish to re-use)")
        print(" brick  : Boot off the iso but keeping same disk.")
        print(" rdisk  : Resets the disk totally.")
        print(" exit  : Without encrypting back.")

----

Uses simple shell scripting to be configurable:
``` 
image_name = "./c/myvm.qcow2"
iso_name = "./d/deb.iso"
size = "60G"
ram = 8096
cores = 12
```

## Get it running:

Create a d folder for your isos. 
Create a c folder for your disk. 

Launch the script and type: `rdisk`. This creates a 60GB disk and exits. 
Launch the script again and `brick` this boots the ISO, when done with install you can close the Qemu window. 

It will open again! We want to be on the disk instead of ISO after initial-install. This let's you do post-install basics. 

Finally, now you can use these options or just any input to skip and run the normal encryption/decryption mechanisms.

----

## How does it encrypt?

hedgen2c usage:

```
./hedgen2c e hello.png helogoencrypted.png 420 && ./hedgen2c d helogoencrypted.png helogogodecrypted.png 420 && ./hedgen2c d helogoencrypted.png helogogocorruptedonpurpose.png 6969
``` 

Works off any number between 0 and 4294967295.

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


