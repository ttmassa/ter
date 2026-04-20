import argparse
from pathlib import Path
from statistics import median
from parser import read_apx, display_parsed_content
from cosar import aggregate_votes
from pygarg.dung import solver


def compute_force(agg):
    """
        Compute the force of each argument using the formula given in wct.md.
    """
    result = {}
    for arg, (v_minus, v_zero, v_plus) in agg.items():
        total = v_plus + v_minus + v_zero
        result[arg] = (v_plus + 0.5 * v_zero) / total if total > 0 else 0.0
    return result


def compute_stability(agg):
    """
        Compute the stability of each argument using the formula given in wct.md.
    """
    result = {}
    for arg, (v_minus, v_zero, v_plus) in agg.items():
        total = v_plus + v_minus + v_zero
        result[arg] = v_zero / total if total > 0 else 0.0
    return result


def compute_attack_weights(atts, tau, stab):
    """
        Compute the weight of each attack using the formula given in wct.md.
    """
    return {(x, y): max(0.0, tau[x] - stab[y]) for x, y in atts}


def compute_cost(ext, weights):
    """
        Compute the cost of an extension using the formula given in wct.md.
    """
    return sum(w for (x, y), w in weights.items() if x in ext and y in ext)


def run(args, atts, votes, semantics, k=None):
    # Aggregate votes and compute force, stability, and attack weights
    agg = aggregate_votes(args, votes)
    tau = compute_force(agg)
    stab = compute_stability(agg)
    weights = compute_attack_weights(atts, tau, stab)

    # Determine the tolerance threshold K (endogenous or manual)
    if k is None:
        k, k_method = compute_endogenous_k(weights)
    else:
        k_method = "manual"

    pruned_zero = [[x, y] for x, y in atts if weights[(x, y)] > 0]
    pruned_k = [[x, y] for x, y in atts if weights[(x, y)] > k]

    # Collect candidate extensions
    candidates = set()
    for graph in [atts, pruned_zero, pruned_k]:
        for ext in solver.extension_enumeration(args, graph, semantics):
            candidates.add(frozenset(ext))

    # Filter valid extensions based on cost and keep only maximal ones
    valid = [e for e in candidates if compute_cost(e, weights) <= k]
    maximal = [e for e in valid if not any(e < other for other in valid)]
    solutions = [sorted(e) for e in maximal]

    return solutions, agg, tau, stab, weights, k, k_method


def main():
    ap = argparse.ArgumentParser(description="WCT solver for OBAF")
    ap.add_argument("file", help=".apx file (path or name in data/)")
    ap.add_argument("-k", type=float, default=None, help="Manual tolerance threshold K (omit for endogenous)")
    ap.add_argument("--semantics", default="PR", help="Base semantics for pygarg (default: PR)")
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--show-input", action="store_true")
    cli = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / "data"
    candidate = Path(cli.file)
    if not candidate.is_absolute():
        in_data = data_dir / cli.file
        candidate = in_data if in_data.exists() else candidate

    args, atts, votes = read_apx(str(candidate.resolve()))

    if cli.show_input:
        display_parsed_content(args, atts, votes)

    maximal, agg, tau, stab, weights, k, k_method = run(args, atts, votes, cli.semantics, cli.k)

    if cli.verbose:
        print("\nForce / Stability:")
        for a in args:
            print(f"  {a}:  tau={tau[a]:.4f}  stab={stab[a]:.4f}")
        print("\nAttack weights:")
        for (x, y), w in weights.items():
            label = "absorbed" if w == 0 else ("tolerable" if w <= k else "kept")
            print(f"  W({x} -> {y}) = {w:.4f}  [{label}]")

    print(f"\nK = {k:.4f}  [{k_method}]  |  Semantics = {cli.semantics}")
    print("WCT extensions:")
    if not maximal:
        print("  (none)")
    for e in maximal:
        c = compute_cost(e, weights)
        print(f"  {{{', '.join(sorted(e))}}}  (cost={c:.4f})")


# ---------------------------------------------------------------------------
# Endogenous K — Natural Break Method
# ---------------------------------------------------------------------------

def compute_endogenous_k(weights):
    w_act = sorted(w for w in weights.values() if w > 0)
    m = len(w_act)

    if m == 0:
        return 0.0, "endogenous/no-active-attacks"

    if m == 1:
        return w_act[0], "endogenous/single-attack"

    gaps = [w_act[i + 1] - w_act[i] for i in range(m - 1)]
    gap_max = max(gaps)

    if m == 2:
        return w_act[gaps.index(gap_max)], "endogenous/natural-break"

    other_gaps = [g for g in gaps if g != gap_max]
    mean_others = sum(other_gaps) / len(other_gaps) if other_gaps else 0.0

    if gap_max >= 2 * mean_others:
        i_star = gaps.index(gap_max)
        return w_act[i_star], "endogenous/natural-break"

    return median(w_act), "endogenous/median-fallback"


if __name__ == "__main__":
    main()
