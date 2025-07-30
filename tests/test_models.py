import pytest
import os
import filecmp
from sr100_model_compiler import shell_cmd
from sr100_model_compiler import sr100_model_compiler


def compare_model_cc(expected_file, out_file):

    # Check for files
    assert os.path.exists(expected_file), f"{expected_file} not found"
    assert os.path.exists(out_file), f"{out_file} not found"
    # cwd = os.getcwd()
    # print(f"compare = {cwd}")

    # Read all the lines
    with open(expected_file, "r") as fp1:
        fp1_lines = fp1.readlines()
    with open(out_file, "r") as fp2:
        fp2_lines = fp2.readlines()

    # First check length of files
    assert len(fp1_lines) == len(fp2_lines)

    for loop1, line in enumerate(fp2_lines):

        if "Generated" in line or "Data" in line:
            next
        assert (
            line == fp2_lines[loop1]
        ), f"Failed comparing {loop1} : {line} != {fp2_lines[loop1]}"


@pytest.mark.parametrize(
    "model, model_loc, python_call",
    [
        ("hello_world", "sram", False),
        ("hello_world", "flash", False),
        ("model_256x480", "sram", False),
    ],
)
def test_model(tmp_path, model, model_loc, python_call):

    if python_call:
        model_dir = f"{model}_{model_loc}_python"
    else:
        model_dir = f"{model}_{model_loc}"
    out_dir = tmp_path / model_dir
    out_dir.mkdir()  #

    print(f'Building output in {out_dir}')

    if python_call:
        compiler = sr100_model_compiler()
        compiler(model=f'tests/models/{model}.tflite', output_dir=f'{out_dir}', model_loc=f'{model_loc}')
    else:
        success, result = shell_cmd(
            f"sr100_model_compiler -m tests/models/{model}.tflite --output-dir {out_dir} --model-loc {model_loc}"
        )

    # Check results
    compare_list = [
        f"{model}_summary_Ethos_U55_High_End_Embedded.csv",
        f"{model}_vela.tflite",
    ]

    for fn in compare_list:
        assert filecmp.cmp(
            f"tests/golden/{model_dir}/{fn}", f"{out_dir}/{fn}", shallow=False
        ), f"Testing file {fn}"

    # Check for created files
    compare_model_cc(f"{out_dir}/model.cc", f"tests/golden/{model_dir}/model.cc")
