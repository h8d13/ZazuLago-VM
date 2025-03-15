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
iso_name = "./d/void.iso"
###############################
disks_dir_path = "./c/"
###############################
#image_name = "./c/myvm5.qcow2"              # > alpine
image_name = "./c/myvm3.qcow2"             # > popos
#image_name = "./c/myvm3.qcow2"             # > antix
#image_name = "./c/myvm2.qcow2"             # > deb
#image_name = "./c/myvm1.qcow2"             # > tiny11
######### EXTERIOR (Optional) #
# For second disk, enable and check paths I mounted one up (relative)
enable_mp=False
mount_point="/media/usr/nvme/"

# If this is disabled mention an image above.
#image_name = f'{mount_point}myvm5.qcow2'    # > alpine ext

target_name = "sda1"
target=f'/dev/{target_name}'
########

### Micro help: CTRL S to save, CTRL Q to quit
