import subprocess
import sys

class Hedgen2c:
    def __init__(self, mode, file1, file2, x):
        self.mode = mode
        self.file1 = file1
        self.file2 = file2
        self.x = x

    def run(self):
        # Construct the command based on the mode (either encrypt or decrypt)
        command = f"ionice -c 1 -n 0 ./lib/hedgen2c {self.mode} {self.file1} {self.file2} {self.x}"
        subprocess.run(command, shell=True)

if __name__ == "__main__":
    # Get arguments from the command line
    if len(sys.argv) != 5:
        print("Usage: python standalone.py [e/d] file1 file2 x")
        print("x being a number between 0 and 4294967295")
        sys.exit(1)

    mode = sys.argv[1]  # 'e' for encrypt, 'd' for decrypt
    file1 = sys.argv[2]
    file2 = sys.argv[3]
    x = sys.argv[4]

    # Validate the mode
    if mode not in ['e', 'd']:
        print("Error: Mode must be 'e' for encrypt or 'd' for decrypt.")
        sys.exit(1)

    # Create an instance of Hedgen2c and run the appropriate action
    hedgen = Hedgen2c(mode, file1, file2, x)
    hedgen.run()
