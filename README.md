# srsdk-model-target
Builds tooling to take a LiteRT model and target the SRSDK for the SR100 series parts

## Links to the Vela compiler
https://review.mlplatform.org/plugins/gitiles/ml/ethos-u/ethos-u-vela

## Get the initial REPO
Get the repo and requirements

```
```

## Development flow

This builds the block with the local package and supports development + testing

```bash
# Clone the repo
git clone git@github.com:dgarrett-synaptics/srsdk-model-target.git
cd srsdk-model-target

# Create Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install toolkit with dev tools
pip install -e .[dev]

# Run the full test sweep
make all
```

### Running the DV Testcases

The instructions run the specific testcases

```
# Go to the DV directory in the docker execution
cd dv

# Run the full sweep 
./test_runner.py
... 

 806.00ns INFO     cocotb.regression                  **************************************************************************************
                                                        ** TEST                          STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        **************************************************************************************
                                                        ** test_custom_aes.test_aes128    PASS         806.00           0.02      42698.53  **
                                                        **************************************************************************************
                                                        ** TESTS=1 PASS=1 FAIL=0 SKIP=0                806.00           0.06      13334.12  **
                                                        **************************************************************************************
                                                        
- :0: Verilog $finish
INFO: Results file: /home/dgarrett/custom-aes-instructions/dv/sim_build/results.xml
Ran 1 tests with 0 failures
----------------------------------------
TEST PASSED
----------------------------------------

# Generate GTKwave database (in sim_build/dump.fst)
./test_runner.py --waves
```
### Run Full regression

```
./scripts/run_regression.sh
```

### Run formatting an Linting checks

```
# Run the Python formatting
./scripts/run_black.sh

# Run the LINT Checks
./scripts/run_pylint.sh
```

### GIT Workflow

In order to sequence multiple people working the project, please use "Pull Requests" for any changes to the main branch

```
# Make sure to pull the latest repo
git checkout main
git pull

# Create a branch to work on
git checkout -b feature_<my_new_feature>

# Do the git commits to track
git add <files>
git commit
# First push needs to create an origin
git push --set-upstream origin feature_<my_new_feature>
# Subsequent push can just push in
git push

# Merge in main before commits
git checkout main
git pull
git checkout feature_<my_new_feature>
git merge main

```


## Installed Tools Info