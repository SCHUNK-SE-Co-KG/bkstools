#!/usr/bin/env python3
"""
CVE-Scanner for the bkstools repository.

Scans Python pip dependencies for known vulnerabilities:
  - Python pip packages from setup.py install_requires (PyPI)

Data sources:
  - Google OSV API  (https://osv.dev)
  - GitHub Advisory Database (REST API + web page scraping)

Results are written as Markdown and JSON reports under
security/reports/.

Usage:
    python security/cve_scanner.py                # Scan + Report
    python security/cve_scanner.py --json-only    # JSON output only

Requirements:
    Python 3.9+, requests (pip install requests)

Author:  SCHUNK Security Tooling
License: GPL-3.0
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Force UTF-8 stdout (Windows cp1252 crashes on special chars) ────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    sys.exit("Error: 'requests' is not installed.\n  pip install requests")

# ── Constants ────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT_DIR / "security" / "reports"
REPO_NAME = "SCHUNK-SE-Co-KG/bkstools"

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL = "https://api.osv.dev/v1/vulns"  # + /{id}

CVSS_HIGH_THRESHOLD = 7.0  # Alert threshold

# Severity label -> estimated CVSS base score (last-resort fallback)
SEVERITY_LABEL_SCORES: dict[str, float] = {
    "CRITICAL": 9.0,
    "HIGH": 7.5,
    "MODERATE": 5.0,
    "MEDIUM": 5.0,
    "LOW": 2.5,
}

# ── Internal packages (skip during scan) ────────────────────────────
INTERNAL_PACKAGES = {
    "bkstools",
    "pyschunk",
}


# ── Data structures ─────────────────────────────────────────────────
@dataclass
class Dependency:
    """A detected dependency."""

    name: str
    version: str
    ecosystem: str  # "PyPI"
    source: str  # File where it was found


@dataclass
class Vulnerability:
    """A detected security vulnerability."""

    vuln_id: str
    summary: str
    severity: str
    cvss_score: float
    affected_package: str
    affected_versions: str
    fixed_version: str
    references: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass
class ScanResult:
    """Complete result of a scan run."""

    timestamp: str
    repository: str
    dependencies_scanned: int
    vulnerabilities_found: int
    high_severity_count: int = 0
    dependencies: list[Dependency] = field(default_factory=list)
    vulnerabilities: list[Vulnerability] = field(default_factory=list)


# ═════════════════════════════════════════════════════════════════════
# CVSS Score Extraction
# ═════════════════════════════════════════════════════════════════════
def _fetch_ghsa_cvss_score(ghsa_id: str) -> Optional[float]:
    """Fetch the official numeric CVSS score for a GitHub Advisory.

    Strategy (priority):
    1. GitHub Advisory web page scraping - always shows the latest score
       (CVSS 3.x or 4.0), pattern: ">X.X<" before "/ 10"
    2. GitHub REST API (/advisories/{id}) - fallback, may return stale
       CVSS 3.1 scores when advisory was updated to CVSS 4.0
    """
    # 1. Advisory web page (primary source - always up-to-date)
    page_url = f"https://github.com/advisories/{ghsa_id}"
    try:
        resp = requests.get(
            page_url,
            timeout=10,
            headers={
                "Accept": "text/html",
                "User-Agent": "SCHUNK-CVE-Scanner/1.0",
            },
        )
        if resp.status_code == 200:
            idx = resp.text.find("/ 10")
            if idx > 0:
                window = resp.text[max(0, idx - 3000) : idx]
                numbers = re.findall(r">(\d+\.\d+)<", window)
                if numbers:
                    return float(numbers[-1])
    except (Exception, KeyboardInterrupt):
        pass

    # 2. REST API as fallback
    url = f"https://api.github.com/advisories/{ghsa_id}"
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            for field_name in ("cvss_v4", "cvss"):
                cvss_data = data.get(field_name)
                if cvss_data and isinstance(cvss_data, dict):
                    score = cvss_data.get("score")
                    if isinstance(score, (int, float)) and score > 0:
                        return float(score)
    except (Exception, KeyboardInterrupt):
        pass

    return None


# ═════════════════════════════════════════════════════════════════════
# 1) Python pip dependencies from setup.py (AST-based parsing)
# ═════════════════════════════════════════════════════════════════════
def _extract_string_list(node: ast.expr) -> list[str]:
    """Extract string values from an AST node (List, Tuple or String)."""
    strings: list[str] = []
    if isinstance(node, (ast.List, ast.Tuple)):
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                strings.append(elt.value)
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        strings.append(node.value)
    return strings


def _parse_requirement_string(req: str) -> tuple[str, str]:
    """Parse a PEP 508 requirement string into (name, version).

    Supported formats:
      "numpy==2.2.6"
      "numpy>=2.2.6"
      "numpy>=2.2.6, <3"
      "numpy"             (no version)
      "requests[security]>=2.31"
      "pypiwin32 ; platform_system==\"Windows\""

    Returns (name, first_version) or (name, "").
    """
    req = req.strip()
    if not req:
        return ("", "")

    # Strip PEP 508 environment markers (everything after ;)
    req = req.split(";")[0].strip()

    match = re.match(r"^([a-zA-Z0-9_.-]+(?:\[[^\]]*\])?)\s*(.*)", req)
    if not match:
        return ("", "")

    name_part = match.group(1)
    version_part = match.group(2).strip()

    # Remove extras like [security]
    name = re.sub(r"\[.*?\]", "", name_part).strip()

    if not version_part:
        return (name, "")

    # Extract first version number
    ver_match = re.match(r"(?:==|>=|<=|~=|!=|<|>)\s*([^\s,;]+)", version_part)
    if ver_match:
        return (name, ver_match.group(1))

    return (name, "")


def _parse_setup_py_install_requires(content: str) -> list[tuple[str, str]]:
    """Parse install_requires from setup.py using Python AST.

    Returns list of (package_name, version_string) tuples.
    More robust than regex: handles comments, brackets and all
    PEP 508 version specifiers correctly.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    requirements: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        func_name = ""
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name != "setup":
            continue

        for kw in node.keywords:
            if kw.arg != "install_requires":
                continue

            req_strings = _extract_string_list(kw.value)
            for req_str in req_strings:
                name, version = _parse_requirement_string(req_str)
                if name:
                    requirements.append((name, version))

    return requirements


