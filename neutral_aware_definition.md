# Neutral-Aware Opinion Aggregation for COSAR

## Definition ($\tau_\epsilon^N$)

Let

- $O = <<Ar, att>, VAr>$ be an OBAF,
- $x$ in Ar,
- $\epsilon > 0$.

For argument $x$, we define:

- $p(x) = |v_{plus}(x)|$
- $m(x) = |v_{minus}(x)|$
- $z(x) = |v_{zero}(x)|$
- $n(x) = p(x) + m(x) + z(x)$

### Base score

We keep the original polarity-based score as a base signal:

$$
b_\epsilon(x)=
\begin{cases}
0 & \text{if } p(x)=m(x)=0 \\
\frac{p(x)}{p(x)+m(x)+\epsilon} & \text{otherwise}
\end{cases}
$$

### Dividing-power index (DPI)

We quantify how divisive the non-neutral opinions are by computing a new metric called the dividing-power index (DPI):

$$
\pi(x)=
\begin{cases}
0 & \text{if } p(x)+m(x)=0 \\
1-\frac{p(x)-m(x)}{p(x)+m(x)} & \text{otherwise}
\end{cases}
$$

Then, we classify arguments into three classes based on their DPI. We use two thresholds $\theta_1$ and $\theta_2$ to define the classes:
- Low dividing-power: $\pi(x) < \theta_1$
- Normal dividing-power: $\theta_1 \le \pi(x) < \theta_2$
- High dividing-power: $\pi(x) \ge \theta_2$

Typical thresholds used in this project:

- $\theta_1 = \frac{1}{3}$
- $\theta_2 = \frac{2}{3}$

### Neutral influence coefficient (NIC)

Let the neutral proportion be:

$$
\eta(x)=
\begin{cases}
0 & \text{if } n(x)=0 \\
\frac{z(x)}{n(x)} & \text{otherwise}
\end{cases}
$$

We assign a class-dependent weight $\omega$:

- $\omega(low)=1.0$
- $\omega(normal)=0.6$
- $\omega(high)=0.3$

Then define the neutral influence coefficient (NIC) as:

$$
\alpha(x) = \min(1, \omega(\pi(x))\cdot\eta(x))
$$

### Neutral-aware aggregation

The final neutral-aware opinion aggregation function is:

$$
\tau_\epsilon^N(x) = (1-\alpha(x))\ b_\epsilon(x) + \alpha(x)\cdot 0.5
$$

This formula is a convex combination of the original base score $b_\epsilon(x)$ and $0.5$ (indecision), where the weight $\alpha(x)$ depends on the proportion of neutral votes and the divisiveness of the argument.
Its goal is to moderate the original score based on the divisiveness of the argument so that arguments with many neutral votes are treated as less certain.

## Why this extension

Definition 23 ignores neutral votes in the final score. In real voting systems, this can hide uncertainty.

This extension keeps the original signal from positive/negative votes, but uses neutral votes as a confidence dampener:

- If neutral votes are rare, $\alpha(x)$ is small and the score stays close to $b_\epsilon(x)$.
- If neutral votes are dominant, the score moves toward 0.5 (indecision).
- The movement is stronger for low dividing-power arguments and weaker for highly divisive ones.

So arguments with 99% neutral votes are no longer treated the same as arguments with 3% neutral votes.

## Example in action (from current COSAR scenario)

The following example comes from the current scenario in `src/cosar.py`.

### Aggregated vote counts

- A: $m(A)=0,\ z(A)=14,\ p(A)=2$
- B: $m(B)=2,\ z(B)=8,\ p(B)=6$
- C: $m(C)=6,\ z(C)=8,\ p(C)=2$

### Program output

```text
(.venv) [tim@archpc ter]$ python src/cosar.py
Aggregate Votes: {'A': [0, 14, 2], 'B': [2, 8, 6], 'C': [6, 8, 2]}
Scores: {'A': 0.952, 'B': 0.741, 'C': 0.247}
Pruned Attacks: [['A', 'B'], ['B', 'C']]
Extensions: ['A', 'C']
Aggregate Votes: {'A': [0, 14, 2], 'B': [2, 8, 6], 'C': [6, 8, 2]}
Scores: {'A': 0.556, 'B': 0.669, 'C': 0.323}
Pruned Attacks (Neutral-Aware): [['B', 'C']]
Extensions (Neutral-Aware): ['A', 'B']
```

### Why the two methods differ here

With the base method, neutrals are fully ignored in the scoring denominator (only positive and negative votes are used, plus $\epsilon=0.1$), so A remains very high:

- $b_\epsilon(A)=\frac{2}{2+0+0.1}=0.952$
- $b_\epsilon(B)=\frac{6}{6+2+0.1}=0.741$
- $b_\epsilon(C)=\frac{2}{2+6+0.1}=0.247$

Hence the ranking is $A > B > C$, so attacks $A \to B$ and $B \to C$ are kept, while $C \to A$ is pruned.

With the neutral-aware method, A is pulled strongly toward 0.5 because neutral votes dominate A (14 out of 16), while B is pulled less:

- $\tau_\epsilon^N(A)=0.556$
- $\tau_\epsilon^N(B)=0.669$
- $\tau_\epsilon^N(C)=0.323$

Now the ranking becomes $B > A > C$. This flips the edge comparison on $A \to B$:

- Base: keep $A \to B$ because $A \ge B$
- Neutral-aware: prune $A \to B$ because $A < B$

That single structural change is enough to produce different extensions:

- Base: ['A', 'C']
- Neutral-aware: ['A', 'B']

This is precisely the intended behavior of $\tau_\epsilon^N$: arguments with many neutral votes are treated as less certain, so high polarity-only scores can be moderated when indecision is strong.
