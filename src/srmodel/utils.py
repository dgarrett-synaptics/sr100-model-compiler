import subprocess


def shell_cmd(cmd):
    """Run a shell command"""

    cmd_list = cmd.split(" ")
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"ERROR in command {e}")
        return False, "ERROR"

    return True, result.stdout.strip()
