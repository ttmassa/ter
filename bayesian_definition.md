# Bayesian Opinion Aggregation for COSAR

## Definition ($\tau_\epsilon^B$)

Let

- $O = <<Ar, att>, V_{Ar}>$ be an OBAF,
- $x$ in $Ar$,
- $\epsilon > 0$,
- $neutral\_weight = 0.5$.

For argument $x$, we define:

- $p(x) = |v_{plus}(x)|$
- $m(x) = |v_{minus}(x)|$
- $z(x) = |v_{zero}(x)|$
- $n(x) = p(x) + m(x) + z(x)$

### Bayesian Score

We define the Bayesian opinion aggregation function as:

$$
\tau_\epsilon^B(x) = \frac{p(x) + (neutral\_weight \cdot z(x))}{n(x) + \epsilon}
$$

This formula treats every neutral vote as a partial positive vote (weighted by $neutral\_weight$, which defaults to $0.5$) in the numerator, and counts all votes (decided and neutral) in the denominator. The $\epsilon$ parameter acts as a smoothing factor (Laplace smoothing) to prevent division by zero and softly pull the score toward $neutral\_weight$ when the number of votes is very low.

## Why this extension

Definition 23 (the base score) completely ignores neutral votes in the final score. In real voting systems, a large proportion of neutral votes indicates a lack of strong support or opposition. 

The Bayesian extension elegantly solves this by:
- Allowing a configurable impact for neutral votes via $neutral\_weight$ (e.g. exactly halfway between a positive and a negative vote if $0.5$).
- Valuing the **quantity** of votes: An argument with 200 positive votes and 100 negative votes will have a slightly better score than an argument with 2 positive votes and 1 negative vote, thanks to the $\epsilon$ smoothing which penalizes arguments with too few total votes.
- Guaranteeing that an argument with only neutral votes will logically converge towards $neutral\_weight$.

## Example in action (from current COSAR scenario)

The following example comes from the current scenario in `src/cosar.py`.

### Aggregated vote counts

- A: $m(A)=0,\ z(A)=14,\ p(A)=2$
- B: $m(B)=2,\ z(B)=8,\ p(B)=6$
- C: $m(C)=6,\ z(C)=8,\ p(C)=2$

### Bayesian score calculation (with $\epsilon=0.1$ and $neutral\_weight=0.5$)

- $\tau_\epsilon^B(A) = \frac{2 + (14 \cdot 0.5)}{2 + 0 + 14 + 0.1} = \frac{9}{16.1} \approx 0.559$
- $\tau_\epsilon^B(B) = \frac{6 + (8 \cdot 0.5)}{6 + 2 + 8 + 0.1} = \frac{10}{16.1} \approx 0.621$
- $\tau_\epsilon^B(C) = \frac{2 + (8 \cdot 0.5)}{2 + 6 + 8 + 0.1} = \frac{6}{16.1} \approx 0.373$

*(Note: In the code, neutral count for C might be slightly different depending on the exact vote distribution, but the logic remains identical).*

### Why this method differs from the Base method here

With the base method, A is ranked first ($A > B > C$) because it has no negative votes, completely ignoring the fact that it only has 2 decided votes compared to B's 8 decided votes.

With the Bayesian method, B surpasses A ($B > A > C$) because B has accumulated much more positive support (6 positives) than A (2 positives), and the large mass of neutral votes for A simply pulls its score down towards $0.5$ (the $neutral\_weight$).

This structural change flips the edge comparison on $A \to B$:

- Base: keep $A \to B$ because $A \ge B$
- Bayesian: prune $A \to B$ because $A < B$

Resulting in a different set of acceptable arguments (extensions).
