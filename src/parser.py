import os
import random
from OBAF import OBAF
from pygarg.dung import solver

def read_apx(file_path: str) -> OBAF:
    """
        Parse the arguments, attacks, and votes from the given file.
    """
    # Validate file extension
    if not file_path.endswith('.apx'):
        raise ValueError(f"File extension must be .apx, got: {file_path}")

    arguments = []
    attacks = []
    agents = None
    vote_entries = []
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
            elif line.startswith('agt'):
                # Check for duplicate agent declaration lines
                if agents is not None:
                    raise ValueError(f"Duplicate agent declaration line, line {line_counter}, in {file_path}.")
                agents = _parse_agt(line, file_path, line_counter)
            elif line.startswith('vot'):
                vote = _parse_vote(line, file_path, line_counter)
                vote_entries.append((line_counter, vote))
            else:
                raise ValueError(f"Invalid line format: {line}. Expected lines to start with 'arg', 'att', 'agt', or 'vot', line {line_counter}, in {file_path}.")

    # Check for mandatory agent declaration line
    if agents is None:
        raise ValueError(f"Missing mandatory line 'agt(A, B, ...)' listing all voting agents, in {file_path}.")

    # Initialize votes dict with all agents and empty vote dicts
    votes = {agent: {} for agent in agents}
    for vote_line_number, vote in vote_entries:
        for agent, arguments_dict in vote.items():
            # Check for votes from undeclared agents
            if agent not in votes:
                raise ValueError(f"Vote for undeclared agent: {agent}, line {vote_line_number}, in {file_path}.")
            
            for argument, vote_value in arguments_dict.items():
                # Check for votes on non-existent arguments
                if argument not in arguments:
                    raise ValueError(f"Vote for non-existent argument: {argument}, line {vote_line_number}, in {file_path}.")
                # Check for duplicate votes (same agent voting on the same argument twice)
                if argument in votes[agent]:
                    raise ValueError(f"Duplicate vote from agent '{agent}' for argument '{argument}', line {vote_line_number}, in {file_path}.")
                votes[agent][argument] = vote_value
            
    # Add neutral votes for any arguments that were not voted on by an agent
    for agent in votes:
        for argument in arguments:
            if argument not in votes[agent]:
                votes[agent][argument] = 0
    
    return OBAF(arguments, attacks, agents, votes)

def write_apx(file_path: str, obaf: OBAF) -> None:
    """
        Write the arguments, attacks, and votes to the given file in the APX format.
    """
    # Validate file extension
    if not file_path.endswith('.apx'):
        raise ValueError(f"File extension must be .apx, got: {file_path}")

    output_dir = os.path.dirname(file_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(f"agt({', '.join(obaf.agents)}).\n")
        for arg in obaf.args:
            f.write(f"arg({arg}).\n")
        for att in obaf.atts:
            f.write(f"att({att[0]}, {att[1]}).\n")
        for agent, arguments_dict in obaf.votes.items():
            for argument, vote in arguments_dict.items():
                # Skip neutral votes since they are equivalent to missing votes
                if vote == 0:
                    continue
                f.write(f"vot({agent}, {argument}, {vote}).\n")

    print(f"Successfully wrote OBAF to file: {file_path}")

def af_to_obaf(file_path: str, semantics: str, reliability: float, number_of_agents: int, distribution_type: str):
    """
        Convert an AF file to an OBAF by generating votes according to a given semantics, reliability, number of agents, and distribution type. 
    """
    # Validate file extension
    if not file_path.endswith('.apx'):
        raise ValueError(f"File extension must be .apx, got: {file_path}")
    if semantics not in ['PR', 'CO']:
        raise ValueError(f"Unsupported semantics: {semantics}. Supported semantics: 'preferred', 'complete'.")
    if distribution_type not in ['uniform', 'average']:
        raise ValueError(f"Unsupported distribution type: {distribution_type}. Supported types: 'uniform', 'average'.")
    
    # Read the AF from the file (ignoring votes and agents if they are present)
    args = []
    atts = []
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
                args.append(arg)
            elif line.startswith('att'):
                att = _parse_att(line, file_path, line_counter)
                atts.append(att)
            elif line.startswith('agt') or line.startswith('vot'):
                # Ignore any agent or vote lines since we will generate new votes
                continue
            else:
                raise ValueError(f"Invalid line format: {line}. Expected lines to start with 'arg', 'att', 'agt', or 'vot', line {line_counter}, in {file_path}.")

    # Compute extensions using pygarg solver
    computed_extensions = solver.extension_enumeration(args, atts, semantics)
    # Pick a random extension as the truth for generating votes.
    if computed_extensions:
        truth_extension = computed_extensions[random.randint(0, len(computed_extensions) - 1)]
    else:
        truth_extension = ['']
    # Convert truth to a list of strings to match the expected format for generating votes
    truth_extension = [str(ext) for ext in truth_extension]
    
    # Use the computed extensions as the "truth" for generating votes
    agents = [f"agent{i+1}" for i in range(number_of_agents)]
    votes = {}
    obaf = OBAF(args, atts, agents, votes)    
    obaf.generate_votes(truth_extension, reliability, distribution_type)

    # Create a new OBAF file with the generated votes
    file_name = file_path.split('/')[-1]
    file_folder = file_path.split('/')[-2]
    truth_label = "" if not truth_extension else ''.join(truth_extension)
    # Create a new file name using the following format:
    # <original_file_name>-sem<semantics>-rel<reliability>-numAgt<number_of_agents>-dist<distribution_type>-truth<truth_extension>.apx
    new_file_name = file_name[:-4] + f"-sem{semantics}-rel{reliability:.1f}-numAgt{number_of_agents}-dist{distribution_type}-truth{truth_label}.apx"
    output_file_path = f'data/OBAF/{file_folder}/{new_file_name}'
    write_apx(output_file_path, obaf)

    return obaf, output_file_path, truth_extension
    
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

def _parse_agt(line: str, file_path: str, line_number: int) -> list[str]:
    """
        Parse the voting agents from the given line and return them as a list of strings.
    """
    content = line[line.find('(') + 1:line.rfind(')')]
    parts = [p.strip() for p in content.split(',')]
    if not parts or any(not part for part in parts):
        raise ValueError(f"Invalid line format: {line}. Expected format: 'agt(agent1, agent2, ...)', line {line_number}, in {file_path}.")
    if len(set(parts)) != len(parts):
        raise ValueError(f"Duplicate agent names in declaration line, line {line_number}, in {file_path}.")
    return parts

def _parse_vote(line: str, file_path: str, line_number: int) -> dict[str, dict[str, int]]:
    """
        Parse the vote from the given line and return a dict of this form:
        {
            agent: {
                argument: vote
            }
        }
    """
    # Extract the content inside the parentheses
    content = line[line.find('(') + 1:line.rfind(')')]
    parts = [p.strip() for p in content.split(',')]
    if len(parts) != 3:
        raise ValueError(f"Invalid line format: {line}. Expected format: 'vot(agent, argument, vote)'")
    agent, argument, vote_str = parts

    # Check if the vote is a valid value
    if vote_str not in ['-1', '1']:
        raise ValueError(f"Invalid vote value: {vote_str}. Expected '-1', or '1', line {line_number}, in {file_path}.")

    return {agent: {argument: int(vote_str)}}