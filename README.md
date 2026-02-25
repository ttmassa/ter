# TER - COSAR/CSS CLI

Unified command-line tool to run two approaches on argumentation frameworks:

- `cosar`: prune attacks using vote-based argument scores.
- `css`: rank extensions using Collective Satisfaction Semantics.

The main entry point is `src/cli.py`.

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`

## Setup

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to use

We provide three ways to run the tool:

### 1) Interactive mode

Run:

```bash
python src/cli.py
```

Steps:

1. Choose algorithm (`cosar` or `css`)
2. File list + commands menu
3. Pick file number to run

In the file menu, you can select one of the following commands:

- `<number>`: run this file
- `v<number>`: view parsed content of this file
- `a`: switch algorithm (without quitting)
- `p`: configure CSS params (only when algorithm is `css`)
- `q`: quit

When `css` is selected, you can configure:

- `semantics` (e.g. `PR`, `ST`, `CO`)
- `measure` in `{S, D, U}`
- `agg` in `{sum, min, leximax, leximin}`

### 2) Run with explicit options

#### COSAR

```bash
python src/cli.py --algorithm cosar --file as_01.apx
```

Without `--no-write`, COSAR writes:

- `data/results/<source>_result.apx`

To disable output file creation, you can use `--no-write`:

```bash
python src/cli.py --algorithm cosar --file as_01.apx --no-write
```

#### CSS

```bash
python src/cli.py --algorithm css --file as_01.apx --semantics PR --measure U --agg sum
```

Notes:

- CSS prints best extension(s).
- CSS does not generate an output `.apx` file.

### 3) Custom input mode (no file)

Provide all three together: `--args`, `--atts`, `--votes`.

Example:

```bash
python src/cli.py \
	--algorithm cosar \
	--args '["a", "b", "c"]' \
	--atts '[["a", "b"], ["b", "c"]]' \
	--votes '{("A", "a"): 1, ("A", "b"): -1, ("B", "c"): 1}'
```

## APX format expected by this project

Input files are plain text with lines like:

```text
arg(a).
arg(b).
att(a, b).
vot(A, a, 1).
vot(B, b, -1).
```

Accepted vote values: `-1`, `0`, `1`.

## Data folders

- Inputs: `data/*.apx`
- COSAR outputs: `data/results/*.apx`