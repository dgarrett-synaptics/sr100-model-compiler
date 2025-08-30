"""Main script to optimize a SR110 model"""

import argparse
import tempfile
from .sr100_model_compiler import sr100_model_compiler, sr100_check_model


def get_argparse_defaults(parser: argparse.ArgumentParser) -> dict:
    """
    Return a dictionary of all argparse defaults for the given parser.
    """
    return {
        action.dest: action.default
        for action in parser._actions  # pylint: disable=W0212
        if action.dest != "help"
    }


def model_optimizer_search(args):
    """Searches for the model that fits"""

    # Using TemporaryDirectory as a context manager for automatic cleanup
    results = None
    with tempfile.TemporaryDirectory() as tmpdirname:

        # You can perform operations within the temporary directory
        output_dir = f"{tmpdirname}"

        # Gets minimum arena cache size
        results_size = sr100_model_compiler(
            model_file=args.model_file, arena_cache_size=3072000, output_dir=output_dir
        )
        # Analyze the results
        weights_size = int(float(results_size["off_chip_flash_memory_used"]) * 1024)
        cache_size = int(float(results_size["sram_memory_used"]) * 1024)
        total_size = cache_size + weights_size

        # Determine the system configuration
        if total_size <= args.vmem_size:
            system_config = "sr100_npu_400MHz_all_vmem"
        elif total_size <= (args.vmem_size + args.lpmem_size):
            system_config = "sr100_npu_400MHz_tensor_vmem_weights_lpmem"
        else:
            system_config = "sr100_npu_400MHz_tensor_vmem_weights_flash66MHz"

        # Run the final results
        results = sr100_model_compiler(
            model_file=args.model_file,
            arena_cache_size=cache_size,
            system_config=system_config,
            output_dir=output_dir,
        )

    # Checks the SR100 mapping
    success, perf_data = sr100_check_model(results)

    return success, perf_data


def sr100_model_optimizer(**kwargs):
    """Python entry functions for the call"""

    # Get default args
    parser = get_argparser()
    arg_defaults = get_argparse_defaults(parser)

    # Update inputs with defaults
    for key in arg_defaults.keys():
        if key not in kwargs:
            kwargs[key] = arg_defaults[key]

    args = argparse.Namespace(**kwargs)
    return model_optimizer_search(args)


def get_argparser():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="Wrapper script to compile a TFLite model onto SR100 devices."
    )
    parser.add_argument(
        "-m", "--model-file", type=str, help="Path to TFLite model file", required=True
    )
    parser.add_argument(
        "--vmem-size", type=int, default=1536000, help="Set vmem size limit"
    )
    parser.add_argument(
        "--lpmem-size", type=int, default=1536000, help="Set lpmem size limit"
    )
    return parser


def main():
    """Main for the command line compiler"""
    parser = get_argparser()
    args = parser.parse_args()

    # Checks the SR100 mapping
    success, perf_data = model_optimizer_search(args)

    # Print performance data
    for key, value in perf_data.items():
        print(f"{key}: {value}")

    # Fine tune the model
    if success:
        returncode = 0
    else:
        returncode = 1
    return returncode


if __name__ == "__main__":
    main()
