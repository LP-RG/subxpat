# SubXPAT

## Setup
To prepare the system for execution you will need to follow a few steps:
1. Initial system setup:
    ```bash
    # bulk commands
    make setup-all # everything
    make setup     # everything except package dependencies

    # individual commands
    make sftw_dep    # install package dependencies
    make py_init     # create python environment
    make py_dep      # install/update requirements
    make folders_dep # create folders (WIP)
    make local_dep   # create input folders and local files
    ```
2. Activate the python environment:
    ```bash
    . venv/bin/activate
    ```

## Usage
You use the system by running the following command
```
python3 main.py exact-benchmark [options]
```

Here are all the arguments with their types and descriptions
| **Argument**                                           | **type**                             | **description**                                                        |
| ------------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------- |
| `exact-benchmark`                                      | file in `input/ver/`                 | Circuit to approximate.                                                |
| `--current-benchmark` <br> `--curr`                    | file in `input/ver/`                 | Approximated circuit to continue from.                                 |
| `--min-labeling`                                       |                                      | Nodes are weighted using their minimum error, instead of maximum error |
| `--partial-labeling`                                   |                                      | Assign weight only to relevant nodes                                   |
| `--extraction-mode` <br> `--mode`                      | { 1, 2, 3, 4, 5, 55, 11, 12 }        | Subgraph extraction algorithm to use                                   |
| `--input-max` <br> `--imax`                            | `int` > 0                            | Maximum allowed number of inputs to the subgraph                       |
| `--output-max` <br> `--omax`                           | `int` > 0                            | Maximum allowed number of outputs from the subgraph                    |
| `--max-sensitivity`                                    | `int` > 0                            | Maximum partitioning sensitivity                                       |
| `--min-subgraph-size`                                  | `int`                                | Minimum valid size for the subgraph                                    |
| `--num-subgraphs`                                      | `int` > 0                            | The number of attempts for subgraph extraction                         |
| `--subxpat`                                            |                                      | Run the system as SubXPAT instead of XPat                              |
| `--template`                                           | { nonshared, shared }                | Select template logic                                                  |
| `--literals-per-product` <br> `--max-lpp` <br> `--lpp` | `int` > 0                            | The max number of literals per product to use                          |
| `--products-per-output` <br> `--max-ppo` <br> `--ppo`  | `int` > 0                            | The max number of products per output to use                           |
| `--products-in-total` <br> `--max-pit` <br> `--pit`    | `int` > 0                            | The max number of products to use in total                             |
| `--wanted-models`                                      | `int` > 0                            | Wanted number of models to generate for each step                      |
| `--max-error` <br> `-e`                                | `int` > 0                            | The maximum allowable error                                            |
| `--error-partitioning` <br> `--epar`                   | { asc, desc, smart_asc, smart_desc } | The error partitioning algorithm to use                                |
| `--encoding`                                           | { z3int, z3bvec, qbf }               | The encoding to use in solving the approximation                       |
| `--timeout`                                            | `float` > 0 (default: 3h)            | The maximum time each cell is given to run in seconds                  |
| `--parallel`                                           |                                      | Run in parallel what is possilbe                                       |
| `--plot`                                               |                                      | The system will be run as plotter (DEPRECATED?)                        |
| `--clean`                                              |                                      | Reset the output folder before running                                 |
| `--help` <br> `-h`                                     |                                      | Show the help message and exit                                         |


### Other useful commands
- To remove temporary files and the virtual python environment:
    ```bash
    # all together
    make clean

    # individually
    make rm_cache # remove the pycache folders
    make rm_temp  # remove temporary files
    make rm_pyenv # remove the virtual python environment
    ```
- To display the program help:
    ```bash
    make help
    ```


## Known problems
- On Apple devices running M# architecture, you will have problems with some packages. \
    No support is given at the moment for this situation.
