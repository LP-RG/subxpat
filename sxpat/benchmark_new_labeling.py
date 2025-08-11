from __future__ import annotations
import time
from typing import Dict, Tuple, List
import sys
from collections import defaultdict
from typing import Callable, Dict, Iterable, Iterator, List, Tuple, TypeVar
import dataclasses as dc
import glob
import os

from tabulate import tabulate
import functools as ft
import csv
import math
import networkx as nx
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Z3Log.config import path as z3logpath

from sxpat.labeling import labeling_explicit
from sxpat.metrics import MetricsEstimator
from sxpat.specifications import Specifications, TemplateType, ErrorPartitioningType
from sxpat.config import paths as sxpatpaths
from sxpat.config.config import *
from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.verification import erroreval_verification_wce
from sxpat.stats import Stats, sxpatconfig, Model
from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.templating import get_specialized as get_templater
from sxpat.solving import get_specialized as get_solver

from sxpat.converting import VerilogExporter
from sxpat.converting import iograph_from_legacy, sgraph_from_legacy
from sxpat.converting import set_bool_constants, prevent_combination

from sxpat.utils.print import pprint
from sxpat.labelling_weird import *

def get_graphs_from_folder(folder_path: str, max_graphs: int = None) -> List[str]:
    """
    Get list of graph names from folder.
    
    Args:
        folder_path: Path to folder containing graphs
        max_graphs: Maximum number of graphs to process (None for all)
    
    Returns:
        List of graph names (without extensions)
    """
    # Look for various graph file formats
    patterns = [
        os.path.join(folder_path, "*.gv"),
        os.path.join(folder_path, "*.v"), 
        os.path.join(folder_path, "*.verilog"),
        os.path.join(folder_path, "*.dot")
    ]
    
    graph_files = []
    for pattern in patterns:
        graph_files.extend(glob.glob(pattern))
    
    # Remove duplicates and extract base names
    graph_names = []
    seen_names = set()
    
    for file_path in graph_files:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        if base_name not in seen_names:
            graph_names.append(base_name)
            seen_names.add(base_name)
    
    # Limit number of graphs if specified
    if max_graphs:
        graph_names = graph_names[:max_graphs]
    
    print(f"Found {len(graph_names)} graphs to benchmark")
    return sorted(graph_names)

