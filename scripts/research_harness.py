from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "research" / "obsidian"
DOI_RE = re.compile(r"https://doi\.org/(10\.[^\s)]+)", re.IGNORECASE)
LINK_RE = re.compile(r"\[\[([^\]|#]+)")


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_repository_gate() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "python" / "tools" / "repo_check.py"),
            "--require-focused-audit-complete",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode:
        print("[FAIL] repository contract gate")
    return result.returncode


def check_files() -> Check:
    required = {
        ROOT / "MEMORY.md",
        ROOT / "research" / "RESEARCH_PROMPT.md",
        VAULT / "cca-nmpc-research.md",
        VAULT / "01_Problem" / "research-gap.md",
        VAULT / "02_Literature" / "closest-work.md",
        VAULT / "02_Literature" / "core-doi-sources.md",
        VAULT / "03_Theory" / "mathematical-model.md",
        VAULT / "03_Theory" / "cca-trajectory-generation.md",
        VAULT / "03_Theory" / "nmpc-motion-control.md",
        VAULT / "03_Theory" / "lyapunov-stability.md",
        VAULT / "04_Evaluation" / "baseline-contract.md",
        VAULT / "04_Evaluation" / "simulation-design.md",
        VAULT / "04_Evaluation" / "claim-evidence-boundary.md",
        VAULT / "05_Workflow" / "research-loop.md",
    }
    missing = sorted(str(path.relative_to(ROOT)) for path in required if not path.is_file())
    return Check("required files", not missing, "none missing" if not missing else ", ".join(missing))


def check_frontmatter(notes: list[Path]) -> Check:
    invalid = []
    for note in notes:
        text = read(note)
        head = text.split("---", 2)
        if len(head) < 3 or not all(f"{key}:" in head[1] for key in ("domain", "status", "evidence")):
            invalid.append(str(note.relative_to(VAULT)))
    return Check("research frontmatter", not invalid, "valid" if not invalid else ", ".join(invalid))


def check_graph(notes: list[Path]) -> list[Check]:
    keys = {str(path.relative_to(VAULT).with_suffix("" )).replace("\\", "/"): path for path in notes}
    stems: dict[str, list[str]] = {}
    for key in keys:
        stems.setdefault(Path(key).name, []).append(key)
    edges: dict[str, set[str]] = {key: set() for key in keys}
    unresolved: list[str] = []
    sparse: list[str] = []
    for key, path in keys.items():
        links = {link.strip().replace("\\", "/") for link in LINK_RE.findall(read(path))}
        if len(links) < 3:
            sparse.append(key)
        for link in links:
            target = link if link in keys else None
            if target is None and len(stems.get(Path(link).name, [])) == 1:
                target = stems[Path(link).name][0]
            if target is None:
                unresolved.append(f"{key}->{link}")
                continue
            edges[key].add(target)
            edges[target].add(key)
    orphans = sorted(key for key, adjacent in edges.items() if not adjacent)
    return [
        Check("knowledge links", not sparse, "at least three per note" if not sparse else ", ".join(sparse)),
        Check("resolved wikilinks", not unresolved, "all resolved" if not unresolved else ", ".join(unresolved)),
        Check("graph orphans", not orphans, "none" if not orphans else ", ".join(orphans)),
    ]


def check_dois(notes: list[Path]) -> Check:
    dois = {match.lower().rstrip(".,;") for note in notes for match in DOI_RE.findall(read(note))}
    return Check("DOI evidence", len(dois) >= 15, f"{len(dois)} unique DOI links")


def check_gap() -> Check:
    text = read(VAULT / "01_Problem" / "research-gap.md")
    normalized = text.casefold()
    fields = ("Closest evidence", "Unresolved limitation", "Proposed response", "Falsification")
    missing = [field for field in fields if field not in text]
    required = (
        "Continuous Context-Aware",
        "local path",
        "observation-rate",
        "trigger-rate",
    )
    absent = [term for term in required if term.casefold() not in normalized]
    forbidden = [
        term
        for term in (
            "first-ever",
            "no prior work exists",
            "guaranteed safety",
            "framework satisfying all six",
        )
        if term in text.lower()
    ]
    passed = not missing and not absent and not forbidden
    detail = (
        "complete and bounded"
        if passed
        else f"headers={missing}; terms={absent}; forbidden={forbidden}"
    )
    return Check("research-gap matrix", passed, detail)


