# SubXPAT

SubXPAT is a fully automated framework for approximate logic synthesis (ALS) based on the XPAT algorithm. It targets circuits described in Verilog and its core idea is to perform circuit rewriting in a way that is both local, i.e., is applied piece-wise to selected subcircuits, and extensive, i.e., systematically explores the design space for good solutions.

For details on the SubXPAT framework and the XPAT algorithm, please see our papers published at [IEEE TCAD] and [DSN-W'23].
Details on template logic can be found on [arXiv][arXiv-shared].


## Dependencies

SubXPAT has been developed for a **Linux** environment and requires the following dependencies:

- [Python] (version 3.14 or higher)
- [Yosys] (using apt: `sudo apt install yosys`)
- [GraphViz] (you also need the headers for development, using apt: `sudo apt install graphviz graphviz-dev`)
- [OpenSTA] (using apt: `sudo apt install opensta`)

**Note:** the binaries of Yosys and OpenSTA should be added to your PATH.

On **macOS** (Apple silicon or Intel) only Python, Yosys and GraphViz are available as packages: OpenSTA is built from source by `make setup macos` into `.deps/`, together with everything else that is missing. See [macOS](#macos).

### Optional

- Cell libraries (by default our cell library is `TODO`, this can be replaced by having the following dependencies and by using the `--cell-library` argument):
  - [SI2 `FreePDK45nm`][FreePDK45nm]


## Setup

To prepare the system for execution you will need to follow a few steps:

1. Initial system setup:
    ```bash
    # bulk commands
    make setup        # python environment and python dependencies
    make setup macos  # [macOS] the above, plus yosys, graphviz and OpenSTA
    make setup all    # the above, plus cqesto (needed by `--encoding=qbf`)

    # individual commands
    make py_init     # create python environment
    make py_dep      # install/update requirements
    make macos       # native dependencies only (same as `make setup macos`)
    make all         # native dependencies and cqesto only (same as `make setup all`)
    ```

2. Activate the python environment:
    ```bash
    . .venv/bin/activate
    ```

### macOS

`make setup macos` installs `python@3.14`, `yosys`, `graphviz`, `swig` and `tcl-tk@8` with [Homebrew] and builds everything that has no package into `./.deps/`, so that no global installation is needed besides Homebrew itself:

| dependency | source | reason |
| :-- | :-- | :-- |
| Python, Yosys, GraphViz | Homebrew | packaged, no build required |
| OpenSTA (`sta`) | cloned and built into `.deps/opt/opensta` | not packaged: only Debian ships it |
| cqesto (`--encoding=qbf`) | cloned and built into `.deps/bin` by `make setup all` | not packaged anywhere |
| `swig`, `tcl-tk@8` | Homebrew | build dependencies of OpenSTA |

OpenSTA is built at version 2.0.17 (commit `c018cb21`, the revision Debian packages as `opensta`), so the metrics match the ones obtained on Linux. Two adjustments are required by the macOS build:

- the Tcl 8.6 headers and library are passed explicitly (`-DTCL_HEADER`, `-DTCL_LIB`), because OpenSTA's `findTcl` picks the system Tcl on macOS, and Tcl 9 is not supported (hence the `tcl-tk@8` keg instead of the default `tcl-tk` one);
- `tcl/StaException.i` is patched from `$function` to `$action`, because SWIG 4.3 and later no longer expand `$function` inside an `%exception` block.

The generated binaries are found automatically: `main.py` looks them up on the `PATH` first and then in `.deps/bin`, so no `PATH` modification is needed.

The macOS setup reproduces the Linux numbers. On the SubXPAT example below the run ends with

| Design | Area | Power | Delay | Error |
| :-- | --: | --: | --: | --: |
| Exact | 52.5616 | 1.84986e-05 | 0.229553 | 0 |
| gen_iter12_model0 | 6.5702 | 2.28038e-06 | 0.0611735 | 8 |

and `run_stats.csv` matches the Linux run row for row, with `circuit_power`/`circuit_delay` differing only past the eighth significant digit. The Yosys provided by Homebrew is 0.45 against the 0.52 of the Linux machines: the synthesized areas agree on the benchmarks tested, but pin a different version if a run has to be comparable with an older result.


### Other useful commands

- To remove temporary files and the virtual python environment:
    ```bash
    # individually
    make rm_cache # remove the pycache folders
    make rm_temp  # remove temporary files
    make rm_pyenv # remove the virtual python environment
    make rm_deps  # remove the locally built dependencies (.deps/)
    make rm_data  # remove the output results

    # all together
    make clean     # rm_cache, rm_temp
    make clean-all # clean, rm_pyenv, rm_deps, rm_data
    ```

- To display the program help:
    ```bash
    make help
    ```


## Usage

SubXPAT is used by running the following command:
```bash
python3 main.py exact-benchmark [options]
```

### Arguments

Here are all the parameters with their arguments and descriptions:

| **parameter**                                 | **argument**                            | **default value**                  | **description**                                                        |
| :-------------------------------------------: | --------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| `exact-benchmark`                             | `path` to Verilog file                  |                                    | Circuit to approximate                                                 |
| `--current-benchmark` <br> `--curr`           | `path` to Verilog file                  | the same as <br> `exact-benchmark` | Approximated circuit used to continue the execution                    |
| `--max-labeling`                              |                                         |                                    | Nodes are weighted using their maximum error, instead of minimum error |
| `--no-partial-labeling`                       |                                         |                                    | Weights are assigned to all nodes, not only the relevant ones          |
| `--extraction-mode` <br> `--mode`             | { 1, 2, 3, 4, 5, 55, 6, 11, 12, 42 }    | 55                                 | Subgraph extraction algorithm to use                                   |
| `--input-max` <br> `--imax`                   | `int` > 0                               |                                    | Maximum allowed number of inputs to the subgraph                       |
| `--output-max` <br> `--omax`                  | `int` > 0                               |                                    | Maximum allowed number of outputs from the subgraph                    |
| `--max-sensitivity`                           | `int` > 0                               |                                    | Maximum partitioning sensitivity                                       |
| `--min-subgraph-size`                         | `int` > 0                               |                                    | Minimum valid size for the subgraph                                    |
| `--num-subgraphs`                             | `int` > 0                               | 1                                  | The number of attempts for subgraph extraction                         |
| `--slash-to-kill`                             |                                         |                                    | Enable the slash pass for the first iteration                          |
| `--error-for-slash`                           | `int` > 0                               |                                    | The error to use for the slash pass                                    |
| `--subxpat`                                   |                                         |                                    | Run SubXPAT iteratively, instead of standard XPAT                      |
| `--constants`                                 | { never, always }                       | always                             | Usage of constants                                                     |
| `--constant-false`                            | { output, product }                     | output                             | Representation of false constants from the subgraph                    |
| `--template`                                  | { nonshared, shared }                   | nonshared                          | Template logic                                                         |
| `--max-lpp` <br> `--max-literals-per-product` | `int` > 0                               |                                    | The maximum number of literals per product                             |
| `--max-ppo` <br> `--max-products-per-output`  | `int` > 0                               |                                    | The maximum number of products per output                              |
| `--max-pit` <br> `--products-in-total`        | `int` > 0                               |                                    | The maximum number of products in total                                |
| `--wanted-models`                             | `int` > 0                               | 1                                  | Wanted number of models to generate at each step                       |
| `--encoding`                                  | { z3int, z3bvec, z3dint, z3dbvec, qbf } | z3bvec                             | The encoding to use in solving                                         |
| `--max-error` <br> `-e`                       | `int` > 0                               |                                    | The maximum allowable error                                            |
| `--error-partitioning` <br> `--epar`          | { asc, desc, smart_asc, smart_desc }    | asc                                | The error partitioning algorithm to use                                |
| `--output`                                    | `path` to folder                        | `output/`                          | The base directory for the output                                      |
| `--cell-library`                              | `path` to lib file                      | `config/gscl45nm.lib`              | The cell library file to use in the metrics estimation                 |
| `--cqesto`                                    | `path`                                  | `cqesto`                           | The path of the cqesto executable                                      |
| `--archive`                                   |                                         |                                    | If the generated files should be archived at the end of the execution  |
| `--debug`                                     |                                         | 10800 (3h)                         | The maximum time each cell is given to run (in seconds)                |
| `--timeout`                                   | `float` > 0                             | 10800 (3h)                         | The maximum time each cell is given to run (in seconds)                |
| `--parallel`                                  |                                         |                                    | Run in parallel whenever possible                                      |
| `--help` <br> `-h` `-?`                       |                                         |                                    | Show the help message and exit                                         |

### Results

Once a command is finished executing, you can find the outputs in the `output/{#ID}/` folder, where `#ID` is a unique id assigned to the run, printed at the beginning of the execution.

Inside the `output/{#ID}/` folder, the structure is as follow:
- `run_details.csv`: the file containing the run specifications, such as arguments and global timings
- `run_stats.csv`: the file containing details for every step of the execution
- `verilog/`: the folder containing all generated circuits in Verilog format

If the `--debug` flag is used, more folders will be available:
- `graphviz/`: the folder containing a visual representation of the selected subgraph of each iteration
- `scripts/`: the folder containing generated solver scripts
- `tmp/`: the folder containing other temporary or intermediate products

### Examples

To execute the framework with the XPAT algorithm in the standard configuration, run the following command:
```bash
python3 main.py benchmarks/v/adder_i8_o5.v --max-lpp=8 --max-ppo=32 --max-error=16
```

To execute the framework with SubXPAT iterations, bit-vector logic encoding, and the defaults, run the following command:
```bash
python3 main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3bvec --max-lpp=8 --max-ppo=10 --imax=6 --omax=3 --max-error=16
```

To execute the framework with SubXPAT iterations, integer logic encoding, subgraph extraction mode 5 (all sub-outputs weight must be less than the error threshold), maximum labeling, ..., run the following command:
```bash
python3 main.py benchmarks/v/adder_i8_o5.v --subxpat --encoding=z3int --extraction-mode=55 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8
```

## Known limitations

- On Apple devices running M# architecture, use `make setup macos`: the dependencies that Linux installs with apt have to be built from source. \
  No support is given for other setups.


<!-- links -->
[IEEE TCAD]: https://doi.org/10.1109/TCAD.2025.3638267
[DSN-W'23]: https://doi.org/10.1109/DSN-W58399.2023.00049
[arXiv-shared]: https://doi.org/10.48550/arXiv.2509.06162
[Python]: https://www.python.org/downloads
[Yosys]: https://github.com/YosysHQ/yosys
[GraphViz]: https://gitlab.com/graphviz/graphviz
[OpenSTA]: https://github.com/The-OpenROAD-Project/OpenSTA
[Homebrew]: https://brew.sh
[FreePDK45nm]: https://si2.org/open-cell-and-free-pdk-libraries/
