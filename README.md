# TER - Analysis of neutral votes in Opinion-Based Argumentation Frameworks

Research software for analyzing Opinion-Based Argumentation Frameworks (OBAFs) through the COSAR and CSS algorithms. This project evaluates how different vote-aggregation strategies, including those that account for neutral votes, recover the given truth extension under varied agent reliability and group configurations. This work is very useful for understanding the impact of neutral opinions in collective decision-making processes such as online debates, or polling scenarios. 

**Context:** Master's research work (M1 in Distributed Artificial Intelligence, Paris Cité University). The research extends the OBAF framework introduced in *Collective Satisfaction Semantics for Opinion Based Argumentation* by proposing new vote-aggregation strategies taking into account neutral votes from agents, and evaluating their efficiency in finding the truth extension in an OBAF.

**Core algorithms:**
- **COSAR**: Derives argument scores from agent votes using multiple aggregation methods. Prunes attacks incompatible with score ordering and computes extensions on the newly pruned framework.
- **CSS**: Ranks extensions by measuring collective agent satisfaction under different vote-aggregation policies.

**Main entry point:** `src/cli.py` — Run all commands from the project root.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Setup

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Algorithms

### COSAR: Score-Based Attack Pruning

Given arguments, attacks, and distributed votes, COSAR aggregates votes to compute credibility scores for each argument, removes attacks that violate the score ordering, and computes extensions on the pruned framework.

For an attack $x \to y$, the attack is retained iff $\text{score}(x) \geq \text{score}(y)$.

**Aggregation methods:**

To see details on each method, refer to `definitions.md` and `wct.md`.
All methods are available via `--aggregation-method` in the CLI.

### CSS: Collective Satisfaction Ranking

Ranks extensions under a chosen semantics (PR, CO, etc.) by measuring how well each extension satisfies distributed agent preferences.

**Parameters:**
- Measure: $S$ (support), $D$ (dissatisfaction), $U$ (utility)
- Aggregation: `sum`, `min`, `leximax`, `leximin`

## CLI: Four Workflows

The CLI provides four workflows: `run` (single-instance analysis), `convert` (batch OBAF generation), `eval` (batch algorithm evaluation), and `plot` (efficiency visualization).

### 1. Run Workflow: Single-Instance Analysis

Executes COSAR or CSS on one test file or custom input.

```bash
# Interactive mode
python src/cli.py run

# Direct analysis (COSAR)
python src/cli.py run --algorithm cosar --file as_01.apx

# With specific aggregation
python src/cli.py run --file as_01.apx --aggregation-method bayesian

# CSS analysis
python src/cli.py run --algorithm css --file as_01.apx --semantics PR --measure U --agg sum

# Custom input
python src/cli.py run --algorithm cosar \
  --args '["a", "b", "c"]' \
  --atts '[["a", "b"], ["b", "c"]]' \
  --votes '{"A": {"a": 1, "b": -1}, "B": {"c": 1}}'
```

**Options:**
- `--algorithm {cosar,css}` — Algorithm to run (default: cosar)
- `--file FILE` — APX file from `data/test/`
- `--args`, `--atts`, `--votes` — Custom input (all three required together)
- `--semantics` — Semantics for extension enumeration: CF/AD/ST/CO/PR/GR/ID/SST (default: PR)
- `--aggregation-method {base,neutral-aware,wct,bayesian}` — COSAR mode (default: base)
- `--measure {S,D,U}` — CSS measure (default: U)
- `--agg {sum,min,leximax,leximin}` — CSS aggregation (default: sum)
- `--no-write` — Don't write COSAR output file
- `--show-input` — Display parsed framework before execution

**Interactive menu** (when no `--file` is provided):
- `<number>` — Select and run file
- `v<number>` — View file contents
- `a` — Switch algorithm
- `s` — Set semantics
- `m`/`p` — Configure algorithm parameters
- `q` — Quit

### 2. Convert Workflow: Generate OBAFs

Converts all AF instances in `data/AF/` into OBAFs in `data/OBAF/` by generating votes and based on the given parameters.

The AF given in this repository have been given to us as base dataset to generate OBAFs. You can find the details of the generation process in `data/AF/Info_generation.txt`. 

```bash
python src/cli.py convert
```

For each AF file, generates $2 \times 9 \times 6 \times 2 = 216$ OBAFs by varying:
- Semantics: PR (Preferred), CO (Complete)
- Reliability: {0.2, 0.3, ..., 1.0}
- Agents: {5, 10, 15, 20, 25, 30}
- Distribution: uniform, average

In total, 18,144 OBAFs will be generated from the 84 AFs in the dataset.

**Output:**
- OBAFs: `data/OBAF/{BA,WS}/`
- Index: `data/OBAF/obaf_metadata.csv`

### 3. Eval Workflow: Score All OBAFs

Evaluates all generated OBAFs using each aggregation method by recording which methods recover the ground-truth extension.

```bash
python src/cli.py eval
```

For each OBAF, runs:
- COSAR (base, neutral-aware, Bayesian)
- WCT (weighted credibility framework)
- CSS (utility measure with sum aggregation)

Records a score of 1 if the algorithm returns exactly the ground-truth extension, 0 otherwise.
Scores are appended to `data/OBAF/obaf_metadata.csv` for later analysis.

### 4. Plot Workflow: Efficiency Visualization

Generates efficiency graphs (% of OBAFs where each algorithm succeeded) vs. agent reliability, filtered by parameters.

```bash
# All data
python src/cli.py plot

# PR semantics only
python src/cli.py plot --plot-semantics PR

# Subset of agent counts
python src/cli.py plot --plot-agents 5,10,15
```

**Options:**
- `--plot-metadata PATH` — Metadata CSV (default: `data/OBAF/obaf_metadata.csv`)
- `--plot-semantics {all,PR,CO}` — Filter by semantics (default: all)
- `--plot-agents AGENTS` — Comma-separated agent counts (valid presets: 5, 5,10, 5,10,15, 5,10,15,20, 5,10,15,20,25, 5,10,15,20,25,30; default: all)
- `--plot-distribution {all,uniform,average}` — Filter by distribution type (default: all)

## APX Format

APX files contains the definition of an OBAF instance. We extended the standard APX format to include agent votes. The format is as follows:

```
agt(Agent1, Agent2, ...).    # All voting agents (mandatory, once only)
arg(argument).               # Arguments (one per line)
att(attacker, target).       # Attacks (one per line)
vot(Agent, argument, vote).  # Votes (one per line)
```

**Vote values:** `-1` (against), `1` (in favor). Neutral votes are automatically inferred for any agent-argument pair not explicitly voted on.

**Constraints:** All agents and arguments referenced in votes/attacks must be declared. No duplicate votes per agent-argument pair.

## References

- *Juliete Rossie, Jérôme Delobelle, Sébastien Konieczny, Clément Lens, Srdjan Vesic. Collective Satisfaction Semantics for Opinion Based Argumentation. 21st International Conference on Principles of Knowledge Representation and Reasoning KR-2023, Nov 2024, Hanoi, Vietnam. pp.631-641, ⟨10.24963/kr.2024/59⟩.*
- *Jean-Guy Mailly. pygarg: A Python Engine for Argumentation. IRIT/RR–2024–02–FR, IRIT - Institut de Recherche en Informatique de Toulouse. 2024.*

## License and Attribution

This is open-source research software. Citation is not required but greatly appreciated.