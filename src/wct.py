import argparse
from pathlib import Path
from parser import read_apx, display_parsed_content
from cosar import aggregate_votes
from pygarg.dung import solver


def compute_force(agg):
    result = {}
    for arg, (v_minus, v_zero, v_plus) in agg.items():
        total = v_plus + v_minus + v_zero
        result[arg] = (v_plus + 0.5 * v_zero) / total if total > 0 else 0.0
    return result


def compute_stability(agg):
    result = {}
    for arg, (v_minus, v_zero, v_plus) in agg.items():
        total = v_plus + v_minus + v_zero
        result[arg] = v_zero / total if total > 0 else 0.0
    return result


def compute_attack_weights(atts, tau, stab):
    return {(x, y): max(0.0, tau[x] - stab[y]) for x, y in atts}


def compute_cost(ext, weights):
    return sum(w for (x, y), w in weights.items() if x in ext and y in ext)


def run(args, atts, votes, semantics, k):
    agg = aggregate_votes(args, votes)
    tau = compute_force(agg)
    stab = compute_stability(agg)
    weights = compute_attack_weights(atts, tau, stab)

    pruned_zero = [[x, y] for x, y in atts if weights[(x, y)] > 0]
    pruned_k = [[x, y] for x, y in atts if weights[(x, y)] > k]

    candidates = set()
    for graph in [atts, pruned_zero, pruned_k]:
        for ext in solver.extension_enumeration(args, graph, semantics):
            candidates.add(frozenset(ext))

    valid = [e for e in candidates if compute_cost(e, weights) <= k]
    maximal = [e for e in valid if not any(e < other for other in valid)]

    return maximal, agg, tau, stab, weights


def main():
    ap = argparse.ArgumentParser(description="WCT solver for OBAF")
    ap.add_argument("file", help=".apx file (path or name in data/)")
    ap.add_argument("-k", type=float, default=0.1, help="Tolerance threshold K (default: 0.1)")
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

    maximal, agg, tau, stab, weights = run(args, atts, votes, cli.semantics, cli.k)

    if cli.verbose:
        print("\nForce / Stability:")
        for a in args:
            print(f"  {a}:  tau={tau[a]:.4f}  stab={stab[a]:.4f}")
        print("\nAttack weights:")
        for (x, y), w in weights.items():
            label = "absorbed" if w == 0 else ("tolerable" if w <= cli.k else "kept")
            print(f"  W({x} -> {y}) = {w:.4f}  [{label}]")

    print(f"\nK = {cli.k}  |  Semantics = {cli.semantics}")
    print("WCT extensions:")
    if not maximal:
        print("  (none)")
    for e in maximal:
        c = compute_cost(e, weights)
        print(f"  {{{', '.join(sorted(e))}}}  (cost={c:.4f})")


if __name__ == "__main__":
    main()