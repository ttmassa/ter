import random

class OBAF:
    def __init__(self, args: list[str], atts: list[list[str]], agents: list[str], votes: dict[str, dict[str, int]]):
        self.args = args
        self.atts = atts
        self.agents = agents
        self.votes = votes
        # Check for any potential issues
        self._validate()

    def aggregate_votes(self) -> dict[str, list[int]]:
        """
            Compute the score of each argument based on the votes and return it in this format:
            {
                argument: [v_minus, v_zero, v_plus]
            }
        """
        aggregate_votes = {arg: [0, 0, 0] for arg in self.args}
        for _, arguments_dict in self.votes.items():
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
    
    def generate_vote(self, agent: str, truth: list[str], reliability: float):
        """
            Generate votes on all arguments for the given agent based on a target reliability.

            Reliability is computed against the expected truth-sign vector where:
            - exact match counts as 1.0
            - neutral vote (0) counts as 0.5
            - opposite sign counts as 0.0

            For reliability 0 and 1, generation is deterministic.
            For intermediate reliabilities, the method samples candidates and keeps
            the first one within tolerance, otherwise the best candidate found.
        """
        if agent not in self.agents:
            raise ValueError(f"Agent '{agent}' is not part of the agents list.")
        for t in truth:
            if t not in self.args:
                raise ValueError(f"Truth argument '{t}' is not part of the arguments list.")
        if not (0 <= reliability <= 1):
            raise ValueError(f"Reliability must be between 0 and 1, got: {reliability}")
        if not self.args:
            raise ValueError("Cannot generate votes without arguments.")
        
        # Truth-sign vector: +1 for the true argument, -1 for all others
        truth_vector = [1 if arg in truth else -1 for arg in self.args]

        # Deterministic extremes
        if reliability == 1:
            generated_vote = truth_vector.copy()
            self.votes[agent] = {arg: vote for arg, vote in zip(self.args, generated_vote)}
            return
        if reliability == 0:
            generated_vote = [-vote for vote in truth_vector]
            self.votes[agent] = {arg: vote for arg, vote in zip(self.args, generated_vote)}
            return

        def compute_reliability(vote_vector: list[int]) -> float:
            score = 0.0
            for vote, truth_sign in zip(vote_vector, truth_vector):
                if vote == truth_sign:
                    score += 1.0
                elif vote == 0:
                    score += 0.5
            return score / len(truth_vector)

        # Probabilities chosen so expected per-argument score equals target reliability:
        # P(correct)=r^2, P(neutral)=2r(1-r), P(wrong)=(1-r)^2
        p_correct = reliability * reliability
        p_neutral = 2 * reliability * (1 - reliability)

        # Max attemps to find a candidate within tolerance before settling for the best found
        max_attempts = 1000
        round_number = 1
        tolerance = 0.25 / len(self.args)
        best_vote = truth_vector.copy()
        best_error = abs(compute_reliability(best_vote) - reliability)

        for _ in range(max_attempts):
            candidate_vote = []
            for truth_sign in truth_vector:
                draw = random.random()
                if draw < p_correct:
                    candidate_vote.append(truth_sign)
                elif draw < p_correct + p_neutral:
                    candidate_vote.append(0)
                else:
                    candidate_vote.append(-truth_sign)

            candidate_reliability = compute_reliability(candidate_vote)
            error = abs(candidate_reliability - reliability)
            round_number += 1

            if error < best_error:
                best_error = error
                best_vote = candidate_vote

            if error <= tolerance:
                best_vote = candidate_vote
                break
        
        # Update the votes for the agent
        self.votes[agent] = {arg: vote for arg, vote in zip(self.args, best_vote)}
        print(f"\nGenerated vote for agent '{agent}': {self.votes[agent]} with reliability {compute_reliability(best_vote):.2f} in {round_number} round{"s" if round_number > 1 else ""} (target: {reliability:.2f})")
        return best_vote
    
    def generate_votes(self, truth: list[str], reliability: float, distribution_type: str):
        """
            Generate votes for all agents based on a target reliability against the given truth.
        """
        if distribution_type == "uniform":
            for agent in self.agents:
                self.generate_vote(agent, truth, reliability)
        elif distribution_type == "average":
            agent_count = len(self.agents)
            target_total_reliability = reliability * agent_count
            sampled_reliabilities = []
            assigned_total_reliability = 0.0

            # Draw random reliabilities for all but the last agent.
            # Bounds keep each draw in [0, 1] while still allowing an exact final average.
            for index in range(agent_count - 1):
                remaining_agents = agent_count - index - 1
                # Calculate the minimum and maximum allowed reliability for the current agent
                min_allowed_reliability = max(
                    0.0,
                    target_total_reliability - assigned_total_reliability - remaining_agents,
                )
                max_allowed_reliability = min(
                    1.0,
                    target_total_reliability - assigned_total_reliability,
                )
                # Draw a random reliability for the current agent within the allowed bounds
                sampled_reliability = random.uniform(min_allowed_reliability, max_allowed_reliability)
                sampled_reliabilities.append(sampled_reliability)
                assigned_total_reliability += sampled_reliability

            # The last value closes the sum so the global average matches the target.
            last_reliability = target_total_reliability - assigned_total_reliability
            sampled_reliabilities.append(min(1.0, max(0.0, last_reliability)))

            # Shuffle to avoid positional bias (first agents would otherwise follow the same pattern).
            random.shuffle(sampled_reliabilities)
            for agent, agent_reliability in zip(self.agents, sampled_reliabilities):
                self.generate_vote(agent, truth, agent_reliability)

            achieved_average = sum(sampled_reliabilities) / len(sampled_reliabilities)
            print(
                f"Assigned random reliabilities with average {achieved_average:.2f} (target: {reliability:.2f})."
            )
        else:
            raise ValueError(f"Unsupported distribution type: {distribution_type}. Supported types: 'uniform', 'average'.")
    
    def __str__(self):
        """
            Display the parsed arguments, attacks, and votes in a readable format.
        """
        formatted_args = "[" + ", ".join(f'\'{arg}\'' for arg in self.args) + "]"
        formatted_atts = "[" + ", ".join(
            f'[\'{attacker}\', \'{target}\']' for attacker, target in self.atts
        ) + "]"
        formatted_agts = "[" + ", ".join(f'\'{agent}\'' for agent in self.votes.keys()) + "]"
        # Format votes in nested structure: {agent: {argument: vote, ...}, ...}
        agent_votes_list = []
        for agent in sorted(self.votes.keys()):
            arg_votes = ", ".join(
                f"{arg}: {self.votes[agent][arg]}" for arg in sorted(self.votes[agent].keys())
            )
            agent_votes_list.append(f"{agent}: {{{arg_votes}}}")
        formatted_votes = "{" + ", ".join(agent_votes_list) + "}"

        print(f"Arguments: {formatted_args}")
        print(f"Attacks: {formatted_atts}")
        print(f"Agents: {formatted_agts}")
        print(f"Votes: {formatted_votes}")

    def _validate(self):
        """
            Validate the OBAF structure
        """
        # Start by adding the empty set argument to the arguments list
        if '∅' not in self.args:
            self.args.append('∅') 
        # Make sure every agent has a vote for every argument, filling in 0 for missing votes
        for agent in self.agents:
            if agent not in self.votes:
                self.votes[agent] = {arg: 0 for arg in self.args}
            else:
                for arg in self.args:
                    if arg not in self.votes[agent]:
                        self.votes[agent][arg] = 0
        # Check for any invalid agents
        for agent in self.votes.keys():
            if agent not in self.agents:
                raise ValueError(f"Agent '{agent}' has votes but is not declared in the agents list.")
        # Check for any invalid arguments in votes
        for agent, arguments_dict in self.votes.items():
            for argument in arguments_dict.keys():
                if argument not in self.args:
                    raise ValueError(f"Argument '{argument}' has votes from agent '{agent}' but is not declared in the arguments list.")
        # Check for any invalid vote values
        for agent, arguments_dict in self.votes.items():
            for argument, vote in arguments_dict.items():
                if vote not in [-1, 0, 1]:
                    raise ValueError(f"Invalid vote value: {vote} from agent '{agent}' for argument '{argument}'. Expected -1, 0, or 1.")
        # Check for duplicate votes (same agent voting on the same argument twice)
        for agent, arguments_dict in self.votes.items():
            for argument in arguments_dict.keys():
                if list(arguments_dict.keys()).count(argument) > 1:
                    raise ValueError(f"Duplicate vote from agent '{agent}' for argument '{argument}'.")
                
