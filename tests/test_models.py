"""Testing different builds of models"""

import os
import filecmp
import pytest
from pathlib import Path
from sr100_model_compiler import shell_cmd
from sr100_model_compiler import sr100_model_compiler, sr100_check_model

#def compare_model_cc(expected_file, out_file):
#    """Compares the CC output files but ignores timestamp differences"""
#
#    # Check for files
#    assert os.path.exists(expected_file), f"{expected_file} not found"
#    assert os.path.exists(out_file), f"{out_file} not found"
#    # cwd = os.getcwd()
#    # print(f"compare = {cwd}")
#
#    # Read all the lines
#    with open(expected_file, "r", encoding="utf-8") as fp1:
#        fp1_lines = fp1.readlines()
#    with open(out_file, "r", encoding="utf-8") as fp2:
#        fp2_lines = fp2.readlines()
#
#    # First check length of files
#    assert len(fp1_lines) == len(fp2_lines)
#
#    for loop1, line in enumerate(fp2_lines):
#
#        if not "Date" in line:
#            assert (
#                line == fp2_lines[loop1]
#            ), f"Failed comparing {loop1} : {line} != {fp2_lines[loop1]}"
#
#
#@pytest.mark.parametrize(
#    "model, model_loc, python_call",
#    [
#        ("hello_world", "sram", False),
#        ("hello_world", "flash", False),
#        ("model_256x480", "sram", False),
#    ],
#)

def test_model_compiler(tmp_path, model, model_loc, model_file_out):
    """builds a model and tests outputs"""

    #model = 'tests/models/uc_person_classification/models/uc_person_classification_flash(448x640).tflite'
    #model = 'tests/models/uc_person_classification/person_classification_256x448.tflite'

    # Get model name to build directory
    if '/' in model:
        model_name = model.split('/')[-1].replace('.tflite', '')
    else:
        model_name = model.replace('.tflite', '')
    model_dir = f'{model_name}_{model_loc}'

    # Building output directory
    out_dir = tmp_path / model_dir
    out_dir.mkdir(parents=True,exist_ok=True)  #
    print(f"Building output in {out_dir}")

    # Run the comparison
    results = sr100_model_compiler(
        model_file=model,
        output_dir=f"{out_dir}",
        model_loc=f"{model_loc}",
        model_file_out='model_wqvfa'
    )

    if not sr100_check_model(results=results):
        assert False, 'Model does not fit'

    #success, _ = shell_cmd(
    #      f"sr100_model_compiler -m {model}"
    #      f" --output-dir {out_dir} --model-loc {model_loc}"
    #)
    #print(f"success = {success}")
    # assert success is True, f'Failed to run command on {model}'
    #assert False
#
#    # Check results
#    compare_list = [
#        f"{model}_summary_Ethos_U55_400MHz_SRAM_3.2_GBs_Flash_3.2_GBs.csv",
#        f"{model}_vela.tflite",
#    ]
#
#    for fn in compare_list:
#        assert filecmp.cmp(
#            f"tests/golden/{model_dir}/{fn}", f"{out_dir}/{fn}", shallow=False
#        ), f"Testing file {fn}"
#
#    # Check for created files
#    compare_model_cc(f"{out_dir}/model.cc", f"tests/golden/{model_dir}/model.cc")
#
if __name__ == "__main__":

    #model = 'tests/models/uc_person_classification/models/uc_person_classification_flash(448x640).tflite'

    # Test SRAM version
    model = 'tests/models/uc_person_classification/person_classification_256x448.tflite'
    model_loc = 'sram'
    model_file_out = 'model_wvqga'
    test_model_compiler(Path('tmp_build'),model, model_loc, model_file_out)

    #model = 'tests/models/uc_person_classification/models/uc_person_classification_flash(448x640).tflite'

    # Test FLASH version
    model = 'tests/models/uc_person_classification/person_classification_448x640.tflite'
    model_loc = 'flash'
    model_file_out = 'model_vga'
    test_model_compiler(Path('tmp_build'),model, model_loc, model_file_out)

    # Building output directory
    #out_dir = tmp_path / model_dir
    #out_dir.mkdir(parents=True,exist_ok=True)  #
    #print(f"Building output in {out_dir}")




    #test_classification(Path('./tmp_build'))