def benchmark_single_graph(graph_name: str) -> Dict:
    """
    Benchmark the three labeling methods on a single graph.
    
    Returns:
        Dictionary with timing, results, and comparison data for this graph4
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking graph: {graph_name}")
    print(f"{'='*60}")
    
    results = {
        'graph_name': graph_name,
        'methods': {}
    }
    
    try:
        graph = AnnotatedGraph(graph_name, is_clean=False)
        print(f"Graph loaded successfully")
    except Exception as e:
        print(f"Failed to load graph {graph_name}: {e}")
        return {'graph_name': graph_name, 'error': str(e)}
    
    # Method 1: labeling_explicit
    print("\n1. Testing labeling_explicit...")
    try:
        start_time = time.perf_counter()
        weights_explicit, _ = labeling_explicit(
            graph_name, graph_name,
            min_labeling=False,
            partial_labeling=False, 
            partial_cutoff=None,
            parallel=False
        )
        explicit_time = time.perf_counter() - start_time
        
        results['methods']['explicit'] = {
            'weights': weights_explicit,
            'time': explicit_time,
            'success': True,
            'error': None,
            'node_count': len(weights_explicit)
        }
        print(f"   Completed in {explicit_time:.4f}s ({len(weights_explicit)} nodes)")
        
    except Exception as e:
        results['methods']['explicit'] = {
            'weights': {},
            'time': float('inf'),
            'success': False,
            'error': str(e),
            'node_count': 0
        }
        print(f"   Failed: {e}")
    
    # Method 2: labeling_using_normal
    print("\n2. Testing labeling_using_normal...")
    try:
        start_time = time.perf_counter()
        weights_normal = labeling_using_normal(
            graph_name, graph_name,
            min_labeling=False,
            partial_labeling=False, 
            partial_cutoff=None,
            parallel=False
        )
        normal_time = time.perf_counter() - start_time
        
        results['methods']['normal'] = {
            'weights': weights_normal,
            'time': normal_time,
            'success': True,
            'error': None,
            'node_count': len(weights_normal)
        }
        print(f"   Completed in {normal_time:.4f}s ({len(weights_normal)} nodes)")
        
    except Exception as e:
        results['methods']['normal'] = {
            'weights': {},
            'time': float('inf'),
            'success': False,
            'error': str(e),
            'node_count': 0
        }
        print(f"   Failed: {e}")
    
    # Method 3: labeling_using_define_improved
    print("\n3. Testing labeling_using_define_improved...")
    try:
        start_time = time.perf_counter()
        weights_improved = labeling_using_define_improved(
            graph_name, graph_name,
            min_labeling=False,
            partial_labeling=False, 
            partial_cutoff=None,
            parallel=False,
            MODE_VECTOR=[True, True, False, False]
        )
        improved_time = time.perf_counter() - start_time
        
        results['methods']['improved'] = {
            'weights': weights_improved,
            'time': improved_time,
            'success': True,
            'error': None,
            'node_count': len(weights_improved)
        }
        print(f"   Completed in {improved_time:.4f}s ({len(weights_improved)} nodes)")
        
    except Exception as e:
        results['methods']['improved'] = {
            'weights': {},
            'time': float('inf'),
            'success': False,
            'error': str(e),
            'node_count': 0
        }
        print(f"   Failed: {e}")
    
    # Quick analysis for this graph
    analyze_single_graph(results)
    
    return results

def analyze_single_graph(result: Dict) -> None:
    """Analyze results for a single graph."""
    methods = result['methods']
    successful_methods = {k: v for k, v in methods.items() if v['success']}
    
    if len(successful_methods) == 0:
        print(f"   All methods failed for {result['graph_name']}")
        return
    
    # Speed ranking
    speed_ranking = sorted(successful_methods.items(), key=lambda x: x[1]['time'])
    print(f"\n   Speed ranking:")
    for i, (method, data) in enumerate(speed_ranking):
        print(f"     {i+1}. {method}: {data['time']:.4f}s")
        if i > 0:
            speedup = data['time'] / speed_ranking[0][1]['time']
            print(f"        ({speedup:.2f}x slower than fastest)")
    
    # Accuracy check (quick version)
    if len(successful_methods) >= 2:
        methods_list = list(successful_methods.keys())
        method1, method2 = methods_list[0], methods_list[1]
        weights1 = successful_methods[method1]['weights']
        weights2 = successful_methods[method2]['weights']
        
        if weights1.keys() == weights2.keys():
            identical = sum(1 for k in weights1.keys() if weights1[k] == weights2[k])
            total = len(weights1)
            accuracy = (identical / total) * 100 if total > 0 else 0
            print(f"   Accuracy: {method1} vs {method2}: {accuracy:.1f}% ({identical}/{total})")

def benchmark_multiple_graphs(folder_path: str, max_graphs: int = None) -> List[Dict]:
    """
    Benchmark multiple graphs and return comprehensive results.
    
    Args:
        folder_path: Path to folder containing graphs
        max_graphs: Maximum number of graphs to process
    
    Returns:
        List of results for each graph
    """
    graph_names = get_graphs_from_folder(folder_path, max_graphs)
    if not graph_names:
        print(f"No graphs found in {folder_path}")
        return []
    
    all_results = []
    
    for i, graph_name in enumerate(graph_names):
        print(f"\nProgress: {i+1}/{len(graph_names)}")
        try:
            result = benchmark_single_graph(graph_name)
            all_results.append(result)
        except Exception as e:
            print(f"Critical error processing {graph_name}: {e}")
            all_results.append({
                'graph_name': graph_name,
                'error': f"Critical error: {e}"
            })
    
    return all_results

def create_summary_report(all_results: List[Dict]) -> None:
    """Create a comprehensive summary report."""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE BENCHMARK SUMMARY")
    print(f"{'='*80}")
    
    # Filter out failed graph loads
    valid_results = [r for r in all_results if 'methods' in r]
    
    if not valid_results:
        print("No valid results to analyze")
        return
    
    # Speed summary table
    table_data = []
    method_totals = defaultdict(float)
    method_counts = defaultdict(int)
    
    for result in valid_results:
        row = [result['graph_name']]
        methods = result['methods']
        
        for method_name in ['explicit', 'normal', 'improved']:
            if method_name in methods and methods[method_name]['success']:
                time_val = methods[method_name]['time']
                row.append(f"{time_val:.4f}s")
                method_totals[method_name] += time_val
                method_counts[method_name] += 1
            else:
                row.append("FAILED")
        
        # Add speedup column
        times = []
        for method_name in ['explicit', 'normal', 'improved']:
            if method_name in methods and methods[method_name]['success']:
                times.append((method_name, methods[method_name]['time']))
        
        if len(times) >= 2:
            times.sort(key=lambda x: x[1])
            fastest_time = times[0][1]
            slowest_time = times[-1][1]
            speedup = slowest_time / fastest_time
            fastest_method = times[0][0]
            row.append(f"{speedup:.2f}x ({fastest_method} fastest)")
        else:
            row.append("N/A")
        
        table_data.append(row)
    
    # Add averages row
    avg_row = ["AVERAGE"]
    for method_name in ['explicit', 'normal', 'improved']:
        if method_counts[method_name] > 0:
            avg_time = method_totals[method_name] / method_counts[method_name]
            avg_row.append(f"{avg_time:.4f}s")
        else:
            avg_row.append("N/A")
    avg_row.append("")  # No speedup for average
    table_data.append(avg_row)
    
    headers = ['Graph', 'Explicit', 'Normal', 'Improved', 'Best Speedup']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Overall statistics
    print(f"\nOverall Statistics:")
    print(f"  Graphs processed: {len(valid_results)}")
    
    for method_name in ['explicit', 'normal', 'improved']:
        success_rate = (method_counts[method_name] / len(valid_results)) * 100
        avg_time = method_totals[method_name] / method_counts[method_name] if method_counts[method_name] > 0 else 0
        print(f"  {method_name.capitalize()}: {success_rate:.1f}% success rate, {avg_time:.4f}s average")
    
    # Best method per graph
    method_wins = defaultdict(int)
    for result in valid_results:
        methods = result['methods']
        successful_methods = {k: v for k, v in methods.items() if v['success']}
        
        if successful_methods:
            fastest = min(successful_methods.items(), key=lambda x: x[1]['time'])
            method_wins[fastest[0]] += 1
    
    print(f"\nMethod Performance:")
    for method, wins in method_wins.items():
        percentage = (wins / len(valid_results)) * 100
        print(f"  {method.capitalize()} was fastest: {wins}/{len(valid_results)} times ({percentage:.1f}%)")

def save_results_to_csv(all_results: List[Dict], filename: str = "benchmark_results.csv") -> None:
    """Save results to CSV file for further analysis."""
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header
        writer.writerow(['Graph', 'Method', 'Time(s)', 'Success', 'NodeCount', 'Error'])
        
        # Data
        for result in all_results:
            if 'methods' in result:
                for method_name, method_data in result['methods'].items():
                    writer.writerow([
                        result['graph_name'],
                        method_name,
                        method_data['time'] if method_data['success'] else 'FAILED',
                        method_data['success'],
                        method_data['node_count'],
                        method_data.get('error', '')
                    ])
            else:
                writer.writerow([result['graph_name'], 'ALL', 'FAILED', False, 0, result.get('error', '')])
    
    print(f"Results saved to {filename}")

def main():
    print(f"=" * 60)
    print(f" Multi-Graph Labeling Benchmark")
    print(f"=" * 60)
    
    # Configuration
    GRAPH_FOLDER = "input/ver"  
    MAX_GRAPHS = 1  # Set to None for all graphs, or specify a number
    
    if len(sys.argv) > 1:
        GRAPH_FOLDER = sys.argv[1]
    if len(sys.argv) > 2:
        MAX_GRAPHS = int(sys.argv[2])
    
    print(f"Graph folder: {GRAPH_FOLDER}")
    print(f"Max graphs: {MAX_GRAPHS if MAX_GRAPHS else 'All'}")
    
    # Run benchmarks
    all_results = benchmark_multiple_graphs(GRAPH_FOLDER, MAX_GRAPHS)
    
    # Generate reports
    create_summary_report(all_results)
    save_results_to_csv(all_results)
    
    print(f"\nBenchmark complete!")

if __name__ == "__main__":
    main()