if __name__ == "__main__":
    # More complex example usage
    args = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    atts = [
        ['a', 'b'], ['a', 'd'],
        ['b', 'a'], ['b', 'e'],
        ['c', 'b'], ['c', 'f'],
        ['d', 'c'], ['d', 'g'],
        ['e', 'd'], ['e', 'h'],
        ['f', 'e'], ['f', 'i'],
        ['g', 'f'], ['g', 'j'],
        ['h', 'g'], ['h', 'a'],
        ['i', 'h'], ['i', 'c'],
        ['j', 'i'], ['j', 'b']
    ]
    agents = ['agent1', 'agent2', 'agent3', 'agent4', 'agent5', 'agent6']
    votes = {
        'agent1': {
            'a': 1, 'b': -1, 'c': -1, 'd': 0, 'e': -1,
            'f': 1, 'g': 0, 'h': -1, 'i': 1, 'j': -1
        },
        'agent2': {
            'a': -1, 'b': 1, 'c': 0, 'd': -1, 'e': 1,
            'f': -1, 'g': 0, 'h': 1, 'i': -1, 'j': 1
        },
        'agent3': {
            'a': 0, 'b': 1, 'c': -1, 'd': 1, 'e': 0,
            'f': -1, 'g': 1, 'h': -1, 'i': 0, 'j': 1
        },
        'agent4': {
            'a': 1, 'b': 0, 'c': 1, 'd': -1, 'e': -1,
            'f': 0, 'g': -1, 'h': 1, 'i': -1, 'j': 0
        },
        'agent5': {
            'a': -1, 'b': -1, 'c': 1, 'd': 1, 'e': 0,
            'f': 1, 'g': -1, 'h': 0, 'i': 1, 'j': -1
        },
        'agent6': {
            'a': 0, 'b': 0, 'c': -1, 'd': 1, 'e': 1,
            'f': -1, 'g': 1, 'h': 0, 'i': -1, 'j': 1
        }
    }
    obaf = OBAF(args, atts, agents, votes)
    obaf.__str__()
    obaf.generate_votes(['a', 'b'], 0.6, distribution_type="average")

