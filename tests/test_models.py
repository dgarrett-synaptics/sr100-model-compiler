import pytest
import os
import filecmp
from srmodel import shell_cmd


def test_hello_world_sram(tmp_path):

    out_dir = tmp_path / "hello_world_sram"  #
    out_dir.mkdir()  #

    cwd = os.getcwd()
    print(f"cwd = {cwd}")

    success, result = shell_cmd(
        f"infer_code_gen -t tests/hello_world.tflite --output_dir {out_dir}"
    )

    # Check results
    compare_list = ['hello_world_summary_Ethos_U55_High_End_Embedded.csv', 'hello_world_vela.tflite']
    for fn in compare_list:
        assert filecmp.cmp(f"tests/golden/hello_world_sram/{fn}", f"{out_dir}/{fn}", shallow=False)

    # Check for created files
    assert os.path.exists(f'{out_dir}/model.cc')
    assert os.path.exists(f'{out_dir}/model_io.cc')
