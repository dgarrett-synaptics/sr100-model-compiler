"""Main script to convert LiteRT models to the SR100 format"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
import datetime
import glob
import csv
from jinja2 import Environment, FileSystemLoader

# import platform
from .gen_model_cpp import generate_model_cpp
from .gen_input_expected_data import generate_input_expected_data
from .generate_micro_mutable_op_resolver_from_model import (
    generate_micro_mutable_ops_resolver_header,
)
from .utils import get_platform_path


# Function to expand wildcards in input paths
def expand_wildcards(file_paths):
    """expand wildcards"""

    expanded_paths = []
    for path in file_paths:
        # Check if the path contains a wildcard
        if "*" in path:
            # Expand the wildcard to actual file names and sort them
            expanded_file_paths = sorted(glob.glob(path))
            # Extend the list with the sorted paths
            expanded_paths.extend(expanded_file_paths)
        else:
            # If no wildcard, add the path as is
            expanded_paths.append(path)
    return expanded_paths


def gen_model_script(new_model_file, args, env, license_header):
    """Generate the model script outputs"""

    # Generate model C++ code
    generate_model_cpp(
        new_model_file,
        args.output_dir,
        args.namespace,
        args.model_loc,
        env,
        license_header,
    )

    # Generate micro mutable op resolver code
    common_path = os.path.dirname(new_model_file)
    if common_path == "":
        common_path = "."
    generate_micro_mutable_ops_resolver_header(
        common_path,
        [os.path.basename(new_model_file)],
        args.output_dir,
        args.namespace,
        license_header,
    )

    # Open the source file in read mode and the destination file in append mode
    src_fn = get_platform_path(
        args.output_dir + "/" + args.namespace + "_micro_mutable_op_resolver.hpp"
    )
    dest_fn = get_platform_path(args.output_dir + "/" + args.namespace + ".cc")
    with (
        open(src_fn, "r", encoding="utf-8") as source_file,
        open(dest_fn, "a", encoding="utf-8") as destination_file,
    ):
        # Read the content from the source file
        content = source_file.read()
        # Append the content to the destination file
        destination_file.write(content)

    # Generate on the original file
    generate_micro_mutable_ops_resolver_header(
        os.path.dirname(os.path.abspath(args.model_file)),
        [os.path.basename(args.model_file)],
        args.output_dir,
        "orig",
        license_header,
    )

    resolver_file = get_platform_path(
        args.output_dir + "/" + "orig_micro_mutable_op_resolver.hpp"
    )
    with open(resolver_file, "r", encoding="utf-8") as source_file:
        content = source_file.read()
        if "AddSynai" in content:
            synai_ethosu_op_found = 1
        elif "AddEthosU" in content:
            synai_ethosu_op_found = 2
        else:
            synai_ethosu_op_found = 0

    # Delete micro mutable op resolver file if it exists
    micro_mutable_file = get_platform_path(
        args.output_dir + "/" + args.namespace + "_micro_mutable_op_resolver.hpp"
    )
    if os.path.exists(micro_mutable_file):
        os.remove(micro_mutable_file)

    # Delete micro mutable op resolver file if it exists
    micro_mutable_file = get_platform_path(
        args.output_dir + "/" + "orig_micro_mutable_op_resolver.hpp"
    )
    if os.path.exists(micro_mutable_file):
        os.remove(micro_mutable_file)

    return synai_ethosu_op_found


def gen_inout_script(synai_ethosu_op_found, args, license_header):
    """Generate the inout script results"""

    # Check if AddSynai or AddEthosU is present in the contents of micro mutable op resolver
    if synai_ethosu_op_found > 0:
        if synai_ethosu_op_found == 1:
            print(
                "Synai custom op found in the model, skipping expected output generation"
            )
        else:
            print(
                "EthosU custom op found in the model, skipping expected output generation"
            )
    else:
        if args.input:
            generate_input_expected_data(
                args.model_file,
                args.output_dir,
                args.namespace,
                license_header,
                args.input,
            )
        else:
            generate_input_expected_data(
                args.model_file,
                args.output_dir,
                args.namespace,
                license_header,
            )


def process_args():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="Wrapper script to compile a TFLite model onto SR100 devices."
    )
    parser.add_argument(
        "-m", "--model-file", type=str, help="Path to TFLite model file", required=True
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        help="Directory to output generated files",
        default=".",
    )
    parser.add_argument(
        "-n",
        "--namespace",
        type=str,
        help="Namespace to use for generated code",
        default="model",
    )
    parser.add_argument(
        "-s",
        "--script",
        type=str,
        nargs="+",
        choices=["model", "inout"],
        help="Choose specific scripts to run, if not provided then run all scripts",
    )
    parser.add_argument(
        "-i", "--input", type=str, nargs="+", help="List of input npy/bin files"
    )
    parser.add_argument(
        "-c",
        "--compiler",
        type=str,
        choices=["vela", "synai", "none"],
        help="Choose target compiler",
        default="vela",
    )
    parser.add_argument(
        "--model-loc",
        type=str,
        choices=["sram", "flash"],
        help="Choose between in-memory SRAM or the model that is loaded from FLASH",
        default="sram",
        required=False,
    )
    parser.add_argument(
        "--arena-cache-size",
        type=int,
        help="Sets the model arena cache size in bytes",
    )
    parser.add_argument(
        "-v",
        "--verbose-all",
        action="store_true",
        help="Turns on verbose all for the compiler",
    )
    parser.add_argument(
        "--verbose-cycle-estimate",
        action="store_true",
        help="Turns on verbose cycle estimation",
    )
    parser.add_argument(
        "-p",
        "--optimize",
        type=str,
        choices=["Performance", "Size"],
        help="Choose optimization Type",
        default="Performance",
        required=False,
    )
    args = parser.parse_args()
    return args


def setup_input(args):
    """Process inputs"""

    # Expand wildcards in input file paths
    if args.input:
        args.input = expand_wildcards(args.input)

    if args.model_loc == "sram":
        memory_mode = "--memory-mode=Sram_Only"
    else:
        memory_mode = "--memory-mode=Shared_Sram"

    # Determine which scripts to run
    scripts_to_run = []
    if args.script:
        scripts_to_run = args.script
    else:
        scripts_to_run = ["model", "inout"]

    # Check if vela compilation is needed or not
    # If not that means the user is trying to run a non-vela model
    # In that case force the file name to no vela one
    file_name = os.path.basename(args.model_file)
    args.model_file = os.path.abspath(args.model_file)

    # Grab the summary file
    model_name = args.model_file.split("/")[-1].replace(".tflite", "")

    if args.compiler == "vela":
        new_tflite_file_name = file_name.split(".")[0] + "_vela.tflite"
    elif args.compiler == "synai":
        new_tflite_file_name = file_name.split(".")[0] + "_synai.tflite"
    elif args.compiler == "none":
        new_tflite_file_name = os.path.basename(args.model_file)
    else:
        new_tflite_file_name = os.path.basename(args.model_file)
        print("Invalid compiler option")
        sys.exit(1)

    new_model_file = get_platform_path(args.output_dir + "/" + new_tflite_file_name)

    return args, memory_mode, scripts_to_run, new_model_file, model_name


def get_vela_summary(output_dir, model_name):
    """
    Parses a CSV file into a list of dictionaries, where each dictionary
    represents a row and uses the header row as keys.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries, or an empty list if the file is not found.
    """

    # Grab the summary file
    summary_files = glob.glob(
        get_platform_path(f"{output_dir}/{model_name}_summary_Ethos_U55*.csv")
    )
    assert len(summary_files) == 1, "Failed to find summary file"
    summary_file = summary_files[0]

    data = []
    try:
        with open(summary_file, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: The file '{summary_file}' was not found.")

    if len(data) == 1:
        data = data[0]
    for key in data.keys():
        print(f"{key} = {data[key]}")
    return data


def compiler_main(args):
    """Main function with input args"""

    #if args is None:
    #    args = process_args()

    results = None

    synai_ethosu_op_found = 0
    args, memory_mode, scripts_to_run, new_model_file, model_name = setup_input(args)

    # Get the path to the directory containing this script
    script_dir = Path(__file__).parent

    # Initialize Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(script_dir / "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    header_template = env.get_template("header_template.txt")
    license_header = header_template.render(
        script_name=script_dir.name,
        file_name=Path(args.model_file).name,
        gen_time=datetime.datetime.now(),
        year=datetime.datetime.now().year,
    )

    print(f"memory_mode = {memory_mode}")
    if args.compiler == "vela":

        arm_config = get_platform_path("Arm/vela.ini")

        # Generate vela optimized model
        vela_params = [
            "vela",
            "--output-dir",
            args.output_dir,
            "--accelerator-config=ethos-u55-128",
            "--optimise=" + args.optimize,
            f"--config={arm_config}",
            memory_mode,
            "--system-config=Ethos_U55_High_End_Embedded",
        ]
        if args.arena_cache_size:
            vela_params.append(f"--arena-cache-size={args.arena_cache_size}")
        if args.verbose_cycle_estimate:
            vela_params.append("--verbose-cycle-estimate")
        if args.verbose_all:
            vela_params.append("--verbose-all")
        vela_params.append(args.model_file)

        print("************ VELA ************")
        subprocess.run(vela_params, check=True)
        print("********* END OF VELA *********")

        # Grab the summary file
        results = get_vela_summary(args.output_dir, model_name)

    elif args.compiler == "synai":
        # Generate synai optimized model
        print("*********** SYNAI **********")
        synai_params = [
            "synai",
            "--output-dir",
            os.path.dirname(args.model_file),
            args.model_file,
        ]
        subprocess.run(synai_params, check=True)
        print("******** END OF SYNAI ********")
    else:
        print("******* No Compilation *******")

    # Run the selected scripts
    for script in scripts_to_run:
        if script == "model":
            synai_ethosu_op_found = gen_model_script(
                new_model_file, args, env, license_header
            )
        elif script == "inout":
            gen_inout_script(synai_ethosu_op_found, args, license_header)

    return results

def sr100_model_compiler(**kwargs):
    """Python entry functions for the call"""

    # should derive defaults from argparse as well
    if "output_dir" not in kwargs:
        kwargs["output_dir"] = "."
    if "namespace" not in kwargs:
        kwargs["namespace"] = "model"
    if "script" not in kwargs:
        kwargs["script"] = ["model", "inout"]
    if "compiler" not in kwargs:
        kwargs["compiler"] = "vela"
    if "model_loc" not in kwargs:
        kwargs["model_loc"] = "sram"
    if "optimize" not in kwargs:
        kwargs["optimize"] = "Performance"
    if "input" not in kwargs:
        kwargs["input"] = []
    if "arena_cache_size" not in kwargs:
        kwargs["arena_cache_size"] = None
    if "verbose_all" not in kwargs:
        kwargs["verbose_all"] = None

    args = argparse.Namespace(**kwargs)
    return compiler_main(args)

def main():
    """Main for the command line compiler"""
    compiler_main(process_args())
    return 0

if __name__ == "__main__":
    main()
