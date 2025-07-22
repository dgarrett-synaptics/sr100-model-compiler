import argparse
import os
import subprocess
from pathlib import Path
from gen_model_cpp import generate_model_cpp
from gen_input_expected_data import generate_input_expected_data
from generate_micro_mutable_op_resolver_from_model import generate_micro_mutable_ops_resolver_header
from jinja2 import Environment, FileSystemLoader
import datetime
import glob
import platform

# Function to expand wildcards in input paths
def expand_wildcards(file_paths):
    expanded_paths = []
    for path in file_paths:
        # Check if the path contains a wildcard
        if '*' in path:
            # Expand the wildcard to actual file names and sort them
            expanded_file_paths = sorted(glob.glob(path))
            # Extend the list with the sorted paths
            expanded_paths.extend(expanded_file_paths)
        else:
            # If no wildcard, add the path as is
            expanded_paths.append(path)
    return expanded_paths

# Parse command line arguments
parser = argparse.ArgumentParser(description='Wrapper script to run TFLite model generation scripts.')
parser.add_argument('-t', '--tflite_path', type=str, help='Path to TFLite model file', required=True)
parser.add_argument('-o', '--output_dir', type=str, help='Directory to output generated files', default='.')
parser.add_argument('-n', '--namespace', type=str, help='Namespace to use for generated code', default='model')
parser.add_argument('-s', '--script', type=str, nargs='+', choices=['model', 'inout'],
                    help='Choose specific scripts to run, if not provided then run all scripts, separated by spaces')
parser.add_argument('-i', '--input', type=str, nargs='+', help='List of input npy/bin files')
parser.add_argument('-c', '--compiler', type=str, choices=['vela', 'synai', 'none'], help='Choose target compiler', default='vela')
parser.add_argument('-tl', '--tflite_loc', type=int, choices=[1, 2], help="Choose an option (1: SRAM, 2: FLASH)", default=1, required=False)
parser.add_argument('-p', '--optimize', type=str, choices=['Performance', 'Size'], help="Choose optimization Type", default='Performance', required=False)
args = parser.parse_args()

synai_ethosu_op_found = 0

# Expand wildcards in input file paths
if args.input:
    args.input = expand_wildcards(args.input)

memory_mode = ''

if args.tflite_loc == 1:
    memory_mode = '--memory-mode=Sram_Only'
else:
    memory_mode = '--memory-mode=Shared_Sram'

# Determine which scripts to run
scripts_to_run = []
if args.script:
    scripts_to_run = args.script
else:
    scripts_to_run = ['model', 'inout']

# Check if vela compilation is needed or not
# If not that means the user is trying to run a non-vela model
# In that case force the file name to no vela one
file_name = os.path.basename(args.tflite_path)
args.tflite_path = os.path.abspath(args.tflite_path)

if args.compiler == 'vela':
    new_tflite_file_name = file_name.split('.')[0] + '_vela.tflite'
elif args.compiler == 'synai':
    new_tflite_file_name = file_name.split('.')[0] + '_synai.tflite'
elif args.compiler == 'none':
    new_tflite_file_name = os.path.basename(args.tflite_path)
else:
    print("Invalid compiler option")
    exit(1)

if platform.system() == "Windows":
    new_tflite_path = os.path.dirname(args.tflite_path) + "\\" + new_tflite_file_name
else:
    new_tflite_path = os.path.dirname(args.tflite_path) + "/" + new_tflite_file_name
# Get the path to the directory containing this script
script_dir = Path(__file__).parent

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(script_dir / 'templates'),
                  trim_blocks=True,
                  lstrip_blocks=True)
header_template = env.get_template("header_template.txt")
license_header = header_template.render(script_name=script_dir.name,
                             file_name=Path(args.tflite_path).name,
                             gen_time=datetime.datetime.now(),
                             year=datetime.datetime.now().year)

if args.compiler == 'vela':
    # Generate vela optimized model
    print("************ VELA ************")
    if platform.system() == "Windows":
        vela_params = ['vela', '--output-dir', os.path.dirname(args.tflite_path), '--accelerator-config=ethos-u55-128' , '--optimise=' + args.optimize, '--config=Arm\\vela.ini', memory_mode, '--system-config=Ethos_U55_High_End_Embedded', args.tflite_path]
    else:
        vela_params = ['vela', '--output-dir', os.path.dirname(args.tflite_path), '--accelerator-config=ethos-u55-128' , '--optimise=' + args.optimize, '--config=Arm/vela.ini', memory_mode, '--system-config=Ethos_U55_High_End_Embedded', args.tflite_path]
    subprocess.run(vela_params)
    print("********* END OF VELA *********")
