#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO_ROOT / "notebooks"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

LOCAL_SOURCE_PATTERNS = (
    re.compile(r"""['"](/Users/[^'"]+)['"]"""),
    re.compile(r"""['"](/home/[^'"]+)['"]"""),
    re.compile(r"""['"]([A-Za-z]:\\\\Users\\\\[^'"]+)['"]"""),
)
BAD_GETENV_PATTERN = re.compile(r"""os\.getenv\(['"]\.\./[^'"]+['"]\)""")
ENV_VAR_PATTERN = re.compile(
    r"""os\.environ\[['"]([A-Z0-9_]+)['"]\]|os\.getenv\(['"]([A-Z0-9_]+)['"]\)"""
)


@dataclass(frozen=True)
class Replacement:
    path: str
    old: str
    new: str


KNOWN_REPLACEMENTS = (
    Replacement(
        path="notebooks/analysis/analysis_sc_jäkel_human.ipynb",
        old='"source": [\n    "import scanpy as sc"\n   ]',
        new='"source": [\n    "import os\\n",\n    "import scanpy as sc"\n   ]',
    ),
    Replacement(
        path="notebooks/analysis/analysis_sc_jäkel_human.ipynb",
        old="adata = sc.read_h5ad('/Users/christoffer/work/karolinska/development/metamitoMicS/data/jäkel_et_al_2019.h5ad')",
        new='adata = sc.read_h5ad(os.environ[\\"OLIGOC4B_JAKEL_H5AD\\"])',
    ),
    Replacement(
        path="notebooks/analysis/analysis_Xenium_EAE_mouse.ipynb",
        old='"source": [\n    "import scanpy as sc"\n   ]',
        new='"source": [\n    "import os\\n",\n    "import scanpy as sc"\n   ]',
    ),
    Replacement(
        path="notebooks/analysis/analysis_Xenium_EAE_mouse.ipynb",
        old="ad = sc.read_h5ad('/Users/christoffer/work/karolinska/development/metamitoMicS/data/RREAE_5k_raw_only_integration_processed.h5ad')",
        new='ad = sc.read_h5ad(os.environ[\\"OLIGOC4B_XENIUM_EAE_H5AD\\"])',
    ),
    Replacement(
        path="notebooks/build/build_sc_AD_mouse_Park.ipynb",
        old="base_dir = '/Users/christoffer/Downloads/GSE224398_RAW/'",
        new='base_dir = os.environ[\\"OLIGOC4B_SC_AD_MOUSE_RAW_DIR\\"]',
    ),
    Replacement(
        path="notebooks/build/build_snRNAseq_aging_mouse_brain.ipynb",
        old='base_dir = \\"/Users/christoffer/Downloads/GSE212576_RAW\\"',
        new='base_dir = os.environ[\\"OLIGOC4B_SNRNASEQ_AGING_RAW_DIR\\"]',
    ),
    Replacement(
        path="notebooks/build/build_Xenium_AD_mouse.ipynb",
        old="base_dir = '/Users/christoffer/Downloads/xenium_alzheimer'",
        new='base_dir = os.environ[\\"OLIGOC4B_XENIUM_AD_RAW_DIR\\"]',
    ),
    Replacement(
        path="notebooks/build/build_Visium_aging_mouse_brain.ipynb",
        old="base_dir = '/Users/christoffer/Downloads/GSE212903_RAW/'",
        new='base_dir = os.environ[\\"OLIGOC4B_VISIUM_AGING_RAW_DIR\\"]',
    ),
    Replacement(
        path="notebooks/build/build_Visium_aging_mouse_brain.ipynb",
        old='SPATIAL_BASE = \\"/Users/christoffer/Downloads/GSE212903_spatial/\\"',
        new='SPATIAL_BASE = os.environ[\\"OLIGOC4B_VISIUM_AGING_SPATIAL_DIR\\"]',
    ),
    Replacement(
        path="notebooks/build/build_sc_AD_mouse_Park.ipynb",
        old='api_key = os.getenv(\\"../OPENAI_API_KEY\\")',
        new='api_key = os.getenv(\\"OPENAI_API_KEY\\")',
    ),
    Replacement(
        path="notebooks/build/build_snRNAseq_aging_mouse_brain.ipynb",
        old='api_key = os.getenv(\\"../OPENAI_API_KEY\\")',
        new='api_key = os.getenv(\\"OPENAI_API_KEY\\")',
    ),
    Replacement(
        path="notebooks/build/build_Xenium_AD_mouse.ipynb",
        old='api_key = os.getenv(\\"../OPENAI_API_KEY\\")',
        new='api_key = os.getenv(\\"OPENAI_API_KEY\\")',
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate notebook hygiene and optionally apply known fixes."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply known source-cell fixes before validating notebooks.",
    )
    return parser.parse_args()


def apply_known_fixes() -> list[Path]:
    changed_paths: list[Path] = []
    grouped: dict[Path, list[Replacement]] = {}
    for replacement in KNOWN_REPLACEMENTS:
        path = REPO_ROOT / replacement.path
        grouped.setdefault(path, []).append(replacement)

    for path, replacements in grouped.items():
        original = path.read_text(encoding="utf-8")
        updated = original
        for replacement in replacements:
            updated = updated.replace(replacement.old, replacement.new)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_paths.append(path)
    return changed_paths


def load_notebook(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid notebook JSON: {exc}") from exc


def iter_code_cells(notebook: dict) -> list[str]:
    sources: list[str] = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if isinstance(source, str):
            sources.append(source)
        else:
            sources.append("".join(source))
    return sources


def load_documented_env_vars() -> set[str]:
    documented: set[str] = set()
    if not ENV_EXAMPLE.exists():
        return documented

    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key:
            documented.add(key)
    return documented


def find_env_vars(source: str) -> set[str]:
    env_vars: set[str] = set()
    for match in ENV_VAR_PATTERN.finditer(source):
        env_var = match.group(1) or match.group(2)
        if env_var:
            env_vars.add(env_var)
    return env_vars


def main() -> int:
    args = parse_args()

    changed_paths: list[Path] = []
    if args.fix:
        changed_paths = apply_known_fixes()
        for path in changed_paths:
            print(f"fixed {path.relative_to(REPO_ROOT)}")

    issues: list[str] = []
    referenced_env_vars: set[str] = set()

    notebook_paths = sorted(NOTEBOOK_DIR.rglob("*.ipynb"))
    for path in notebook_paths:
        try:
            notebook = load_notebook(path)
        except ValueError as exc:
            issues.append(str(exc))
            continue

        for source in iter_code_cells(notebook):
            referenced_env_vars.update(find_env_vars(source))
            for pattern in LOCAL_SOURCE_PATTERNS:
                for match in pattern.finditer(source):
                    issues.append(
                        f"{path.relative_to(REPO_ROOT)}: hard-coded local path in source cell: {match.group(1)}"
                    )
            if BAD_GETENV_PATTERN.search(source):
                issues.append(
                    f"{path.relative_to(REPO_ROOT)}: malformed getenv usage; env var names must not include ../"
                )

    documented_env_vars = load_documented_env_vars()
    missing_env_vars = sorted(referenced_env_vars - documented_env_vars)
    for env_var in missing_env_vars:
        issues.append(f".env.example: missing documented variable {env_var}")

    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1

    print(f"validated {len(notebook_paths)} notebooks")
    if referenced_env_vars:
        print(f"documented env vars: {', '.join(sorted(referenced_env_vars))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