def check_closest_work() -> Check:
    paths = (
        VAULT / "02_Literature" / "closest-work.md",
        VAULT / "02_Literature" / "core-doi-sources.md",
    )
    text = "\n".join(read(path) for path in paths)
    required = (
        "10.48550/arXiv.2507.09134",
        "10.1109/TCST.2024.3365996",
        "10.1016/S0020-0255(98)10052-X",
        "10.1016/j.robot.2014.11.001",
        "10.1016/j.mechmachtheory.2021.104605",
        "10.1016/S0045-7825(01)00323-1",
        "10.1016/j.cosrev.2009.07.001",
        "10.1162/evco.1999.7.1.19",
        "10.1016/S0005-1098(02)00135-8",
        "closest architectural",
        "not contributions",
    )
    missing = [term for term in required if term not in text]
    return Check(
        "closest-work challenge",
        not missing,
        "PathFG and governor covered" if not missing else ", ".join(missing),
    )


def check_baselines() -> Check:
    text = read(VAULT / "04_Evaluation" / "baseline-contract.md")
    required = (
        "Shared conditions",
        "Prediction layer",
        "CCA local-path layer",
        "Motion-control layer",
        "End-to-end layer",
        "p50/p95/p99",
        "DWA",
        "MPPI",
        "PathFG-style",
        "$v_y=0$",
        "G0",
        "GCV",
        "GLT",
        "P−GLT",
        "decoder-only",
        "pre/post-repair",
    )
    missing = [item for item in required if item not in text]
    return Check("matched baselines", not missing, "complete" if not missing else ", ".join(missing))


def check_layout() -> Check:
    invalid = []
    if (ROOT / "matlab").exists():
        invalid.append("top-level matlab remains")
    if (ROOT / "src" / "simulation").exists():
        invalid.append("src/simulation remains")
    for path in (ROOT / "simulations" / "matlab", ROOT / "simulations" / "python"):
        if not path.is_dir():
            invalid.append(f"missing {path.relative_to(ROOT)}")
    if (ROOT / "simulations" / "matlab" / "+ccanmpc").exists():
        invalid.append("legacy MATLAB package remains")
    for name in ("planner.py", "study.py"):
        path = ROOT / "simulations" / "python" / name
        if not path.is_file():
            invalid.append(f"missing {path.relative_to(ROOT)}")
    return Check("code layout", not invalid, "separated" if not invalid else "; ".join(invalid))


