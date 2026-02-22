def apx_parser(file_path: str):
    """
        Parse the arguments, attacks, and votes from the given file.
    """
    arguments = []
    attacks = []
    votes = {}
    with open(file_path, 'r') as f:
        line_counter = 0
        for line in f:
            line_counter += 1
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            
            if line.startswith('arg'):
                arg = _parse_arg(line, file_path, line_counter)
                arguments.append(arg)
            elif line.startswith('att'):
                att = _parse_att(line, file_path, line_counter)
                attacks.append(att)
            elif line.startswith('vot'):
                vote = _parse_vote(line, file_path, line_counter)
                # Use the update method to only add the last vote in case of multiple votes for the same (agent, argument) pair
                votes.update(vote)
            else:
                raise ValueError(f"Invalid line format: {line}. Expected lines to start with 'arg', 'att', or 'vot', line {line_counter}, in {file_path}.")
    return arguments, attacks, votes

def _parse_arg(line: str, file_path: str, line_number: int) -> str:
    """
        Parse the argument from the given line and return it as a string.
    """
    # Extract the content inside the parentheses
    content = line[line.find('(') + 1:line.rfind(')')]
    arg = content.strip()
    if not arg:
        raise ValueError(f"Invalid line format: {line}. Expected format: 'arg(argument)', line {line_number}, in {file_path}.")
    return arg

def _parse_att(line: str, file_path: str, line_number: int) -> list[str]:
    """
        Parse the attack from the given line and return it as a list of two strings: [attacker, target].
    """
    # Extract the content inside the parentheses
    content = line[line.find('(') + 1:line.rfind(')')]
    parts = [p.strip() for p in content.split(',')]
    if len(parts) != 2:
        raise ValueError(f"Invalid line format: {line}. Expected format: 'att(attacker, target)', line {line_number}, in {file_path}.")
    return parts

def _parse_vote(line: str, file_path: str, line_number: int) -> dict[tuple[str, str], int]:
    """
        Parse the votes from the given file and return a dict of this form:
        {
            (agent, argument): vote
        }
    """
    # Extract the content inside the parentheses
    content = line[line.find('(') + 1:line.rfind(')')]
    parts = [p.strip() for p in content.split(',')]
    if len(parts) != 3:
        raise ValueError(f"Invalid line format: {line}. Expected format: 'vot(agent, argument, vote)'")
    agent, argument, vote_str = parts

    # Check if the vote is a valid value
    if vote_str not in ['-1', '0', '1']:
        raise ValueError(f"Invalid vote value: {vote_str}. Expected '-1', '0', or '1', line {line_number}, in {file_path}.")

    return {(agent, argument): int(vote_str)}