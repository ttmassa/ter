# Definition of New Approaches

Here we define and formalize 3 new approaches to compute the strength of arguments in an OBAF.

## Neutral-aware score ($\tau_{\epsilon}^N$)

Let $O = <<Ar, att>, V_{Ar}>$ be an $OBAF$ and $x \in Ar$. $\tau_{\epsilon}^N$ is an opinion aggregation function that takes into account the neutral opinions in the OBAF. It is defined as follows:

Let $\tau_{\epsilon}$ be the base score function as defined in Definition 23. We define the neutral proportion for $x$ as:

$$
N(x) =
\begin{cases}
    0\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \text{if } |v^+(x)| + |v^-(x)| + |v^0(x)| = 0 \\
    \frac{|v^0(x)|}{|v^+(x)| + |v^-(x)| + |v^0(x)|}\ \text{otherwise}
\end{cases}
$$

Next, we define the Dividing-Power Index ($DPI$) to measure the polarization of non-neutral votes:

$$
DPI(x) =
\begin{cases}
    0\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \text{if } |v^+(x)| + |v^-(x)| = 0 \\
    \frac{||v^+(x)| - |v^-(x)||}{|v^+(x)| + |v^-(x)|} \text{otherwise}
\end{cases}
$$

The Neutral Influence Coefficient ($NIC$) then combines the neutral proportion with the DPI to quantify the influence of neutral opinions:

$$
NIC(x) = N(x) * DPI(x)
$$

Finally, the neutral-aware score is computed as:

$$\tau_{\epsilon}^N(x) = (1 - NIC(x)) * \tau_{\epsilon}(x) + NIC(x) * 0.5$$

Once we have obtained $\tau_{\epsilon}^N$ for all arguments in $Ar$, we can use it to prune the OBAF by removing all attacks from an argument $x$ on another argument $y$ if $\tau_{\epsilon}^N(x) < \tau_{\epsilon}^N(y)$.


## Weighted Conflict Tolerance Semantics

Let $\mathcal{O} = \langle \langle \mathcal{Ar}, att \rangle, \mathcal{V}_{\mathcal{Ar}} \rangle$ be an OBAF and $x \in \mathcal{Ar}$. 

For any argument $x$, let $P(x) = |v^+(x)|$, $C(x) = |v^-(x)|$, and $N(x) = |v^0(x)|$. The total number of votes is $Total(x) = P(x) + C(x) + N(x)$.

We define the **Neutral-Aware Force** $\tau^N(x)$ and the **Stability** $Stab(x)$ of an argument as follows:

$$
\tau^N(x) = 
\begin{cases}
    0 & \text{if } Total(x) = 0 \\
    \frac{P(x) + 0.5 N(x)}{Total(x)} & \text{otherwise}
\end{cases}
$$

$$
Stab(x) = 
\begin{cases}
    0 & \text{if } Total(x) = 0 \\
    \frac{N(x)}{Total(x)} & \text{otherwise}
\end{cases}
$$

### Attack Weight ($W$)
Every attack $(x, y) \in att$ produces a cost, or weight, defined as the difference between the attacker's force and the target's stability:

$$
W(x, y) = \max(0, \tau^N(x) - Stab(y))
$$

### Tolerance-Free Extensions
Let $E \subseteq \mathcal{Ar}$ be a set of arguments (an extension). The total cost of internal conflicts within $E$ is the sum of the weights of all attacks between arguments in $E$:

$$
Cost(E) = \sum_{(x, y) \in att \cap (E \times E)} W(x, y)
$$

Given a tolerance threshold $K \ge 0$, an extension $E$ is considered **$K$-Tolerance-Free** if:

$$
Cost(E) \le K
$$

This replaces the traditional conflict-free property, allowing arguments to be accepted together if their internal conflict cost does not exceed $K$.



## Bayesian score ($\tau_{\epsilon}^B$)

Let $O = <<Ar, att>, V_{Ar}>$ be an $OBAF$ and $x \in Ar$. $\tau_{\epsilon}^B$ is an opinion aggregation function that computes the strength of an argument using a Bayesian approach, treating neutral votes with a specific weight. It is defined as follows:

Let $neutral\_weight \in [0, 1]$ be the designated weight assigned to neutral opinions (e.g., $0.5$ for an exactly intermediate opinion).

$$
\tau_{\epsilon}^B(x) = \frac{|v^+(x)| + neutral\_weight \cdot |v^0(x)|}{|v^+(x)| + |v^-(x)| + |v^0(x)| + \epsilon}
$$

Once we have obtained $\tau_{\epsilon}^B$ for all arguments in $Ar$, we can use it to prune the OBAF by removing all attacks from an argument $x$ on another argument $y$ if $\tau_{\epsilon}^B(x) < \tau_{\epsilon}^B(y)$.

---

## Comparative Analysis (Preferred Semantics)

The following tables compare the four approaches on five argumentation scenarios from the `data/` directory. All results use: $\epsilon = 0.1$, $neutral\_weight = 0.5$, $K = 0.1$ (WCT), and Preferred (PR) semantics.

### Extensions Summary

