# SubXPAT

SubXPAT is a fully automated framework for approximate logic synthesis (ALS) based on the XPAT algorithm. It targets circuits described in Verilog and its core idea is to perform circuit rewriting in a way that is both local, i.e., is applied piece-wise to selected subcircuits, and extensive, i.e., systematically explores the design space for good solutions.

For details on the SubXPAT framework and the XPAT algorithm, please see our papers published at [IEEE TCAD] and [DSN-W'23].


## Dependencies

SubXPAT has been developed for a **Linux** environment and requires the manual installation of the following dependencies:

- [Python] (version 3.8 or higher)
- [Yosys] (using apt: `sudo apt install yosys`)
- [GraphViz] (you also need the headers for development, using apt: `sudo apt install graphviz graphviz-dev`)
- [OpenSTA] (using apt: `sudo apt install opensta`)

**Note:** the binaries of Yosys and OpenSTA should be added to your PATH.

### Optional

- Cell libraries (by default our cell library is `TODO`, this can be replaced by having the following dependencies and by using the `--cell-library` argument):
  - [SI2 `FreePDK45nm`][FreePDK45nm]


## Setup

To prepare the system for execution you will need to follow a few steps:

1. Initial system setup:
    ```bash
    # bulk commands
    make setup     # everything

    # individual commands
    make py_init     # create python environment
    make py_dep      # install/update requirements
    make local_dep   # create input folders and local files
    ```

2. Activate the python environment:
    ```bash
    . .venv/bin/activate
    ```


### Other useful commands

- To remove temporary files and the virtual python environment:
    ```bash
    # individually
    make rm_cache # remove the pycache folders
    make rm_temp  # remove temporary files
    make rm_pyenv # remove the virtual python environment
    make rm_data  # remove the output results

    # all together
    make clean     # rm_cache, rm_temp
    make clean-all # clean, rm_pyenv, rm_data
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

Here are all the parameters with their arguments and descriptions:
| **parameter**                                 | **argument**                            | **default value**                  | **description**                                                        |
| :-------------------------------------------: | --------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| `exact-benchmark`                             | Verilog file in `input/ver/`            |                                    | Circuit to approximate                                                 |
| `--current-benchmark` <br> `--curr`           | Verilog file in `input/ver/`            | the same as <br> `exact-benchmark` | Approximated circuit used to continue the execution                    |
| `--max-labeling`                              |                                         |                                    | Nodes are weighted using their maximum error, instead of minimum error |
| `--no-partial-labeling`                       |                                         |                                    | Weights are assigned to all nodes, not only the relevant ones          |
| `--extraction-mode` <br> `--mode`             | { 1, 2, 3, 4, 5, 55, 6, 11, 12 }        | 55                                 | Subgraph extraction algorithm to use                                   |
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
| `--max-error` <br> `-e`                       | `int` > 0                               |                                    | The maximum allowable error                                            |
| `--error-partitioning` <br> `--epar`          | { asc, desc, smart_asc, smart_desc }    | asc                                | The error partitioning algorithm to use                                |
| `--encoding`                                  | { z3int, z3bvec, z3dint, z3dbvec, qbf } | z3bvec                             | The encoding to use in solving                                         |
| `--cell-library`                              |                                         | `config/gscl45nm.lib`              | The cell library file to use in the metrics estimation                 |
| `--timeout`                                   | `float` > 0                             | 10800 (3h)                         | The maximum time each cell is given to run (in seconds)                |
| `--parallel`                                  |                                         |                                    | Run in parallel whenever possible                                      |
| `--clean`                                     |                                         |                                    | Reset the output folder before running                                 |
| `--help` <br> `-h`                            |                                         |                                    | Show the help message and exit                                         |

### Examples

To execute the framework with the XPAT algorithm in the standard configuration, run the following command:
```bash
python3 main.py adder_i8_o5 --max-lpp=8 --max-ppo=32 --max-error=16
```

To execute the framework with SubXPAT iterations, bit-vector logic encoding, and the defaults, run the following command:
```bash
python3 main.py adder_i8_o5 --subxpat --encoding=z3bvec --max-lpp=8 --max-ppo=10 --imax=6 --omax=3 --max-error=16
```

To execute the framework with SubXPAT iterations, integer logic encoding, subgraph extraction mode 5 (all sub-outputs weight must be less than the error threshold), maximum labeling, ..., run the following command:
```bash
python3 main.py adder_i8_o5 --subxpat --encoding=z3int --extraction-mode=5 --max-labeling --max-lpp=8 --max-ppo=10 --max-error=16 --imax=2 --omax=8
```


Once a command is finished executing, you can find the outputs in the following directories:

`output/csv/` contains the log of execution and all information for each iteration.
`output/ver/` contains the Verilog descriptions of all the approximate circuits found.
`output/gv/` contains the information of all the subgraphs that have been selected, in a visual form.


## Known limitations

- On Apple devices running M# architecture, you will have problems with some packages. \
  No support is given at the moment for this situation.


<!-- links -->
[IEEE TCAD]: https://doi.org/10.1109/TCAD.2025.3638267
[DSN-W'23]: https://doi.org/10.1109/DSN-W58399.2023.00049
[Python]: https://www.python.org/downloads
[Yosys]: https://github.com/YosysHQ/yosys
[GraphViz]: https://gitlab.com/graphviz/graphviz
[OpenSTA]: https://github.com/The-OpenROAD-Project/OpenSTA
[FreePDK45nm]: https://si2.org/open-cell-and-free-pdk-libraries/
