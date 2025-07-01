from sxpat.utils.decorators import make_utility_class


__all__ = [
    'SolverConstants',
]


@make_utility_class
class SolverConstants:

    @make_utility_class
    class optimization:
        # reserved names
        identity: str = 'sc_optimization__identity'
        target: str = 'sc_optimization__target'
        constant: str = 'sc_optimization__constant'
        rule: str = 'sc_optimization__rule'
        constraint: str = 'sc_optimization__constraint'

    @make_utility_class
    class forall:
        # reserved names
        pass
