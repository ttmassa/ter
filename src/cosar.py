from pygarg.dung import solver

def aggregate_votes(args: list[str], votes: dict[tuple[str, str], int]) -> dict[str, list[int]]:
    """
        Compute the score of each argument based on the votes and return it in this format:
        {
            argument: [v_minus, v_zero, v_plus]
        }
    """
    aggregate_votes = {arg: [0, 0, 0] for arg in args}
    for (_, argument), vote in votes.items():
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

def prune_attacks(atts: list[list[str]], scores: dict[str, float]) -> list[list[str]]:
    """
        Prune the attacks based on the scores of the arguments. If an argument with a lower score attacks an argument with a higher score, the attack is pruned.
    """
    pruned_atts = []
    for attacker, target in atts:
        if scores[attacker] >= scores[target]:
            pruned_atts.append([attacker, target])
    return pruned_atts

        
def run(args, atts, votes, semantics):
    """
        Run the COSAR algorithm on the given argumentation system.
    """
    aggregate = aggregate_votes(args, votes)
    scores = compute_scores(aggregate)
    pruned_atts = prune_attacks(atts, scores)

    # Compute extensions using pygarg solver
    extensions = solver.compute_some_extension(args, pruned_atts, semantics)

    return pruned_atts, extensions
    