def extract_setup_py_deps(root_dir: Path) -> list[Dependency]:
    """Extract Python packages from all setup.py install_requires via AST.

    Uses Python's ast module instead of regex for robust parsing.
    Dedup key is based on (normalized_name, version) so that different
    versions of the same package from multiple setup.py files are
    scanned correctly.
    """
    deps: list[Dependency] = []
    seen: set[str] = set()

    internal_norm = {p.lower().replace("-", "_") for p in INTERNAL_PACKAGES}

    for setup_py in root_dir.rglob("setup.py"):
        try:
            content = setup_py.read_text(encoding="utf-8")
        except Exception:
            continue

        source = str(setup_py.relative_to(root_dir))
        requirements = _parse_setup_py_install_requires(content)

        for name, version in requirements:
            norm_name = name.lower().replace("-", "_")

            if norm_name in internal_norm:
                continue

            dedup_key = f"{norm_name}:{version}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            deps.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem="PyPI",
                    source=source,
                )
            )

    return deps


# ═════════════════════════════════════════════════════════════════════
# Dedup + Merge
# ═════════════════════════════════════════════════════════════════════
def deduplicate_deps(deps: list[Dependency]) -> list[Dependency]:
    """Remove duplicate dependencies (same name + ecosystem + version)."""
    seen: set[str] = set()
    unique: list[Dependency] = []
    for d in deps:
        key = f"{d.ecosystem}:{d.name}:{d.version}"
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


