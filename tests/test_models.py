import pytest
import os
import filecmp
from srmodel import shell_cmd

# def test_create_file(tmp_path):
#    # Create a subdirectory and a file within it
#    sub_dir = tmp_path / "my_subdir"  #
#    sub_dir.mkdir()  #
#
#    temp_file = sub_dir / "test_file.txt"  #
#    temp_file.write_text("Hello from pytest!")  #
#
#    assert temp_file.is_file()  #
#    assert temp_file.read_text() == "Hello from pytest!"  #


def test_hello_world(tmp_path):

    out_dir = tmp_path / "hello_world_sram"  #
    out_dir.mkdir()  #

    cwd = os.getcwd()
    print(f"cwd = {cwd}")

    success, result = shell_cmd(
        f"infer_code_gen -t tests/hello_world.tflite --output_dir {out_dir}"
    )
    # success, result = shell_cmd(f'infer_code_gen -h')
    # success, result = shell_cmd('infer_code_gen -t tests/hello_world.tflite')

    contents = os.listdir(out_dir)
    print(f"Contents of '{out_dir}':")
    for item in contents:
        print(item)

    compare_list = ["model.cc", "model_io.cc"]

    for fn in compare_list:
        assert filecmp.cmp(f"tests/golden/{fn}", f"{out_dir}/{fn}", shallow=False)

    print(result)
    # assert False

    # assert success == True, f'Failed to run vela command'
    # assert version == "3.7.0", f'Failed to run vela and get correct version'