elif args.compiler == 'synai':
    # Generate synai optimized model
    print("*********** SYNAI **********")
    synai_params = ['synai', '--output-dir', os.path.dirname(args.tflite_path), args.tflite_path]
    subprocess.run(synai_params)
    print("******** END OF SYNAI ********")
else:
    print("******* No Compilation *******")

# Run the selected scripts
for script in scripts_to_run:
    if script == 'model':
        # Generate model C++ code
        generate_model_cpp(new_tflite_path, args.output_dir, args.namespace, args.tflite_loc, license_header)

        # Generate micro mutable op resolver code
        common_path = os.path.dirname(new_tflite_path)
        if common_path == '':
            common_path = '.'
        generate_micro_mutable_ops_resolver_header(common_path, [os.path.basename(new_tflite_path)], args.output_dir,
                                                   args.namespace, license_header)
        
        # Open the source file in read mode and the destination file in append mode
        if platform.system() == "Windows":
            with open(args.output_dir + "\\" + args.namespace + '_micro_mutable_op_resolver.hpp', 'r') as source_file, \
                 open(args.output_dir + "\\" + args.namespace + '.cc', 'a') as destination_file:
                # Read the content from the source file
                content = source_file.read()
                # Append the content to the destination file
                destination_file.write(content)
        else:
            with open(args.output_dir + "/" + args.namespace + '_micro_mutable_op_resolver.hpp', 'r') as source_file, \
                open(args.output_dir + "/" + args.namespace + '.cc', 'a') as destination_file:
                # Read the content from the source file
                content = source_file.read()
                # Append the content to the destination file
                destination_file.write(content)

        generate_micro_mutable_ops_resolver_header(common_path, [os.path.basename(args.tflite_path)], args.output_dir,
                                                   "orig", license_header)
        
        if platform.system() == "Windows":
            with open(args.output_dir + "\\" + 'orig_micro_mutable_op_resolver.hpp', 'r') as source_file:
                content = source_file.read()
                if 'AddSynai' in content:
                    synai_ethosu_op_found = 1
                elif 'AddEthosU' in content:
                    synai_ethosu_op_found = 2
                else:
                    synai_ethosu_op_found = 0
        else:
            with open(args.output_dir + "/" + 'orig_micro_mutable_op_resolver.hpp', 'r') as source_file:
                content = source_file.read()
                if 'AddSynai' in content:
                    synai_ethosu_op_found = 1
                elif 'AddEthosU' in content:
                    synai_ethosu_op_found = 2
                else:
                    synai_ethosu_op_found = 0
        
        # Delete micro mutable op resolver file if it exists
        if platform.system() == "Windows":
            micro_mutable_file = args.output_dir + "\\" + args.namespace + '_micro_mutable_op_resolver.hpp'
        else:
            micro_mutable_file = args.output_dir + "/" + args.namespace + '_micro_mutable_op_resolver.hpp'
        if os.path.exists(micro_mutable_file):
            os.remove(micro_mutable_file)
        
        # Delete micro mutable op resolver file if it exists
        if platform.system() == "Windows":
            micro_mutable_file = args.output_dir + "\\" + args.namespace + '_micro_mutable_op_resolver.hpp'
        else:
            micro_mutable_file = args.output_dir + "/" + 'orig_micro_mutable_op_resolver.hpp'
        if os.path.exists(micro_mutable_file):
            os.remove(micro_mutable_file)


    elif script == 'inout':
        # Check if AddSynai or AddEthosU is present in the contents of micro mutable op resolver
        if synai_ethosu_op_found > 0:
            if synai_ethosu_op_found == 1:
                print("Synai custom op found in the model, skipping expected output generation")
            else:
                print("EthosU custom op found in the model, skipping expected output generation")
        else:
            if args.input:
                generate_input_expected_data(args.tflite_path, args.output_dir, args.namespace, license_header, args.input)
            else:
                generate_input_expected_data(args.tflite_path, args.output_dir, args.namespace, license_header)
