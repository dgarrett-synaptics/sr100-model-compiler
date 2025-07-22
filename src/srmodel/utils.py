import subprocess
import platform

def shell_cmd(cmd):
    """Run a shell command"""

    cmd_list = cmd.split(" ")
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"ERROR in command {e}")
        return False, "ERROR"

    return True, result.stdout.strip()


def get_platform_path(unix_path):

    if platform.system() == "Windows":
        return unix_path.replace("/", "\\")
    else:
        return unix_path
