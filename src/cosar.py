from pygarg.dung import solver
from OBAF import OBAF

def compute_scores(obaf: OBAF) -> dict[str, float]:
    """
        Aggregate the score of each argument using the formula given in the paper.    
    """
    EPS = 0.1
    aggregate_votes = obaf.aggregate_votes()
    scores = {}
    for arg, votes in aggregate_votes.items():
        v_minus, _, v_plus = votes
        if v_plus == 0 and v_minus == 0:
            scores[arg] = 0.0
        else:
            scores[arg] = round(v_plus / (v_minus + v_plus + EPS), 3)
    return scores

def compute_neutral_aware_score(obaf: OBAF) -> dict[str, float]:
    """
        Compute the neutral-aware score of each argument using the formula given in definitions.md. 
    """
    # Start by computing the base scores using the original formula
    base_scores = compute_scores(obaf)
    aggregate_votes = obaf.aggregate_votes()
    scores = {}

    for arg, votes in aggregate_votes.items():
        v_minus, v_zero, v_plus = votes
        base_score = base_scores[arg]

        total_votes = v_minus + v_zero + v_plus
        decided_votes = v_minus + v_plus

        # Neutral proportion
        neutral_proportion = (v_zero / total_votes) if total_votes > 0 else 0.0

        # Dividing-power index (DPI)
        dpi = (abs(v_plus - v_minus) / decided_votes) if decided_votes > 0 else 0.0

        # Neutral influence coefficient (NIC)
        nic = min(1.0, neutral_proportion * dpi)

        # Final neutral-aware score
        scores[arg] = round((1 - nic) * base_score + nic * 0.5, 3)
    return scores

def compute_bayesian_score(obaf: OBAF) -> dict[str, float]:
    """
        Compute the neutral-aware score of each argument using the Bayesian approach defined in definitions.md.
        The neutral vote weight is fixed at 0.5.
    """
    EPSILON = 0.1
    NEUTRAL_WEIGHT = 0.5
    scores = {}
    aggregate_votes = obaf.aggregate_votes()
    for arg, votes in aggregate_votes.items():
        v_minus, v_zero, v_plus = votes
        numerateur = v_plus + (v_zero * NEUTRAL_WEIGHT)
        denominateur = v_plus + v_minus + v_zero + EPSILON
        scores[arg] = round(numerateur / denominateur, 3)
    return scores

def prune_attacks(atts: list[list[str]], scores: dict[str, float]) -> list[list[str]]:
    """
        Prune the attacks based on the scores of the arguments. If an argument with a lower score attacks an argument with a higher score, the attack is pruned.
    """
    pruned_atts = []
    for attacker, target in atts:
        if scores[attacker] >= scores[target]:
            pruned_atts.append([attacker, target])
    return pruned_atts

        
def run(obaf: OBAF, semantics, aggregation_method="base", log = True):
    """
        Run the COSAR algorithm on the given argumentation system.
    """
    # Run the correct aggregation method based on the input parameter
    if aggregation_method == "wct":
        from wct import run as wct_run
        extensions, _, _, _, _, _, _ = wct_run(obaf, semantics)
        # WCT does not prune attacks, so we keep the original attacks for reporting
        pruned_atts = obaf.atts
    else:
        if aggregation_method == "neutral-aware" or aggregation_method == "na":
            scores = compute_neutral_aware_score(obaf)
        elif aggregation_method == "bayesian":
            scores = compute_bayesian_score(obaf)
        else:
            scores = compute_scores(obaf)

        if log:
            print(f"Scores ({aggregation_method}): {scores}")

        # Prune attacks based on the computed scores
        pruned_atts = prune_attacks(obaf.atts, scores)
        
        # Compute extensions using pygarg solver
        extensions = solver.extension_enumeration(obaf.args, pruned_atts, semantics)

    if log:
        print(f"Pruned Attacks ({aggregation_method}): {pruned_atts}")

    # Create a new OBAF with the pruned attacks for reporting
    pruned_obaf = OBAF(obaf.args, pruned_atts, obaf.agents, obaf.votes)

    # pygarg may return "NO" when no extension is found.
    # Normalize it so this function always returns a list.
    if extensions == "NO":
        return []
    return extensions, pruned_obaf

if __name__ == "__main__":
    # Example usage
    args = ["A", "B", "C"]
    atts = [["A", "B"], ["B", "C"], ["C", "A"]]
    agents = ["voter1", "voter2", "voter3", "voter4", "voter5", "voter6", "voter7", "voter8", "voter9", "voter10", "voter11", "voter12", "voter13", "voter14", "voter15", "voter16"]

    # Scenario designed to highlight the impact of neutral votes:
    # - A has very high base support but mostly neutral votes overall
    # - B has lower base support but more decided votes
    votes = {
        "voter1": {"A": 1, "B": 1, "C": -1},
        "voter2": {"A": 1, "B": 1, "C": -1},
        "voter3": {"A": 0, "B": 1, "C": -1},
        "voter4": {"A": 0, "B": 1, "C": -1},
        "voter5": {"A": 0, "B": 1, "C": -1},
        "voter6": {"A": 0, "B": 1, "C": -1},
        "voter7": {"A": 0, "B": -1, "C": 0},
        "voter8": {"A": 0, "B": -1, "C": 0},
        "voter9": {"A": 0, "B": 0, "C": 0},
        "voter10": {"A": 0, "B": 0, "C": 0},
        "voter11": {"A": 0, "B": 0, "C": 0},
        "voter12": {"A": 0, "B": 0, "C": 0},
        "voter13": {"A": 0, "B": 0, "C": 0},
        "voter14": {"A": 0, "B": 0, "C": 0},
        "voter15": {"A": 0, "B": 0, "C": 1},
        "voter16": {"A": 0, "B": 0, "C": 1}
    }
    obaf = OBAF(args, atts, agents, votes)

    # Base aggregation
    print("BASE AGGREGATION\n")
    extensions, _ = run(obaf, semantics="PR")
    print(f"Extensions: {extensions}\n")

    # Neutral-aware aggregation
    print("NEUTRAL-AWARE AGGREGATION\n")
    extensions_na, _ = run(obaf, semantics="PR", aggregation_method="neutral-aware")
    print(f"Extensions (neutral-aware): {extensions_na}\n")

    # WCT aggregation
    print("WCT AGGREGATION\n")
    extensions_wct, _ = run(obaf, semantics="PR", aggregation_method="wct")
    print(f"Extensions (wct): {extensions_wct}\n")

    # Bayesian aggregation
    print("BAYESIAN AGGREGATION\n")
    extensions_bayesian, _ = run(obaf, semantics="PR", aggregation_method="bayesian")
    print(f"Extensions (Bayesian): {extensions_bayesian}")
