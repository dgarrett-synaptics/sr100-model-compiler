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
        args.model_file_out,
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
        args.model_file_out,
        license_header,
    )

    # Open the source file in read mode and the destination file in append mode
    src_fn = get_platform_path(
        args.output_dir + "/" + args.model_file_out + "_micro_mutable_op_resolver.hpp"
    )
    dest_fn = get_platform_path(args.output_dir + "/" + args.model_file_out + ".cc")
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
        args.output_dir + "/" + args.model_file_out + "_micro_mutable_op_resolver.hpp"
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
                args.model_file_out,
                license_header,
                args.input,
            )
        else:
            generate_input_expected_data(
                args.model_file,
                args.output_dir,
                args.model_file_out,
                license_header,
            )


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


def get_vela_summary(summary_file):
    """
    Parses a CSV file into a list of dictionaries, where each dictionary
    represents a row and uses the header row as keys.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries, or an empty list if the file is not found.
    """

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


def sr100_default_config():
    """Gets the SR100 default config"""
    default_config = {"flash_size": 32e6, "sram_size": 3e6, "core_clock": 400e6}
    return default_config


def sr100_check_model(summary_file=None, results=None, config=None):
    """Check model on SR100 data file to see if it fits"""

    # Override config if needed
    if config is None:
        default_config = sr100_default_config()
    else:
        default_config = config

    # Get the success story
    success = True

    # Reads the Vela results file
    if results:
        results_dict = results
    else:
        results_dict = get_vela_summary(summary_file)

    if results_dict is None:
        success = False
        perf_data = {
            "sram_weights_size": 0,
            "sram_tensor_size": 0,
            "flash_weights_size": 0,
            "sram_size_limit": default_config["sram_size"],
            "sram_tensor_size_limit": 0,
            "flash_size_limit": default_config["flash_size"],
            "core_clock": default_config["core_clock"],
            "inference_per_sec": 0,
            "inference_time": 0,
        }

    else:

        # Setup inference scalar based on the clock
        inference_scalar = default_config["core_clock"] / float(
            results_dict["core_clock"]
        )

        # Read out SRAM and FLASH usage (convert to bytes)
        sram_weights_used = float(results_dict["on_chip_flash_memory_used"]) * 1024
        sram_tensors_used = float(results_dict["sram_memory_used"]) * 1024
        sram_used = sram_weights_used + sram_tensors_used
        flash_weights_used = float(results_dict["off_chip_flash_memory_used"]) * 1024

        # Check memory limits
        if flash_weights_used > default_config["flash_size"]:
            success = False
        if sram_used > default_config["sram_size"]:
            success = False

        # Return performance data
        perf_data = {
            "sram_weights_size": sram_weights_used,
            "sram_tensor_size": sram_tensors_used,
            "flash_weights_size": flash_weights_used,
            "sram_size_limit": default_config["sram_size"],
            "sram_tensor_size_limit": float(results_dict["arena_cache_size"]) * 1024,
            "flash_size_limit": default_config["flash_size"],
            "core_clock": default_config["core_clock"],
            "inference_per_sec": float(results_dict["inferences_per_second"])
            / inference_scalar,
            "inference_time": float(results_dict["inference_time"]) * inference_scalar,
        }

    return success, perf_data


def compiler_main(args):  # pylint: disable=R0914
    """Main function with input args"""

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

        # arm_config = get_platform_path("Arm/vela.ini")
        arm_config = get_platform_path(f"{script_dir}/config/sr100_system_config.ini")

        # Generate vela optimized model
        vela_params = [
            "vela",
            "--output-dir",
            args.output_dir,
            "--accelerator-config=ethos-u55-128",
            "--optimise=" + args.optimize,
            f"--config={arm_config}",
            memory_mode,
            f"--system-config={args.system_config}",
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
        model_name = args.model_file.split("/")[-1].replace(".tflite", "")
        summary_file = (
            f"{args.output_dir}/{model_name}_summary_{args.system_config}.csv"
        )
        results = get_vela_summary(summary_file)

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


def get_argparse_defaults(parser: argparse.ArgumentParser) -> dict:
    """
    Return a dictionary of all argparse defaults for the given parser.
    """
    return {
        action.dest: action.default
        for action in parser._actions  # pylint: disable=W0212
        if action.dest != "help"
    }


def sr100_model_compiler(**kwargs):
    """Python entry functions for the call"""

    # Get default args
    parser = get_argparser()
    arg_defaults = get_argparse_defaults(parser)

    # Update inputs with defaults
    for key in arg_defaults.keys():
        if key not in kwargs:
            kwargs[key] = arg_defaults[key]

    args = argparse.Namespace(**kwargs)
    return compiler_main(args)


def get_argparser():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="Wrapper script to compile a TFLite model onto SR100 devices."
    )
    parser.add_argument(
        "-m", "--model-file", type=str, help="Path to TFLite model file", required=True
    )
    parser.add_argument(
        "--system-config",
        type=str,
        default="sr100_npu_400MHz_16GBFLASH",
        help="Sets system config selection",
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
        "--model-file-out",
        type=str,
        help="Name of the output cc file for the model",
        default="model",
    )
    parser.add_argument(
        "-s",
        "--script",
        type=str,
        nargs="+",
        choices=["model", "inout"],
        default=["model"],
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
        default=1500000,
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

    return parser


def main():
    """Main for the command line compiler"""
    parser = get_argparser()
    args = parser.parse_args()

    # Runs the vela compiler
    results = compiler_main(args)

    # Checks the SR100 mapping
    success, perf_data = sr100_check_model(results=results)

    # Reports the
    if success:
        print(f"Successfully mapped {args.model_file} onto sr100")
        returncode = 0
    else:
        print(f"ERROR:: Failed to map {args.model_file} onto sr100")
        returncode = 1
    for key, value in perf_data.items():
        print(f"   {key} = {value}")

    return returncode


if __name__ == "__main__":
    main()