def check_model_parity() -> Check:
    paths = {
        "python": ROOT / "simulations" / "python" / "model.py",
        "matlab": ROOT / "simulations" / "matlab" / "position_step.m",
        "kinematics": ROOT / "simulations" / "matlab" / "kinematics.m",
        "dynamics": ROOT / "simulations" / "matlab" / "dynamics.m",
        "parameters": ROOT / "simulations" / "matlab" / "robot_parameters.m",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        return Check("theory-code model", False, f"missing {', '.join(missing)}")
    python = read(paths["python"])
    matlab = "\n".join(read(path) for name, path in paths.items() if name != "python")
    python_ok = all(token in python for token in ("position_step", "velocity_time_constant", "command"))
    matlab_ok = all(token in matlab for token in ("position_step", "velocityTimeConstant", "command"))
    return Check("theory-code model", python_ok and matlab_ok, "symbols aligned")


def check_algorithm_scope() -> Check:
    paths = [ROOT / "MEMORY.md", ROOT / "research" / "RESEARCH_PROMPT.md"]
    paths.extend(sorted(VAULT.rglob("*.md")))
    text = "\n".join(read(path) for path in paths).lower()
    planner = read(ROOT / "simulations" / "python" / "planner.py")
    forbidden = ("bounded rl", "reinforcement-learning", "learnedscore", "scorebound")
    invalid = [term for term in forbidden if term in text or term in planner.lower()]
    boundary_violations = [
        term
        for term in ("applied_command", "reference_from_path", "nmpc.solve")
        if term in planner.lower()
    ]
    passed = (
        not invalid
        and not boundary_violations
        and "continuous context-aware" in text
        and "genetic algorithm" in text
        and "def observe_context(" in planner
        and "def plan_local_path(" in planner
        and "def _next_population(" in planner
    )
    detail = (
        "Python CCA with causal LSTM and GA"
        if passed
        else f"invalid={invalid}; boundary={boundary_violations}"
    )
    return Check("CCA algorithm scope", passed, detail)


def check_simulink_model() -> Check:
    model = ROOT / "simulations" / "matlab" / "cca_nmpc_closed_loop.slx"
    builder = ROOT / "simulations" / "matlab" / "build_model.m"
    if not model.is_file() or not builder.is_file():
        return Check("Simulink closed loop", False, "model or builder missing")
    text = read(builder)
    required = (
        "CCA Reference",
        "Reference State",
        "Tracking Error e = Xhat - Xref",
        "NMPC-Lyapunov",
        "Mecanum Object",
        "Sensors and EKF",
        "Kinematics eta_dot = R(theta)v",
        "Dynamics dv = (u-v) over tau + d",
        "State update X(k+1)=X(k)+dt Xdot",
        "Constant body load d",
        "Sensor noise z=X+nu",
        "EKF estimate",
        "add_scope(path + \"/Position\"",
        "add_scope(path + \"/Velocity\"",
        "add_scope(path + \"/Trajectory\"",
        "Reference Log",
        "True State Log",
        "Estimated State Log",
        "Diagnostics Log",
        "add_scope(path + \"/Covariance scope\"",
    )
    missing = [item for item in required if item not in text]
    forbidden = [
        item
        for item in ("Human Observation", "Replan Request", "Governed CCA-NMPC")
        if item in text
    ]
    passed = not missing and not forbidden
    detail = (
        "nonlinear Mecanum kinematics/dynamics with load, noise, and EKF"
        if passed
        else f"missing={missing}; forbidden={forbidden}"
    )
    return Check("Simulink closed loop", passed, detail)


def check_cca_implementation() -> Check:
    planner = read(ROOT / "simulations" / "python" / "planner.py")
    study = read(ROOT / "simulations" / "python" / "study.py")
    required = (
        "def observe_context(",
        "gates @ joined + bias",
        "def plan_local_path(",
        "def _shifted_seed(",
        "def _repair_candidate(",
        "candidate_budget",
        "decode_budget",
        "global_path_unchanged",
        'path_source="previous_unvalidated"',
        '"same_registered_local_segment": True',
        '"paired_contrasts"',
        '"observed_human_clearance_m"',
        '"GLT": "replan-trigger-only"',
        '"P": "every-valid-observation"',
        '"nmpc_backend_included": False',
        '"human_trajectory_generated": False',
    )
    text = planner + "\n" + study
    missing = [item for item in required if item not in text]
    forbidden = [
        item
        for item in (
            "human_trajectory_generated\": True",
            "human_path",
            "applied_command",
            "nmpc.solve",
        )
        if item in text.lower()
    ]
    passed = not missing and not forbidden
    detail = (
        "Python LSTM-GA local-path boundary"
        if passed
        else f"missing={missing}; forbidden={forbidden}"
    )
    return Check("CCA implementation", passed, detail)


def check_motion_contract() -> Check:
    controller = read(ROOT / "simulations" / "matlab" / "nmpc_controller.m")
    checks = read(ROOT / "simulations" / "matlab" / "run_checks.m")
    required = (
        "function states = predictionStates",
        "lowerCommand(:) - commands(:)",
        "stateMargin",
        'config.controllerMode = "terminal_nmpc"',
        "invalidPlan.feasible",
        "invalidGate.fallbackUsable",
        "baselineFeasible",
        'closedLoop.evidenceScope == "nmpc_lyapunov_only"',
        "maximumLyapunovResidual",
    )
    text = controller + "\n" + checks
    missing = [term for term in required if term not in text]
    return Check(
        "motion-control contract",
        not missing,
        "static obligations present" if not missing else ", ".join(missing),
    )


def check_sil_harness() -> Check:
    path = ROOT / "experiments" / "run_sil.py"
    if not path.is_file():
        return Check("SIL harness", False, "experiments/run_sil.py is missing")
    text = read(path)
    required = (
        "CompiledController",
        "encode_stm32_velocity_command",
        "Astra-S adapter contract",
        "N10P adapter contract",
        '"hardware_run": False',
        '"ros_enabled": False',
    )
    missing = [item for item in required if item not in text]
    return Check(
        "SIL harness",
        not missing,
        "C++ NMPC and hardware contracts" if not missing else ", ".join(missing),
    )


def check_repair_contract() -> Check:
    text = read(VAULT / "03_Theory" / "cca-trajectory-generation.md")
    normalized = " ".join(text.split()).lower()
    required = (
        "bounded deterministic repair",
        "operatorname{Plan}_{CCA}",
        "mathcal P_k^{loc}",
        "mathcal C_P",
        "M+1",
        "longitudinal stations remain fixed",
        "guaranteed-success claim",
        "time-parameterization belongs to NMPC",
        "swept-footprint clearance",
        "previous valid local path",
        "registered generation, candidate, and decoder budgets",
        "integrated squared curvature",
    )
    missing = [term for term in required if term.lower() not in normalized]
    return Check(
        "GA repair contract",
        not missing,
        "CCA local path and NMPC conversion separated"
        if not missing
        else ", ".join(missing),
    )


def check_comments() -> Check:
    roots = [ROOT / "simulations" / "python", ROOT / "simulations" / "matlab"]
    long_comments = []
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() not in {".py", ".m"} or not path.is_file():
                continue
            marker = "#" if path.suffix.lower() == ".py" else "%"
            for number, line in enumerate(read(path).splitlines(), start=1):
                if line.lstrip().startswith(marker) and len(line) > 79:
                    long_comments.append(f"{path.relative_to(ROOT)}:{number}")
    return Check("short simulation comments", not long_comments, "valid" if not long_comments else ", ".join(long_comments))


def check_paper_firewall() -> Check:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "*.tex", "*.pdf"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    changed = result.stdout.strip()
    return Check("local paper firewall", not changed, "Overleaf-only" if not changed else changed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.implementation_only:
        checks = [
            check_layout(),
            check_model_parity(),
            check_algorithm_scope(),
            check_simulink_model(),
            check_cca_implementation(),
            check_motion_contract(),
            check_sil_harness(),
            check_comments(),
            check_paper_firewall(),
        ]
        for check in checks:
            state = "PASS" if check.passed else "FAIL"
            print(f"[{state}] {check.name}: {check.detail}")
        print(json.dumps({"passed": sum(c.passed for c in checks), "total": len(checks)}))
        return 0 if all(check.passed for check in checks) else 1
    repository_exit = run_repository_gate()
    notes = sorted(VAULT.rglob("*.md"))
    checks = [
        Check(
            "repository contract gate",
            repository_exit == 0,
            "complete" if repository_exit == 0 else "evidence freeze remains open",
        ),
        check_files(),
        check_frontmatter(notes),
    ]
    checks.extend(check_graph(notes))
    checks.extend(
        [
            check_dois(notes),
            check_gap(),
            check_closest_work(),
            check_baselines(),
            check_layout(),
            check_model_parity(),
            check_algorithm_scope(),
            check_simulink_model(),
            check_cca_implementation(),
            check_motion_contract(),
            check_repair_contract(),
            check_comments(),
            check_paper_firewall(),
        ]
    )
    for check in checks:
        state = "PASS" if check.passed else "FAIL"
        print(f"[{state}] {check.name}: {check.detail}")
    print(json.dumps({"passed": sum(c.passed for c in checks), "total": len(checks)}))
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
