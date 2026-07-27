from .specifications import Specifications
from sxpat.annotatedGraph_backup import AnnotatedGraph_backup

class RefactoringVerifier:
    @staticmethod
    def verify_refactoring_generic(self, specs_obj: Specifications, old_finder, new_finder, iterations: int = 1):
        """
        Verifies whether the old and refactored implementations produce 
        the same results for subgraphs.
        """

        for i in range(1, iterations + 1):
            print(f"Verification Iteration {i}")
        
            # 1. Run the old (monolithic) version
            old_nodes = old_finder(self, specs_obj)
        
            # 2. Run the new (modularly refactored) version
            new_nodes = new_finder(specs_obj)
        
            # Applying the logic from the sketch:
            if len(old_nodes) != len(new_nodes):
                print(f"ERROR at iteration {i}: Different number of nodes! Old: {len(old_nodes)}, New: {len(new_nodes)}")
                raise RuntimeError("Refactoring verification failed: node count mismatch!")
            
            elif set(old_nodes) == set(new_nodes):
                print(f"Iteration {i}: OK - Subcircuits are identical.")
                continue
            
            else:
                print(f"Iteration {i}: Differences found in subgraph content (alternative path chosen).")
                break

    @classmethod
    def mode_1(cls, graph_instance, specs_obj: Specifications, iterations: int = 1):
        """Verifies refactoring for Mode 1."""
        cls.verify_refactoring_generic(
            graph_instance,
            specs_obj,
            old_finder=AnnotatedGraph_backup.find_subgraph,
            new_finder=graph_instance.find_subgraph,
            iterations=iterations
        )

    @classmethod
    def mode_2(cls, graph_instance, specs_obj: Specifications, iterations: int = 1):
        """Verifies refactoring for Mode 2 (Sensitivity)."""
        cls.verify_refactoring_generic(
            graph_instance,
            specs_obj,
            old_finder=AnnotatedGraph_backup.find_subgraph_sensitivity,
            new_finder=graph_instance.find_subgraph_sensitivity,
            iterations=iterations
        )

    @classmethod
    def mode_3(cls, graph_instance, specs_obj: Specifications, iterations: int = 1):
        """Verifies refactoring for Mode 3 (Sensitivity without IO constraints)."""
        cls.verify_refactoring_generic(
            graph_instance,
            specs_obj,
            old_finder=AnnotatedGraph_backup.find_subgraph_sensitivity_no_io_constraints,
            new_finder=graph_instance.find_subgraph_sensitivity_no_io_constraints,
            iterations=iterations
        )