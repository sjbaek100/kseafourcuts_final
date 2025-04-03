import subprocess
print(subprocess.run(["which", "gphoto2"], capture_output=True, text=True).stdout)
