from pygarg.dung import solver

def aggregate_votes(args: list[str], votes: dict[str, dict[str, int]]) -> dict[str, list[int]]:
    """
        Compute the score of each argument based on the votes and return it in this format:
        {
            argument: [v_minus, v_zero, v_plus]
        }
    """
    aggregate_votes = {arg: [0, 0, 0] for arg in args}
    for _, arguments_dict in votes.items():
        for argument, vote in arguments_dict.items():
            if argument in aggregate_votes:
                if vote == -1:
                    aggregate_votes[argument][0] += 1
                elif vote == 0:
                    aggregate_votes[argument][1] += 1
                elif vote == 1:
                    aggregate_votes[argument][2] += 1
                else:
                    raise ValueError(f"Invalid vote value: {vote}. Expected -1, 0, or 1.")
    return aggregate_votes

def compute_scores(aggregate_votes: dict[str, list[int]]) -> dict[str, float]:
    """
        Aggregate the score of each argument using the formula given in the paper.    
    """
    EPS = 0.1
    scores = {}
    for arg, votes in aggregate_votes.items():
        v_minus, _, v_plus = votes
        if v_plus == 0 and v_minus == 0:
            scores[arg] = 0.0
        else:
            scores[arg] = round(v_plus / (v_minus + v_plus + EPS), 3)
    return scores

def compute_neutral_aware_score(aggregate_votes: dict[str, list[int]], theta_low: float = 0.33, theta_high: float = 0.66) -> dict[str, float]:
    """
        Compute the neutral-aware score of each argument using the formula given in neutral_aware_definition.md. 
    """
    # Start by computing the base scores using the original formula
    base_scores = compute_scores(aggregate_votes)
    scores = {}

    for arg, votes in aggregate_votes.items():
        v_minus, v_zero, v_plus = votes
        base_score = base_scores[arg]

        total_votes = v_minus + v_zero + v_plus
        decided_votes = v_minus + v_plus

        # Neutral proportion
        neutral_proportion = (v_zero / total_votes) if total_votes > 0 else 0.0

        # Dividing-power index (DPI)
        dpi = (1 - (abs(v_plus - v_minus) / decided_votes)) if decided_votes > 0 else 0.0

        # Classify argument based on their DPI
        if dpi < theta_low:
            class_weight = 1.0
        elif dpi < theta_high:
            class_weight = 0.6
        else:
            class_weight = 0.3

        # Neutral influence coefficient (NIC)
        nic = min(1.0, class_weight * neutral_proportion)

        # Final neutral-aware score
        scores[arg] = round((1 - nic) * base_score + nic * 0.5, 3)
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

        
def run(args, atts, votes, semantics, aggregation_method="base"):
    """
        Run the COSAR algorithm on the given argumentation system.
    """
    aggregate = aggregate_votes(args, votes)
    # Run the correct aggregation method based on the input parameter
    if aggregation_method == "neutral-aware" or aggregation_method == "na":
        scores = compute_neutral_aware_score(aggregate)
    else:
        scores = compute_scores(aggregate)
    pruned_atts = prune_attacks(atts, scores)

    # Compute extensions using pygarg solver
    extensions = solver.compute_some_extension(args, pruned_atts, semantics)

    return pruned_atts, extensions

if __name__ == "__main__":
    # Example usage
    args = ["A", "B", "C"]
    atts = [["A", "B"], ["B", "C"], ["C", "A"]]

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

    # Base aggregation
    print("BASE AGGREGATION\n")
    pruned_atts, extensions = run(args, atts, votes, semantics="PR")
    print(f"Pruned Attacks: {pruned_atts}")
    print(f"Extensions: {extensions}\n")

    # Neutral-aware aggregation
    print("NEUTRAL-AWARE AGGREGATION\n")
    pruned_atts_na, extensions_na = run(args, atts, votes, semantics="PR", aggregation_method="neutral-aware")
    print(f"Pruned Attacks (Neutral-Aware): {pruned_atts_na}")
    print(f"Extensions (Neutral-Aware): {extensions_na}")
