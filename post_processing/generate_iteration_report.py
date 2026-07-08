from __future__ import annotations

import argparse
import ast
import importlib
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def load_svg2rlg():
    try:
        module = importlib.import_module("svglib.svglib")
        return getattr(module, "svg2rlg", None)
    except Exception:
        return None


@dataclass
class CellResult:
    row: int
    col: int
    status: str
    models_found: Optional[int] = None


@dataclass
class IterationRecord:
    iteration: int
    et: int
    available_error: int
    benchmark: str = ""
    out_node: Optional[int] = None
    ascendants: List[str] = field(default_factory=list)
    node_partition: List[str] = field(default_factory=list)
    subgraph_path: Optional[Path] = None
    cells: List[CellResult] = field(default_factory=list)
    exact_metrics: Optional[Tuple[str, str, str, str]] = None
    approx_metrics: Optional[Tuple[str, str, str, str]] = None

    @property
    def has_sat(self) -> bool:
        return any(cell.status == "SAT" for cell in self.cells)

    @property
    def first_sat_cell(self) -> Optional[CellResult]:
        for cell in self.cells:
            if cell.status == "SAT":
                return cell
        return None


ITERATION_RE = re.compile(r"iteration\s+(\d+)\s+with\s+et\s+(\d+),\s+available\s+error\s+(\d+)")
BENCHMARK_RE = re.compile(r"benchmark\s+(.+)")
EXTRACTING_RE = re.compile(r"^\d+$")
CELL_RE = re.compile(r"Cell\((\d+),(\d+)\)\s+at\s+iteration\s+(\d+)\s+->\s+(SAT|UNSAT|UNKNOWN|DOMINATED)(?:\s+\((\d+)\s+models\s+found\))?")
SUBGRAPH_RE = re.compile(r"subgraph exported at\s+(.+\.gv)")
LIST_RE = re.compile(r"^\s*\[.*\]\s*$")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SPEC_REPR_START_RE = re.compile(r"^specs_obj\s*=\s*Specifications\(")


def _format_spec_value(value: object) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    return str(value)


def parse_specs_from_log_text(log_text: str) -> Dict[str, str]:
    specs_lines: List[str] = []
    capturing = False
    paren_depth = 0

    for raw_line in log_text.splitlines():
        line = ANSI_RE.sub("", raw_line.rstrip("\n"))
        if not capturing:
            if SPEC_REPR_START_RE.match(line.strip()):
                capturing = True
                paren_depth = line.count("(") - line.count(")")
                continue

        if capturing:
            stripped = line.strip()
            if stripped == ")":
                break
            specs_lines.append(line)
            paren_depth += line.count("(") - line.count(")")
            if paren_depth <= 0:
                break

    specs: Dict[str, str] = {}
    for raw_line in specs_lines:
        line = raw_line.strip().rstrip(",")
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value_text = line.split("=", 1)
        key = key.strip()
        value_text = value_text.strip()
        try:
            value = ast.literal_eval(value_text)
        except Exception:
            value = value_text
        specs[key] = _format_spec_value(value)

    return specs


def append_specs_page(story: List, specs: Dict[str, str], title_style: ParagraphStyle, info_style: ParagraphStyle) -> None:
    story.append(Paragraph("Specifications", title_style))
    if not specs:
        story.append(Paragraph("<b>Specifications:</b> not found in log", info_style))
        story.append(PageBreak())
        return

    used_keys = set()
    for key, value in specs.items():
        story.append(Paragraph(f"<b>{key}:</b> {value}", info_style))
        used_keys.add(key)

    story.append(Paragraph("In graphs green nodes indicates the cone of the output node, red nodes are the selected node partitions ", info_style))

    story.append(PageBreak())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a PDF report for SubXPAT iterations")
    parser.add_argument("--log", default="nohup.log", help="Path to subxpat log file")
    parser.add_argument("--benchmark", default="mul_i16_o16", help="Benchmark name used in output/gv")
    parser.add_argument("--full-graph", default=None, help="Path to the complete GraphViz file")
    parser.add_argument("--subgraph-dir", default="output/gv/subgraphs", help="Directory with iteration subgraph .gv files")
    parser.add_argument("--output", default=None, help="Destination PDF path")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary rendered files")
    parser.add_argument("--image-format", choices=["png", "svg"], default="svg", help="Graph render format for report images")
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N iterations from the log")
    return parser.parse_args()