# ═════════════════════════════════════════════════════════════════════
# GitHub Advisory Database scan for PyPI packages
# ═════════════════════════════════════════════════════════════════════
def scan_github_advisories_for_pypi(dep: Dependency) -> list[dict]:
    """Scan GitHub Advisory Database for a specific PyPI package.

    Queries multiple ecosystems since packages can have advisories
    filed under different ecosystems. Deduplicates results by GHSA-ID.
    """
    if dep.ecosystem != "PyPI":
        return []

    all_advisories: list[dict] = []
    seen_ids: set[str] = set()

    url = "https://api.github.com/advisories"
    for ecosystem in ("pip", "go", "rust", "npm"):
        try:
            resp = requests.get(
                url,
                timeout=15,
                params={
                    "ecosystem": ecosystem,
                    "affects": dep.name,
                },
                headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            if resp.status_code == 200:
                for adv in resp.json():
                    adv_id = adv.get("ghsa_id", "")
                    if adv_id and adv_id not in seen_ids:
                        seen_ids.add(adv_id)
                        all_advisories.append(adv)
        except (Exception, KeyboardInterrupt):
            pass

    return all_advisories


# ═════════════════════════════════════════════════════════════════════
# OSV API queries
# ═════════════════════════════════════════════════════════════════════
def _build_osv_query(dep: Dependency) -> dict:
    """Build a single OSV query for a dependency."""
    q: dict = {"package": {"name": dep.name, "ecosystem": dep.ecosystem}}
    if dep.version:
        q["version"] = dep.version
    return q


def query_osv_batch(deps: list[Dependency]) -> list[list[dict]]:
    """Send a batch query to the OSV API."""
    if not deps:
        return []

    osv_ecosystems = {"PyPI", "Debian", "npm", "crates.io", "Go", "Maven"}

    queries = []
    query_indices = []
    for i, dep in enumerate(deps):
        if dep.ecosystem in osv_ecosystems:
            queries.append(_build_osv_query(dep))
            query_indices.append(i)

    results: list[list[dict]] = [[] for _ in deps]

    if queries:
        try:
            resp = requests.post(
                OSV_BATCH_URL,
                json={"queries": queries},
                timeout=30,
            )
            resp.raise_for_status()
            batch_results = resp.json().get("results", [])
            for j, res in enumerate(batch_results):
                orig_idx = query_indices[j]
                results[orig_idx] = res.get("vulns", [])
        except requests.RequestException as exc:
            print(f"  WARNING  OSV API batch error: {exc}")

    return results


def fetch_vuln_details(vuln_id: str) -> Optional[dict]:
    """Fetch full vulnerability details from the OSV API."""
    try:
        resp = requests.get(f"{OSV_VULN_URL}/{vuln_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def enrich_vulnerabilities(vulns_per_dep: list[list[dict]]) -> list[list[dict]]:
    """Enrich batch results with full details."""
    enriched: list[list[dict]] = []
    for dep_vulns in vulns_per_dep:
        enriched_list: list[dict] = []
        for v in dep_vulns:
            vuln_id = v.get("id", "")
            if not v.get("summary") and not v.get("details"):
                full = fetch_vuln_details(vuln_id)
                if full:
                    enriched_list.append(full)
                    continue
            enriched_list.append(v)
        enriched.append(enriched_list)
    return enriched


# ═════════════════════════════════════════════════════════════════════
# Vulnerability parsing
# ═════════════════════════════════════════════════════════════════════
def _extract_severity(vuln: dict) -> str:
    """Extract severity from an OSV vulnerability."""
    severity_entries = vuln.get("severity", [])
    for s in severity_entries:
        score_str = s.get("score", "")
        if score_str:
            return score_str
    db_spec = vuln.get("database_specific", {})
    severity = db_spec.get("severity", "")
    if severity:
        return severity
    return "UNKNOWN"


def _compute_cvss_score(vuln: dict, severity_str: str) -> float:
    """Fetch the official CVSS score from the GitHub Advisory API."""
    vuln_id = vuln.get("id", "")

    # 1. Determine GHSA-ID
    ghsa_id = vuln_id if vuln_id.startswith("GHSA-") else ""
    if not ghsa_id:
        for alias in vuln.get("aliases", []):
            if alias.startswith("GHSA-"):
                ghsa_id = alias
                break

    if ghsa_id:
        api_score = _fetch_ghsa_cvss_score(ghsa_id)
        if api_score is not None:
            return api_score

    # 2. Fallback: Severity label
    db_severity = vuln.get("database_specific", {}).get("severity", "").upper()
    if db_severity in SEVERITY_LABEL_SCORES:
        return SEVERITY_LABEL_SCORES[db_severity]

    upper = severity_str.upper()
    for label in SEVERITY_LABEL_SCORES:
        if label in upper:
            return SEVERITY_LABEL_SCORES[label]

    return 0.0


def _extract_fixed_version(affected: dict) -> str:
    """Determine the first fixed version from affected ranges."""
    for rng in affected.get("ranges", []):
        for event in rng.get("events", []):
            if "fixed" in event:
                return event["fixed"]
    return "–"


def parse_vulnerabilities(
    dep: Dependency, vulns: list[dict]
) -> list[Vulnerability]:
    """Convert raw OSV entries into Vulnerability objects."""
    results: list[Vulnerability] = []
    for v in vulns:
        vuln_id = v.get("id", "?")
        summary = v.get("summary", v.get("details", "No description"))
        severity = _extract_severity(v)
        aliases = v.get("aliases", [])

        affected_versions = ""
        fixed_version = "–"
        for aff in v.get("affected", []):
            pkg = aff.get("package", {})
            if pkg.get("name") == dep.name:
                affected_versions = ", ".join(aff.get("versions", [])[:10])
                if len(aff.get("versions", [])) > 10:
                    affected_versions += " ..."
                fixed_version = _extract_fixed_version(aff)
                break

        refs = [
            r.get("url", "")
            for r in v.get("references", [])
            if r.get("url")
        ]
        cvss_score = _compute_cvss_score(v, severity)

        results.append(
            Vulnerability(
                vuln_id=vuln_id,
                summary=summary[:300].strip(),
                severity=severity,
                cvss_score=cvss_score,
                affected_package=(
                    f"{dep.ecosystem}:{dep.name}"
                    + (f"@{dep.version}" if dep.version else "")
                ),
                affected_versions=affected_versions,
                fixed_version=fixed_version,
                references=refs[:5],
                aliases=aliases,
            )
        )
    return results


def parse_github_advisory(
    dep: Dependency, advisory: dict
) -> Optional[Vulnerability]:
    """Convert a GitHub Advisory into a Vulnerability object."""
    ghsa_id = advisory.get("ghsa_id", "")
    if not ghsa_id:
        return None

    summary = advisory.get("summary", "No description")
    severity = advisory.get("severity", "UNKNOWN")
    cve_id = advisory.get("cve_id", "")

    cvss_score = 0.0
    score = _fetch_ghsa_cvss_score(ghsa_id)
    if score is not None:
        cvss_score = score
    elif severity.upper() in SEVERITY_LABEL_SCORES:
        cvss_score = SEVERITY_LABEL_SCORES[severity.upper()]

    refs = []
    if advisory.get("html_url"):
        refs.append(advisory["html_url"])

    aliases = [ghsa_id]
    if cve_id:
        aliases.append(cve_id)

    return Vulnerability(
        vuln_id=ghsa_id,
        summary=summary[:300].strip(),
        severity=severity,
        cvss_score=cvss_score,
        affected_package=(
            f"PyPI:{dep.name}"
            + (f"@{dep.version}" if dep.version else "")
        ),
        affected_versions="",
        fixed_version="–",
        references=refs[:5],
        aliases=aliases,
    )


# ═════════════════════════════════════════════════════════════════════
# Report generation
# ═════════════════════════════════════════════════════════════════════
def generate_markdown_report(result: ScanResult) -> str:
    """Generate a Markdown report from the scan result."""
    lines: list[str] = []
    lines.append("# CVE-Scan Report - bkstools")
    lines.append("")
    lines.append(f"**Scan timestamp:** {result.timestamp}")
    lines.append(f"**Repository:** {result.repository}")
    lines.append(f"**Dependencies scanned:** {result.dependencies_scanned}")
    lines.append(f"**Vulnerabilities found:** {result.vulnerabilities_found}")
    lines.append("")

    if result.vulnerabilities_found == 0:
        lines.append("> No known vulnerabilities found.")
    else:
        lines.append(
            f"> {result.vulnerabilities_found} vulnerability(ies) found!"
        )
    lines.append("")

    # Summary by ecosystem
    pypi_deps = [d for d in result.dependencies if d.ecosystem == "PyPI"]
    pypi_vulns = [
        v
        for v in result.vulnerabilities
        if v.affected_package.startswith("PyPI:")
    ]

    lines.append("## Summary by ecosystem")
    lines.append("")
    lines.append("| Ecosystem | Dependencies | Vulnerabilities |")
    lines.append("|-----------|-------------|-----------------|")
    lines.append(
        f"| PyPI (Python) | {len(pypi_deps)} | {len(pypi_vulns)} |"
    )
    lines.append(
        f"| **Total** | **{result.dependencies_scanned}**"
        f" | **{result.vulnerabilities_found}** |"
    )
    lines.append("")

    # Scanned dependencies
    lines.append("## Scanned dependencies")
    lines.append("")

    if pypi_deps:
        lines.append("### Python (PyPI)")
        lines.append("")
        lines.append("| Package | Version | Source |")
        lines.append("|---------|---------|--------|")
        for d in pypi_deps:
            lines.append(
                f"| {d.name} | {d.version or '–'} | {d.source} |"
            )
        lines.append("")

    # Vulnerabilities
    if result.vulnerabilities:
        lines.append("## Found vulnerabilities")
        lines.append("")
        for v in result.vulnerabilities:
            cve_aliases = [a for a in v.aliases if a.startswith("CVE-")]
            cve_str = ", ".join(cve_aliases) if cve_aliases else "–"
            lines.append(f"### {v.vuln_id}")
            lines.append("")
            lines.append(f"- **Package:** {v.affected_package}")
            score_display = (
                f"{v.cvss_score:.1f}" if v.cvss_score > 0 else "–"
            )
            high_marker = (
                " (CRITICAL)" if v.cvss_score >= CVSS_HIGH_THRESHOLD else ""
            )
            lines.append(
                f"- **CVSS Score:** {score_display}{high_marker}"
            )
            lines.append(f"- **Severity:** {v.severity}")
            lines.append(f"- **CVE:** {cve_str}")
            lines.append(f"- **Description:** {v.summary}")
            lines.append(f"- **Fix version:** {v.fixed_version}")
            if v.references:
                lines.append("- **References:**")
                for ref in v.references:
                    lines.append(f"  - {ref}")
            lines.append("")

    lines.append("---")
    lines.append(
        "*Automatically generated by `security/cve_scanner.py`"
        " via [OSV.dev](https://osv.dev)"
        " and GitHub Advisory Database.*"
    )
    lines.append("")
    return "\n".join(lines)


def generate_alert_body(result: ScanResult) -> str:
    """Generate the body for the high-severity alert."""
    high = [
        v
        for v in result.vulnerabilities
        if v.cvss_score >= CVSS_HIGH_THRESHOLD
    ]
    lines: list[str] = []
    lines.append("CVE Alert: Critical vulnerabilities in bkstools")
    lines.append("=" * 68)
    lines.append("")
    lines.append(f"Scan timestamp: {result.timestamp}")
    lines.append(f"Repository:     {result.repository}")
    lines.append(
        f"Vulnerabilities: {result.vulnerabilities_found} total, "
        f"{len(high)} with CVSS >= {CVSS_HIGH_THRESHOLD}"
    )
    lines.append("")
    lines.append("-" * 68)

    for v in high:
        cve_aliases = [a for a in v.aliases if a.startswith("CVE-")]
        cve_str = ", ".join(cve_aliases) if cve_aliases else "–"
        lines.append("")
        lines.append(f"  {v.vuln_id}  (CVSS {v.cvss_score:.1f})")
        lines.append(f"  Package:     {v.affected_package}")
        lines.append(f"  CVE:         {cve_str}")
        lines.append(f"  Fix version: {v.fixed_version}")
        lines.append(f"  {v.summary[:200]}")
        if v.references:
            lines.append(f"  -> {v.references[0]}")

    lines.append("")
    lines.append("-" * 68)
    lines.append("Full report: security/reports/cve_report.md")
    lines.append(
        f"https://github.com/{REPO_NAME}/blob/main/"
        "security/reports/cve_report.md"
    )
    lines.append("")
    return "\n".join(lines)


def write_alert_output(result: ScanResult, report_dir: Path) -> None:
    """Write alert files for GitHub Actions."""
    report_dir.mkdir(parents=True, exist_ok=True)
    alert_flag_path = report_dir / "alert_high_severity.txt"

    if result.high_severity_count > 0:
        alert_body = generate_alert_body(result)
        alert_flag_path.write_text(alert_body, encoding="utf-8")
        print(f"  Alert file: {alert_flag_path.relative_to(ROOT_DIR)}")

        gh_output = os.environ.get("GITHUB_OUTPUT")
        if gh_output:
            with open(gh_output, "a") as f:
                f.write("high_severity=true\n")
                f.write(f"high_count={result.high_severity_count}\n")
                f.write(
                    f"alert_subject=CVE Alert: "
                    f"{result.high_severity_count} critical "
                    f"vulnerability(ies) in bkstools\n"
                )
    else:
        if alert_flag_path.exists():
            alert_flag_path.unlink()
        gh_output = os.environ.get("GITHUB_OUTPUT")
        if gh_output:
            with open(gh_output, "a") as f:
                f.write("high_severity=false\n")


def save_reports(
    result: ScanResult, report_dir: Path
) -> tuple[Path, Path]:
    """Save JSON and Markdown reports."""
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "cve_report.json"
    md_path = report_dir / "cve_report.md"

    json_path.write_text(
        json.dumps(asdict(result), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        generate_markdown_report(result), encoding="utf-8"
    )

    return json_path, md_path


# ═════════════════════════════════════════════════════════════════════
# Main logic
# ═════════════════════════════════════════════════════════════════════
def run_scan() -> ScanResult:
    """Run the complete CVE scan."""
    print("CVE Scanner started ...")
    print(f"   Repository root: {ROOT_DIR}")
    print()

    # 1. Collect dependencies from setup.py
    print("== Python pip dependencies (setup.py) ==")
    pip_deps = extract_setup_py_deps(ROOT_DIR)
    for d in pip_deps:
        version_str = f"=={d.version}" if d.version else " (unpinned)"
        print(f"   * {d.name}{version_str}  ({d.source})")

    all_deps = deduplicate_deps(pip_deps)
    print()
    print(f"Total: {len(all_deps)} dependency(ies) detected")
    print(f"   PyPI: {len([d for d in all_deps if d.ecosystem == 'PyPI'])}")
    print()

    # 2. OSV API batch query (PyPI)
    print("Querying OSV API (PyPI) ...")
    batch_results = query_osv_batch(all_deps)
    batch_results = enrich_vulnerabilities(batch_results)

    # 3. GitHub Advisory scan for PyPI packages
    print("Checking GitHub Advisory Database for PyPI packages ...")
    all_vulns: list[Vulnerability] = []

    for dep, osv_vulns in zip(all_deps, batch_results):
        # Process OSV results
        parsed = parse_vulnerabilities(dep, osv_vulns)
        if parsed:
            print(
                f"   !! {dep.name}: "
                f"{len(parsed)} vulnerability(ies) (OSV)"
            )
        all_vulns.extend(parsed)

        # GitHub Advisories for PyPI packages (multi-ecosystem query)
        gh_advisories = scan_github_advisories_for_pypi(dep)
        seen_ids = {v.vuln_id for v in all_vulns}
        for adv in gh_advisories:
            vuln = parse_github_advisory(dep, adv)
            if vuln and vuln.vuln_id not in seen_ids:
                all_vulns.append(vuln)
                seen_ids.add(vuln.vuln_id)
                print(
                    f"   !! {dep.name}: "
                    f"{vuln.vuln_id} (GitHub Advisory)"
                )

    if not all_vulns:
        print("   OK  No vulnerabilities found.")

    high_sev = [
        v for v in all_vulns if v.cvss_score >= CVSS_HIGH_THRESHOLD
    ]
    if high_sev:
        print(
            f"   ALERT  {len(high_sev)} vulnerability(ies)"
            f" with CVSS >= {CVSS_HIGH_THRESHOLD}!"
        )

    result = ScanResult(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repository=REPO_NAME,
        dependencies_scanned=len(all_deps),
        vulnerabilities_found=len(all_vulns),
        high_severity_count=len(high_sev),
        dependencies=all_deps,
        vulnerabilities=all_vulns,
    )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CVE Scanner for bkstools dependencies"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output JSON to stdout only, don't write files",
    )
    args = parser.parse_args()

    result = run_scan()

    if args.json_only:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return

    json_path, md_path = save_reports(result, REPORT_DIR)
    print()
    print(f"JSON report: {json_path.relative_to(ROOT_DIR)}")
    print(f"Markdown report: {md_path.relative_to(ROOT_DIR)}")

    write_alert_output(result, REPORT_DIR)
    print()

    if result.vulnerabilities_found > 0:
        print(
            f"{result.vulnerabilities_found} vulnerability(ies) found! "
            "Details in report."
        )
        if result.high_severity_count > 0:
            print(
                f"{result.high_severity_count} of those with "
                f"CVSS >= {CVSS_HIGH_THRESHOLD} - alert triggered."
            )
        sys.exit(1)
    else:
        print("No known vulnerabilities - all clear.")
        sys.exit(0)


if __name__ == "__main__":
    main()
