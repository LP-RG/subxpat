from Z3Log.z3solver import Z3solver as _Z3solver

from Z3Log.config.config import SINGLE, MONOTONIC


class Z3solver(_Z3solver):

    def label_gate(self, gate: str) -> int:
        # settings
        self.experiment = SINGLE
        self.set_strategy(MONOTONIC)
        CONSTANT_VALUE = False # this is not used in the labelling, only in names and stuff

        # run labelling
        self.create_pruned_z3pyscript_approximate([gate], CONSTANT_VALUE)
        self.run_z3pyscript_labeling()
        self.import_labels(CONSTANT_VALUE)

        # reset the solver list of scripts
        self.set_pyscript_files_for_labeling(list())

        # return weight
        return self.labels[gate]