def parse_list(text: str) -> List[str]:
    try:
        value = ast.literal_eval(text)
    except Exception:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def parse_metrics_line(line: str) -> Optional[Tuple[str, str, str, str]]:
    stripped = line.strip()
    if not stripped:
        return None
    parts = stripped.split()
    if len(parts) < 5:
        return None
    if parts[0] not in {"Exact", "None_E"}:
        return None
    return parts[0], parts[1], parts[2], parts[3]


def parse_log(log_path: Path) -> Tuple[List[IterationRecord], bool]:
    records: List[IterationRecord] = []
    current: Optional[IterationRecord] = None
    saw_exhausted = False
    pending_out_node: Optional[int] = None

    with log_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = ANSI_RE.sub("", raw_line.rstrip("\n"))

            match = ITERATION_RE.search(line)
            if match:
                if current is not None:
                    records.append(current)
                current = IterationRecord(
                    iteration=int(match.group(1)),
                    et=int(match.group(2)),
                    available_error=int(match.group(3)),
                    out_node=pending_out_node,
                )
                pending_out_node = None
                continue

            if "The error space is exhausted!" in line:
                saw_exhausted = True

            match = EXTRACTING_RE.search(line)
            if match:
                pending_out_node = int(match.group(0))
                continue

            # Handle logs that indicate a skipped output node, e.g. "Skipping node out2".
            # If the skipped node matches the current output node or the pending one,
            # advance it by 1 so subsequent ascendant lists refer to the correct output.
            skip_match = re.search(r"Skipping node out(\d+)", line)
            if skip_match:
                try:
                    skipped = int(skip_match.group(1))
                except Exception:
                    skipped = None
                if skipped is not None:
                    if current is not None and current.out_node == skipped:
                        current.out_node = skipped + 1
                    elif pending_out_node is not None and pending_out_node == skipped:
                        pending_out_node = pending_out_node + 1
                continue

            # Parse a verbose ascendants line like: "all ascendants = ['g1','g2',...]"
            if "all ascendants" in line and "[" in line:
                idx = line.find("[")
                parsed = parse_list(line[idx:])
                if parsed:
                    current.ascendants = parsed
                continue

            if current is None:
                continue

            match = BENCHMARK_RE.search(line)
            if match:
                current.benchmark = match.group(1).strip()
                continue

            if line.startswith("[") and LIST_RE.match(line):
                parsed = parse_list(line)
                if parsed and not current.ascendants:
                    current.ascendants = parsed
                continue

            if line.startswith("node partition ="):
                current.node_partition = parse_list(line.split("=", 1)[1].strip())
                continue

            match = SUBGRAPH_RE.search(line)
            if match:
                current.subgraph_path = Path(match.group(1).strip())
                continue

            match = CELL_RE.search(line)
            if match:
                cell = CellResult(
                    row=int(match.group(1)),
                    col=int(match.group(2)),
                    status=match.group(4),
                    models_found=int(match.group(5)) if match.group(5) else None,
                )
                current.cells.append(cell)
                continue

            metrics = parse_metrics_line(line)
            if metrics:
                if metrics[0] == "Exact":
                    current.exact_metrics = metrics
                elif metrics[0] == "None_E":
                    current.approx_metrics = metrics

    if current is not None:
        records.append(current)

    return records, saw_exhausted


def replace_fillcolor(line: str, fillcolor: str) -> str:
    if "fillcolor" not in line:
        if line.endswith("];\n"):
            return line[:-3] + f", fillcolor={fillcolor}];\n"
        if line.endswith("];"):
            return line[:-2] + f", fillcolor={fillcolor}];"
        return line
    return re.sub(r"fillcolor\s*=\s*[^,\]]+", f"fillcolor={fillcolor}", line, count=1)


