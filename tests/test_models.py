import pytest
import os
import filecmp
from sr100_model_compiler import shell_cmd
from sr100_model_compiler import sr100_model_compiler


def compare_model_cc(expected_file, out_file):

    # Check for files
    assert os.path.exists(expected_file), f'{expected_file} not found'
    assert os.path.exists(out_file), f'{out_file} not found'
    #cwd = os.getcwd()
    #print(f"compare = {cwd}")

    # Read all the lines
    with open(expected_file, 'r') as fp1:
        fp1_lines = fp1.readlines()
    with open(out_file, 'r') as fp2:
        fp2_lines = fp2.readlines()

    # First check length of files
    assert len(fp1_lines) == len(fp2_lines)

    for loop1, line in enumerate(fp2_lines):
        if 'Generated' in line or 'Data' in line:
            continue
        assert line == fp2_lines[loop1], f'Failed comparing {loop1} : {line} != {fp2_lines[loop1]}'


def test_hello_world_sram(tmp_path):

    out_dir = tmp_path / "hello_world_sram"  #
    out_dir.mkdir()  #

    cwd = os.getcwd()
    print(f"cwd = {cwd}")

    success, result = shell_cmd(
        f"sr100_model_compiler -m tests/models/hello_world.tflite --output-dir {out_dir}"
    )

    # Check results
    compare_list = [
        "hello_world_summary_Ethos_U55_High_End_Embedded.csv",
        "hello_world_vela.tflite",
    ]
    for fn in compare_list:
        assert filecmp.cmp(
            f"tests/golden/hello_world_sram/{fn}", f"{out_dir}/{fn}", shallow=False
        )

    # Check for created files
    assert os.path.exists(f"{out_dir}/model.cc")
    assert os.path.exists(f"{out_dir}/model_io.cc")
    compare_model_cc(f"{out_dir}/model.cc", "tests/golden/hello_world_sram/model.cc")


def test_hello_world_sram_python(tmp_path):

    out_dir = tmp_path / "hello_world_sram_python"  #
    out_dir.mkdir()  #

    cwd = os.getcwd()
    print(f"cwd = {cwd}")

    sr100_model_compiler(model_file="tests/models/hello_world.tflite", output_dir=f"{out_dir}")
    # success, result = shell_cmd(
    #    f"sr100_model_compiler -m tests/hello_world.tflite --output-dir {out_dir}"
    # )

    # Check results
    compare_list = [
        "hello_world_summary_Ethos_U55_High_End_Embedded.csv",
        "hello_world_vela.tflite",
    ]
    for fn in compare_list:
        assert filecmp.cmp(
            f"tests/golden/hello_world_sram/{fn}", f"{out_dir}/{fn}", shallow=False
        )

    # Check for created files
    #assert os.path.exists(f"{out_dir}/model.cc")
    #assert os.path.exists(f"{out_dir}/model_io.cc")
    compare_model_cc(f"{out_dir}/model.cc", "tests/golden/hello_world_sram/model.cc")
