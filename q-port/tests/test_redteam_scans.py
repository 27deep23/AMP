"""
Red-Team Test: Codebase Integrity & Banned Import / Fake Metric Scans.
Scans Python source files in core/ and api/ to enforce zero hardware provider imports and zero fake result metrics.
"""

import os
import re
import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def test_no_hardware_provider_imports():
    """Scan all .py files to ensure no IBM / IonQ / Rigetti hardware provider libraries are imported."""
    banned_imports = [
        "qiskit_ibm_provider",
        "qiskit_ibm_runtime",
        "qiskit_ionq",
        "qiskit_rigetti",
        "pyquil",
        "braket"
    ]

    target_dirs = [PROJECT_ROOT / "core", PROJECT_ROOT / "api", PROJECT_ROOT / "ui"]

    for tdir in target_dirs:
        if not tdir.exists():
            continue
        for py_file in tdir.glob("**/*.py"):
            content = py_file.read_text(encoding="utf-8")
            for banned in banned_imports:
                pattern = rf"\bimport\s+{banned}\b|\bfrom\s+{banned}\b"
                assert not re.search(pattern, content), f"Banned hardware import '{banned}' found in {py_file}"


def test_no_hardcoded_fake_benchmark_results():
    """Scan core/ and api/ to ensure benchmark runtimes or outputs are computed dynamically, not hardcoded."""
    target_dirs = [PROJECT_ROOT / "core", PROJECT_ROOT / "api"]

    banned_phrases = [
        "runtime = 0.001",
        "runtime = 0.01",
        "return 0.001",
        "return 0.01",
        "fake_result",
        "mock_qaoa"
    ]

    for tdir in target_dirs:
        if not tdir.exists():
            continue
        for py_file in tdir.glob("**/*.py"):
            content = py_file.read_text(encoding="utf-8")
            for phrase in banned_phrases:
                assert phrase not in content, f"Forbidden hardcoded phrase '{phrase}' found in {py_file}"