| Dataset | Initial | Base COSAR | Neutral-Aware | Bayesian | WCT ($K=0.1$) |
|---------|---------|------------|---------------|----------|----------------|
| `as_01` | $\{a\}$ | $\{a\}$ | $\{a\}$ | $\{a\}$ | $\{a\}$ |
| `as_02` | $\emptyset$ | $\{b, c\}$ | $\{b, c\}$ | $\{b, c\}$ | $\{a, b, c\}$ |
| `as_03` | $\{a, d\}$ | $\{a, b, d\}$ | $\{a, b, d\}$ | $\{a, b, d\}$ | $\{a, b, c, d\}$ |
| `as_04` | $\{p, s\}$, $\{r, t\}$ | $\{p, r, t\}$ | $\{p, r, t\}$ | $\{p, r, t\}$ | $\{p, q, r, s, t\}$ |
| `as_05` | $\emptyset$ | $\{a, c\}$ | $\{a, b\}$ | $\{a, b\}$ | $\{a, c\}$ |

### Scores Comparison — `as_05` (3 arguments, high neutral proportion)

| Arg | Votes $(v^-, v^0, v^+)$ | Base | Neutral-Aware | Bayesian | WCT Force | WCT Stab |
|-----|-------------------------|------|---------------|----------|-----------|----------|
| a | $(0, 8, 2)$ | 0.952 | 0.590 | 0.594 | 0.600 | 0.800 |
| b | $(2, 2, 6)$ | 0.741 | 0.717 | 0.693 | 0.700 | 0.200 |
| c | $(6, 2, 2)$ | 0.247 | 0.272 | 0.297 | 0.300 | 0.200 |

**Key observation:** The Base method overestimates $a$ (0.952) by ignoring its 8 neutral votes. The Neutral-Aware and Bayesian methods reduce $a$'s dominance, which flips the pruning decision on the $a \to b$ attack, resulting in a different extension: $\{a, b\}$ instead of $\{a, c\}$.

### Scores Comparison — `as_03` (4 arguments, balanced votes)

| Arg | Votes $(v^-, v^0, v^+)$ | Base | Neutral-Aware | Bayesian | WCT Force | WCT Stab |
|-----|-------------------------|------|---------------|----------|-----------|----------|
| a | $(2, 9, 3)$ | 0.588 | 0.577 | 0.532 | 0.536 | 0.643 |
| b | $(2, 9, 3)$ | 0.588 | 0.577 | 0.532 | 0.536 | 0.643 |
| c | $(3, 9, 2)$ | 0.392 | 0.406 | 0.461 | 0.464 | 0.643 |
| d | $(2, 10, 2)$ | 0.488 | 0.488 | 0.496 | 0.500 | 0.714 |

### Scores Comparison — `as_02` (3 arguments, varied distributions)

| Arg | Votes $(v^-, v^0, v^+)$ | Base | Neutral-Aware | Bayesian | WCT Force | WCT Stab |
|-----|-------------------------|------|---------------|----------|-----------|----------|
| a | $(2, 5, 3)$ | 0.588 | 0.579 | 0.545 | 0.550 | 0.500 |
| b | $(2, 6, 2)$ | 0.488 | 0.488 | 0.495 | 0.500 | 0.600 |
| c | $(1, 6, 3)$ | 0.732 | 0.662 | 0.594 | 0.600 | 0.600 |

### Extreme Case — "Total Indecision" (`extreme_all_neutral.apx`)

No voters express any opinion (all votes are neutral or absent). This tests how each method handles complete lack of information.

| Arg | Votes $(v^-, v^0, v^+)$ | Base | NA | Bayesian | WCT Force | WCT Stab |
|-----|-------------------------|------|----|----------|-----------|----------|
| a | $(0, 0, 0)$ | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| b | $(0, 0, 0)$ | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| c | $(0, 0, 0)$ | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

| Approach | Extension |
|----------|-----------|
| Base COSAR | $\emptyset$ |
| Neutral-Aware | $\emptyset$ |
| Bayesian | $\emptyset$ |
| WCT ($K=0.1$) | $\{a, b, c\}$ ✅ |

**Analysis:** When nobody votes, all pruning-based methods (Base, NA, Bayesian) give scores of 0 and keep all attacks, resulting in no acceptable arguments. **WCT is the only method that produces an extension** — since all attack weights are 0 (no force), the total cost is 0, which satisfies the tolerance $K = 0.1$. This shows WCT's advantage in sparse-information scenarios.

---

### General Observations

1. **Base COSAR** tends to produce extreme scores because it ignores neutral votes entirely, leading to overconfident rankings.
2. **Neutral-Aware and Bayesian** consistently correct this bias by incorporating neutral votes, producing more realistic rankings. They agree on extensions in all tested cases.
3. **WCT** behaves differently from the other three: it is the only method that can produce extensions when no votes exist (total indecision), and it tends to accept larger coalitions by tolerating residual conflicts.
4. The choice of method depends on the application:
   - Use **Base** only when neutral votes are absent or irrelevant.
   - Use **NA/Bayesian** when neutral votes carry informational weight (e.g., "I don't know" is meaningful).
   - Use **WCT** when maximizing the number of accepted arguments is desirable, even at the cost of tolerating minor conflicts.
