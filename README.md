# TER - COSAR/CSS CLI

Command-line tool for two analyses of argumentation frameworks:

- `cosar`: prune attacks using vote-based argument scores.
- `css`: rank extensions using Collective Satisfaction Semantics.

Main entry point: `src/cli.py`.

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

### COSAR

Given arguments, attacks, and votes, COSAR computes a score for each argument, removes attacks that are incompatible with the score ordering, then computes extensions on the pruned framework.

For an attack $x \to y$, the attack is kept iff $score(x) \ge score(y)$.

#### Aggregation modes in the implementation

COSAR currently supports three score-based aggregation methods:

- `base` (default)
- `neutral-aware` (alias: `na`)
- `bayesian`

When the `bayesian` method is selected, neutral votes are treated as half a vote in favor (fixed weight `0.5`).

In addition, the CLI provides a `wct` mode through the same COSAR execution path (`--aggregation-method wct`).
This mode delegates scoring/selection to the weighted framework procedure defined in `wct.md`.

The COSAR algorithm used here is based on Section 4.3 in `Collective Satisfaction Semantics for Opinion Based Argumentation.pdf`.  
The base aggregation definition is given in Definition 23 of `Collective Satisfaction Semantics for Opinion Based Argumentation.pdf`.  
The neutral-aware aggregation definition is documented in `neutral_aware_definition.md`.  

### CSS

CSS ranks extensions computed under a chosen semantics using:

- measure in `{S, D, U}`
- aggregation in `{sum, min, leximax, leximin}`

## CLI usage

### Interactive mode

Run:

```bash
python src/cli.py
```

Interactive flow:

1. Choose algorithm (`cosar` or `css`).
2. Optionally set semantics.
3. Select a data file or use menu commands.

File-menu commands:

- `<number>`: run selected file
- `v<number>`: display parsed content of selected file
- `a`: switch algorithm
- `s`: set semantics
- `m`: configure COSAR aggregation (available only when algorithm is `cosar`)
- `p`: configure CSS parameters (available only when algorithm is `css`)
- `q`: quit

## Command-line options

```text
--algorithm {cosar,css}                 default: cosar
--file FILE                             APX file path or file name in data/
--args CUSTOM_ARGS                      custom arguments (Python literal list)
--atts CUSTOM_ATTS                      custom attacks (Python literal list)
--votes CUSTOM_VOTES                    custom votes (Python literal nested dict)
--no-write                              skip COSAR output file creation
--show-input                            display parsed input before execution
--semantics SEMANTICS                   default: PR
--aggregation-method {base,neutral-aware,wct,bayesian}
                                        default: base
--measure {S,D,U}                       default: U
--agg {sum,min,leximax,leximin}         default: sum
```

Valid semantics in interactive validation: `CF`, `AD`, `ST`, `CO`, `PR`, `GR`, `ID`, `SST`.

## Typical commands

COSAR on a file:

```bash
python src/cli.py --algorithm cosar --file as_01.apx
```

COSAR without writing output file:

```bash
python src/cli.py --algorithm cosar --file as_01.apx --no-write
```

COSAR with Bayesian aggregation:

```bash
python src/cli.py --algorithm cosar --file as_01.apx --aggregation-method bayesian
```

COSAR with WCT mode:

```bash
python src/cli.py --algorithm cosar --file as_01.apx --aggregation-method wct
```

CSS on a file:

```bash
python src/cli.py --algorithm css --file as_01.apx --semantics PR --measure U --agg sum
```

Display parsed input before run:

```bash
python src/cli.py --algorithm cosar --file as_01.apx --show-input
```

## Custom input mode

Custom input requires all three options together: `--args`, `--atts`, and `--votes`.

Example:

```bash
python src/cli.py \
  --algorithm cosar \
  --args '["a", "b", "c"]' \
  --atts '[["a", "b"], ["b", "c"]]' \
  --votes '{"A": {"a": 1, "b": -1}, "B": {"c": 1}}'
```

## APX input format

Input files use lines such as:

```text
agt(A, B).
arg(a).
arg(b).
att(a, b).
vot(A, a, 1).
vot(B, b, -1).
```

APX vote values accepted by the project format are `-1`, `1`.
The `agt(...)` line is mandatory and must list all voting agents in the file.
Neutral votes don't need to be included in the input files as they are equivalent to no vote. The parser will automatically handle missing votes and treat them as neutral, including agents that only have neutral votes.

## Outputs

- Before algorithm-specific processing, the CLI computes and prints initial extension(s) for the selected semantics.
- COSAR prints pruned framework information and best extension(s).
- COSAR writes `data/test/results/<source>_result.apx` unless `--no-write` is set.
- CSS prints best extension(s) and does not write an output `.apx` file.

## AF to OBAF Conversion

The AF files provided in `data/AF` come from the experimental dataset given to use in this project experimental phase. You can find all the details about their generation in `data/AF/Info_generation.txt`.

To generate OBAF files from all AF files in `data/AF`, run:

```bash
python src/af_to_obaf_script.py
```

The script processes both `data/AF/BA` and `data/AF/WS` and, for each AF file, tries all combinations of:

- semantics: `PR`, `CO`
- reliability: `0.2` to `1.0` (step `0.1`)
- number of agents: `5, 10, 15, 20, 25, 30`
- distribution type: `uniform`, `average`

This is `2 x 9 x 6 x 2 = 216` configurations per AF file, which can produce more than 18,000 generated `.apx` files for the current dataset. Once it's done, you'll be able to find a detailled log of the generation process in `logs/`, and the generated `.apx` files in `data/OBAF`.

## Acknowledgments

This implementation is grounded in the formal framework presented in `Collective Satisfaction Semantics for Opinion Based Argumentation.pdf`.
The software implementation also relies on the `pygarg` engine for argumentation reasoning, as described in `pygarg: A Python Engine for Argumentation.pdf`.

This repository is released as open-source research software; citation of these references is appreciated but not required.