# testgen/excel_writer.py
"""
Create an Excel sheet of generated pytest testcases.

Columns:
- Test Cases Name
- Test Case Description
- Test Steps
- Expected Output
- Actual Output (Empty row)
- Automation Pending (Yes always)

We use lightweight heuristics parsing the generated pytest file contents:
- Test Case Name: AST function name (test_*)
- Description: any leading comment block immediately above the function (if present)
- Test Steps: the function body source (truncated) to indicate steps
- Expected Output: derived from assert expressions or pytest.raises occurrences
- Actual Output: left empty
- Automation Pending: "Yes"
"""

from pathlib import Path
import ast
import textwrap
from typing import List, Dict
from openpyxl import Workbook

# helper to safely unwrap AST function body to readable strings
def _source_of_node(source: str, node: ast.AST) -> str:
    try:
        # ast.get_source_segment exists in Python 3.8+. If unavailable, fallback to unparse
        seg = ast.get_source_segment(source, node)
        if seg:
            return seg.strip()
    except Exception:
        pass
    try:
        return ast.unparse(node).strip()
    except Exception:
        return "<unavailable>"

def _extract_test_cases_from_source(source: str) -> List[Dict[str,str]]:
    """
    Parse source and return list of test-case dictionaries.
    """
    tree = ast.parse(source)
    lines = source.splitlines()
    results = []

    # Build mapping of line numbers to comments immediately above functions
    # We'll examine tokens by scanning lines.
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # name
            name = node.name

            # get leading comments: look at lines before function.lineno
            desc_lines = []
            lineno = node.lineno - 1  # 0-based index for lines
            i = lineno - 1
            while i >= 0:
                line = lines[i].rstrip()
                if line.strip().startswith("#"):
                    # collect comment content (strip '#')
                    desc_lines.insert(0, line.strip().lstrip("#").strip())
                    i -= 1
                    continue
                # stop if blank line directly between comment block and function? we allow one blank
                if line.strip() == "" and desc_lines:
                    # if there's a blank but we already collected comments, stop scanning
                    break
                # otherwise stop scanning
                if line.strip() == "":
                    i -= 1
                    continue
                break
            description = " ".join(desc_lines).strip()

            # Test steps: convert the function body to readable pseudo-steps
            # We'll join each statement's source as a step
            steps = []
            for stmt in node.body:
                s = _source_of_node(source, stmt)
                steps.append(s)
            test_steps = "\n".join(textwrap.shorten(s, width=250, placeholder="...") for s in steps)

            # Expected output: look for assert statements or pytest.raises contexts
            expected_parts = []
            for stmt in node.body:
                if isinstance(stmt, ast.Assert):
                    try:
                        expected_parts.append("assert " + ast.unparse(stmt.test))
                    except Exception:
                        expected_parts.append("assert <expr>")
                # pytest.raises is usually inside a with-statement: with pytest.raises(ValueError):
                if isinstance(stmt, ast.With):
                    # check context exprs
                    for item in stmt.items:
                        ctx = item.context_expr
                        # crude check for 'pytest.raises'
                        src_ctx = _source_of_node(source, ctx)
                        if "pytest.raises" in src_ctx:
                            # extract the exception type from the with args
                            expected_parts.append(f"raises: {src_ctx}")
                # also inspect nested statements inside try/with
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Call):
                        try:
                            call_src = ast.unparse(child)
                        except Exception:
                            call_src = "<call>"
                        if "pytest.raises" in call_src:
                            expected_parts.append(f"raises: {call_src}")
            expected = "; ".join(expected_parts) if expected_parts else "Asserts in test (see Test Steps)"

            results.append({
                "name": name,
                "description": description,
                "test_steps": test_steps,
                "expected_output": expected,
            })

    return results

def write_excel_from_source(source: str, out_path: str):
    """
    Write an xlsx file with the test case rows derived from `source`.
    out_path: str path to output file (overwrites if exists)
    """
    testcases = _extract_test_cases_from_source(source)

    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"

    headers = [
        "Test Cases Name",
        "Test Case Description",
        "Test Steps",
        "Expected Output",
        "Actual Output (Empty row)",
        "Automation Pending (Yes always)"
    ]
    ws.append(headers)

    for tc in testcases:
        row = [
            tc["name"],
            tc["description"],
            tc["test_steps"],
            tc["expected_output"],
            "",                    # Actual Output empty
            "Yes"
        ]
        ws.append(row)

    # Auto-width modest implementation
    for col in ws.columns:
        max_len = 0
        col = list(col)
        for cell in col:
            try:
                v = str(cell.value) if cell.value is not None else ""
            except Exception:
                v = ""
            if len(v) > max_len:
                max_len = len(v)
        # limit max width to avoid huge columns:
        adjusted_width = min(max_len + 2, 50)
        ws.column_dimensions[col[0].column_letter].width = adjusted_width

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_file)
