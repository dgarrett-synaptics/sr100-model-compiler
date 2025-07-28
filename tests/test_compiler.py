import pytest
from sr100_model_compiler import shell_cmd


def test_compiler():

    success, version = shell_cmd("vela --version")
    print(f"Run vela --version, found {success}:{version}")

    assert success == True, f"Failed to run vela command"
    assert version == "4.3.0", f"Failed to run vela and get correct version"
