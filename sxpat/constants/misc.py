from enum import Enum

# legacy solver status
#   all of these should be replaced with the enum approach
SAT = 'sat'
UNSAT = 'unsat'
UNKNOWN = 'unknown'


class SolverStatus(Enum):
    SAT = 'sat'
    UNSAT = 'unsat'
    UNKNOWN = 'unknown'


# node attributes
WEIGHT = 'weight'
