#!/usr/bin/bash

# Generate golden vectors
sr100_model_compiler -m models/hello_world.tflite --model-loc sram  --output-dir golden/hello_world_sram
sr100_model_compiler -m models/hello_world.tflite --model-loc flash --output-dir golden/hello_world_flash

# Test
sr100_model_compiler -m models/model_256x480.tflite --output-dir golden/model_256x480_sram --model-loc sram
sr100_model_compiler -m models/model_256x480.tflite --output-dir golden/model_256x480_flash --model-loc flash