def colorize_dot(dot_path: Path, output_path: Path, highlight_nodes_1: Sequence[str], highlight_nodes_2: Optional[Sequence[str]] = None, in_color_1: str = "red", in_color_2: str = "green") -> None:
    """Colorize dot file: highlight_nodes in in_colors(default=red), others white."""
    highlight_set_1 = set(highlight_nodes_1)
    highlight_set_2 = set(highlight_nodes_2) if highlight_nodes_2 else set()
    node_line = re.compile(r"^(?P<name>[^\s\[]+)\s+\[(?P<attrs>.*)\];\s*$")
    source_lines = dot_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    rendered_lines: List[str] = []

    for line in source_lines:
        match = node_line.match(line.rstrip("\n"))
        if not match:
            rendered_lines.append(line)
            continue

        node_name = match.group("name")

        # Selected nodes are a subset of cone nodes: keep them green by giving
        # highlight_set_2 precedence over highlight_set_1.
        if node_name in highlight_set_2:
            updated = replace_fillcolor(line, in_color_2)
            rendered_lines.append(updated)
        elif node_name in highlight_set_1:
            updated = replace_fillcolor(line, in_color_1)
            rendered_lines.append(updated)
        else:
            updated = replace_fillcolor(line, "white")
            rendered_lines.append(updated)


    output_path.write_text("".join(rendered_lines), encoding="utf-8")


def extract_cone_subgraph(dot_path: Path, cone_nodes: Sequence[str]) -> str:
    """Extract subgraph containing only cone_nodes and their edges."""
    cone_set = set(cone_nodes)
    lines = dot_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    
    header_end = 0
    for i, line in enumerate(lines):
        if "{" in line:
            header_end = i
            break
    
    result_lines = lines[:header_end + 2]  # header + digraph line + node defaults
    
    for line in lines[header_end + 2:]:
        if "->" in line:
            match = re.match(r"(\w+)\s*->\s*(\w+)", line)
            if match and match.group(1) in cone_set and match.group(2) in cone_set:
                result_lines.append(line)
        elif "[" in line and "]" in line:
            match = re.match(r"(\w+)\s*\[", line)
            if match and match.group(1) in cone_set:
                result_lines.append(line)
    
    result_lines.append("}")
    return "\n".join(result_lines)


