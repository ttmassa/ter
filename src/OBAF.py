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

