# zazulago

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
WARNING Options are shown because you are <at rest> but can be dangerous
#command ###description
 r  : Refresh the key and logs.
 d  : Delete the key (Write it down, if you wish to re-use later)
 brick  : Boot off the iso but keeping same disk, then encrypts.
 rdisk  : Resets the disk totally. Boots, then encrypts.
 cdisk  : Copies the disk to VM2. Then boots this backup.
 ddisk  : Just runs VM2... Then encrypts.
 exit  : Just exits. Without encrypting back.
 ```

Even for larger files:

```
Encrypting file: ./c/myvm.qcow2 to ./c/myvm.qcow2.bin
Total size: 11225.75 MB
Progress: [====================] 100.0% (601.74 MB/s)
Finished! Processed 11225.75 MB in 18.66 seconds (601.74 MB/s)
 ```