def render_dot(dot_path: Path, out_path: Path, fmt: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = ["dot", f"-T{fmt}", str(dot_path), "-o", str(out_path)]
    subprocess.run(command, check=True, capture_output=True)


def build_full_graph_with_cone(dot_path: Path, gv_dir: Path, image_dir: Path, iteration: int, cone_nodes: Sequence[str], changed_nodes: Sequence[str], image_format: str) -> Path:
    """Render full graph with cone highlighted in red."""
    colored_dot = gv_dir / f"iter_{iteration}_full_cone.gv"
    image_path = image_dir / f"iter_{iteration}_full_cone.{image_format}"

    colorize_dot(dot_path, colored_dot, highlight_nodes_1=cone_nodes, highlight_nodes_2=changed_nodes, in_color_1="green", in_color_2="red")

    render_dot(colored_dot, image_path, image_format)
    return image_path


def build_cone_subgraph_with_changes(dot_path: Path, gv_dir: Path, image_dir: Path, iteration: int, cone_nodes: Sequence[str], changed_nodes: Sequence[str], image_format: str) -> Path:
    """Render cone subgraph with changed nodes highlighted in red."""
    cone_dot = gv_dir / f"iter_{iteration}_cone_only.gv"
    cone_dot_content = extract_cone_subgraph(dot_path, cone_nodes)
    cone_dot.write_text(cone_dot_content, encoding="utf-8")
    
    colored_cone_dot = gv_dir / f"iter_{iteration}_cone_colored.gv"
    colorize_dot(cone_dot, colored_cone_dot, highlight_nodes_1=cone_nodes, highlight_nodes_2=changed_nodes, in_color_1="green", in_color_2="red")
    
    image_path = image_dir / f"iter_{iteration}_cone.{image_format}"
    render_dot(colored_cone_dot, image_path, image_format)
    return image_path


def append_report_image(story: List, image_path: Path, image_format: str, width: float, height: float, info_style: ParagraphStyle) -> None:
    if image_format == "svg":
        svg2rlg = load_svg2rlg()
        if svg2rlg is None:
            raise RuntimeError("SVG rendering requires svglib. Install with: pip install svglib")
        drawing = svg2rlg(str(image_path))
        if drawing is None:
            raise RuntimeError(f"Unable to load SVG drawing: {image_path}")
        if not drawing.width or not drawing.height:
            raise RuntimeError(f"Invalid SVG size for drawing: {image_path}")

        scale = min(width / float(drawing.width), height / float(drawing.height))
        drawing.scale(scale, scale)
        # Keep ReportLab layout engine in sync with transformed size.
        drawing.width = float(drawing.width) * scale
        drawing.height = float(drawing.height) * scale
        story.append(drawing)
        return

    story.append(Image(str(image_path), width=width, height=height))


def main() -> None:
    args = parse_args()
    script_root = Path(__file__).resolve().parent.parent
    log_path = Path(args.log)
    if not log_path.is_absolute():
        log_path = Path.cwd() / log_path

    records, saw_exhausted = parse_log(log_path)

    benchmark = records[0].benchmark if records else args.benchmark
    full_graph = Path(args.full_graph) if args.full_graph else Path("output/gv") / f"{benchmark}.gv"
    if not full_graph.is_absolute():
        full_graph = script_root / full_graph

    subgraph_dir = Path(args.subgraph_dir)
    if not subgraph_dir.is_absolute():
        subgraph_dir = script_root / subgraph_dir

    output_pdf = Path(args.output) if args.output else Path("output/report") / f"{benchmark}_iteration_report.pdf"
    if not output_pdf.is_absolute():
        output_pdf = script_root / output_pdf
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        raise SystemExit(f"No iterations found in {log_path}")

    specs_text = log_path.read_text(encoding="utf-8", errors="ignore")
    specs = parse_specs_from_log_text(specs_text)

    if args.image_format == "svg" and load_svg2rlg() is None:
        raise SystemExit("--image-format svg requires svglib (pip install svglib)")

    if args.limit is not None:
        records = records[: max(args.limit, 0)]
        if not records:
            raise SystemExit("--limit produced an empty iteration set")

    # Create temporary directory for rendered image files
    temp_context = tempfile.TemporaryDirectory(prefix="subxpat_iteration_report_")
    image_dir = Path(temp_context.name)
    
    # Create permanent directory for .gv files only if --keep-temp flag is set
    if args.keep_temp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gv_dir = Path.cwd() / "temp" / f"subxpat_iteration_report_{timestamp}"
        gv_dir.mkdir(parents=True, exist_ok=True)
    else:
        gv_dir = image_dir  # Use temporary directory for .gv files if not keeping
    
    try:
        # Build PDF using ReportLab with A4 portrait pages
        doc = SimpleDocTemplate(str(output_pdf), pagesize=A4, topMargin=10*mm, bottomMargin=10*mm, leftMargin=10*mm, rightMargin=10*mm)
        story = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor='#000000',
            spaceAfter=4,
            alignment=TA_CENTER,
            leading=14,
        )
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=8,
            textColor='#333333',
            spaceAfter=6,
            alignment=TA_LEFT,
            leading=10,
        )

        append_specs_page(story, specs, title_style, info_style)

        for idx, record in enumerate(records):
            if record.subgraph_path is not None and not record.subgraph_path.is_absolute():
                candidate = script_root / record.subgraph_path
                if candidate.exists():
                    record.subgraph_path = candidate

            if record.subgraph_path is None:
                candidate = subgraph_dir / f"{benchmark}_et{record.et}_mode0_omax2.gv"
                if candidate.exists():
                    record.subgraph_path = candidate

            if record.subgraph_path is None or not record.subgraph_path.exists():
                raise FileNotFoundError(f"Missing subgraph .gv for iteration {record.iteration}: {record.subgraph_path}")

            # PAGE 1: Full graph with cone highlighted in red
            full_image = build_full_graph_with_cone(
                record.subgraph_path,
                gv_dir,
                image_dir,
                record.iteration,
                record.ascendants,
                record.node_partition,
                args.image_format,
            )
            
            title_text = f"Iteration {record.iteration} &ndash; Full Circuit with Cone (out_node={record.out_node})"
            story.append(Paragraph(title_text, title_style))
            
            info_text = f"<b>ET:</b> {record.et} | <b>Benchmark:</b> {record.benchmark} | <b>Cone size:</b> {len(record.ascendants)} | <b>Partition size:</b> {len(record.node_partition)}"
            story.append(Paragraph(info_text, info_style))
            
            story.append(Spacer(1, 2*mm))
            
            try:
                append_report_image(story, full_image, args.image_format, width=5.5*inch, height=7.5*inch, info_style=info_style)
            except Exception as e:
                story.append(Paragraph(f"<b>Error loading image:</b> {str(e)}", info_style))
            
            story.append(PageBreak())

            # PAGE 2: Cone subgraph with changed nodes highlighted in red
            cone_image = build_cone_subgraph_with_changes(
                record.subgraph_path,
                gv_dir,
                image_dir,
                record.iteration,
                record.ascendants,
                record.node_partition,
                args.image_format,
            )
            
            title_text = f"Iteration {record.iteration} &ndash; Cone Subgraph with Selected Nodes"
            story.append(Paragraph(title_text, title_style))
            
            result_status = "NO FEASIBLE SOLUTION"
            if record.has_sat and idx + 1 < len(records) and records[idx + 1].benchmark != record.benchmark:
                result_status = "NEW VERILOG CREATED"
            
            cell_info = ""
            if record.first_sat_cell:
                cell_info = f"First SAT: Cell({record.first_sat_cell.row},{record.first_sat_cell.col})"
            else:
                UNSAT_explored_cells = sum(1 for c in record.cells if c.status == 'UNSAT')
                UNKNOWN_explored_cells = sum(1 for c in record.cells if c.status == 'UNKNOWN')
                DOMINATED_explored_cells = sum(1 for c in record.cells if c.status == 'DOMINATED')
                explored_cells = UNSAT_explored_cells + UNKNOWN_explored_cells + DOMINATED_explored_cells

                if explored_cells > 0:
                    cell_info = f"Explored {explored_cells} cells - UNSAT: {UNSAT_explored_cells}, UNKNOWN: {UNKNOWN_explored_cells}, DOMINATED: {DOMINATED_explored_cells}"
                else:
                    cell_info = f"All cells UNSAT, explored {explored_cells} cells (subgraph is equal to the previous one, skipped iteration)"

            
            metric_info = ""
            if record.approx_metrics:
                _, area, power, delay = record.approx_metrics
                metric_info = f" | <b>Metrics:</b> Area={area}, Power={power}, Delay={delay}"
            
            info_text = f"<b>Result:</b> {result_status} | <b>Status:</b> {cell_info}{metric_info}"
            story.append(Paragraph(info_text, info_style))
            
            story.append(Spacer(1, 2*mm))
            
            try:
                append_report_image(story, cone_image, args.image_format, width=5.5*inch, height=7.5*inch, info_style=info_style)
            except Exception as e:
                story.append(Paragraph(f"<b>Error loading image:</b> {str(e)}", info_style))
            
            story.append(PageBreak())

        # Build the PDF
        doc.build(story)
        print(f"PDF written to: {output_pdf}")
        print(f"Total iterations processed: {len(records)}")
        if args.keep_temp:
            print(f"GraphViz files saved to: {gv_dir}")
    finally:
        if args.keep_temp:
            print(f"Temporary rendered image files kept at: {image_dir}")
        else:
            temp_context.cleanup()


if __name__ == "__main__":
    main()
