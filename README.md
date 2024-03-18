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
