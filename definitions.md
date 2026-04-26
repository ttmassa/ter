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

Next, we define the Dividing-Power Index ($DPI \in [0 ; 1]$) to measure the polarization of non-neutral votes. This index captures how much the decided voters (those who voted for or against) are in agreement or disgreement. The higher the $DPI$, the more polarized the decided votes are:

$$
DPI(x) =
\begin{cases}
    0\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \text{if } |v^+(x)| + |v^-(x)| = 0 \\
    \frac{||v^+(x)| - |v^-(x)||}{|v^+(x)| + |v^-(x)|} \text{otherwise}
\end{cases}
$$

The Neutral Influence Coefficient ($NIC$) then combines the neutral proportion with the DPI to quantify the influence of neutral opinions. The intuition is that neutral votes should have a stronger influence when there is a high proportion of neutral voters **and** when the decided voters are highly polarized (i.e., they mostly agree with each other). Conversely, if the decided voters are evenly split, the neutral votes should have less influence because they do not indicate a clear consensus. The $NIC$ is defined as:

$$
NIC(x) = N(x) * DPI(x)
$$

Finally, the neutral-aware score is computed as a weighted average between the base score $\tau_{\epsilon}(x)$ and a neutral baseline of $0.5$, where the weight is determined by the $NIC$. The formula is defined as:

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

Let $O = <<Ar, att>, V_{Ar}>$ be an $OBAF$ and $x \in Ar$. $\tau_{\epsilon}^B$ is an opinion aggregation function that computes the strength of an argument using a Bayesian approach, where neutral votes are treated as **half a vote in favor** of the argument.

### Interpretation of the neutral vote

In the context of opinion-based argumentation, a voter can express three types of opinions on an argument $x$:

- **In favor** ($v^+(x)$): the voter explicitly supports the argument. This contributes a weight of $1$ in favor.
- **Against** ($v^-(x)$): the voter explicitly opposes the argument. This contributes a weight of $0$ in favor (i.e., it only appears in the denominator).
- **Neutral** ($v^0(x)$): the voter **does not have a clear opinion** — they are undecided, lack sufficient information, or are indifferent. This is **not** a vote both for and against; rather, it reflects **uncertainty or abstention**. Since the voter neither supports nor opposes the argument, the neutral vote is treated as contributing **half the weight of a positive vote** (i.e., $0.5$). This reflects the idea that a neutral voter is **exactly midway between supporting and opposing** — they are not fully convinced, but they are not against either.

### Formula

The neutral vote weight is fixed at $0.5$. The Bayesian score is defined as:

$$
\tau_{\epsilon}^B(x) = \frac{|v^+(x)| + 0.5 \cdot |v^0(x)|}{|v^+(x)| + |v^-(x)| + |v^0(x)| + \epsilon}
$$

**Example:** Consider an argument $x$ with 2 votes in favor, 1 vote against, and 4 neutral votes ($\epsilon = 0.1$):

$$
\tau_{\epsilon}^B(x) = \frac{2 + 0.5 \times 4}{2 + 1 + 4 + 0.1} = \frac{4}{7.1} \approx 0.563
$$

The 4 neutral voters contribute as if 2 of them voted in favor, reflecting their intermediate position between support and opposition.

Once we have obtained $\tau_{\epsilon}^B$ for all arguments in $Ar$, we can use it to prune the OBAF by removing all attacks from an argument $x$ on another argument $y$ if $\tau_{\epsilon}^B(x) < \tau_{\epsilon}^B(y)$.

---

## Comparative Analysis (Preferred Semantics)

The following tables compare the four approaches on five argumentation scenarios from the `data/test/` directory. All results use: $\epsilon = 0.1$, $neutral\_weight = 0.5$, $K = 0.1$ (WCT), and Preferred (PR) semantics.

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

### Differentiating Examples — Where All 3 Pruning-Based Approaches Disagree

The following examples use a simple 3-argument cycle: $a \to b$, $b \to c$, $c \to a$ with Preferred (PR) semantics and $\epsilon = 0.1$. They demonstrate cases where **Base, Neutral-Aware, and Bayesian each produce a different extension**, proving that the three methods are truly distinct.

#### Example 1

| Arg | $v^-$ | $v^0$ | $v^+$ | Total |
|-----|:-----:|:-----:|:-----:|:-----:|
| a   | 0     | 1     | 1     | 2     |
| b   | 0     | 3     | 2     | 5     |
| c   | 1     | 1     | 3     | 5     |

| Arg | Base  | Neutral-Aware | Bayesian |
|-----|-------|---------------|----------|
| a   | 0.909 | 0.705         | 0.714    |
| b   | 0.952 | 0.681         | 0.686    |
| c   | 0.732 | 0.709         | 0.686    |

| Approach | Extension | Explanation |
|----------|-----------|-------------|
| **Base** | $\{a, b\}$ | $b$ dominates (0.952) because its 3 neutral votes are invisible. Attack $a \to b$ is removed ($a < b$), so $a$ and $b$ coexist. |
| **Neutral-Aware** | $\{b, c\}$ | $b$ drops to 0.681 (neutral proportion penalizes it). $c$ becomes the strongest (0.709). Attack $b \to c$ is removed ($b < c$), so $b$ and $c$ coexist. |
| **Bayesian** | $\{a, c\}$ | $a$ leads (0.714). $b$ and $c$ are tied (0.686). Attack $c \to a$ is removed ($c < a$), so $a$ and $c$ coexist. |

**Why the three methods disagree here:**
- **Base** overestimates $b$ by ignoring its 3 neutral votes entirely ($2/2.1 \approx 0.952$).
- **Neutral-Aware** strongly corrects $b$ because the high neutral proportion ($3/5 = 60\%$) combined with a clear majority among decided votes ($DPI = 1$) creates a strong pull toward 0.5.
- **Bayesian** treats neutral votes more moderately: it adds $0.5 \times v^0$ to the numerator, which gives $b$ a score of $(2 + 1.5) / 5.1 = 0.686$. For $a$, the single neutral vote gives $(1 + 0.5) / 2.1 = 0.714$, making $a$ the strongest.

#### Example 2 — Bayesian ≠ WCT

This example shows how the Bayesian pruning approach and WCT can disagree. Same 3-argument cycle: $a \to b$, $b \to c$, $c \to a$.

| Arg | $v^-$ | $v^0$ | $v^+$ | Total |
|-----|:-----:|:-----:|:-----:|:-----:|
| a   | 0     | 1     | 1     | 2     |
| b   | 0     | 1     | 1     | 2     |
| c   | 0     | 1     | 3     | 4     |

**Bayesian scores** (pruning-based):

| Arg | Bayesian Score |
|-----|---------------|
| a   | 0.714          |
| b   | 0.714          |
| c   | 0.854          |

Bayesian ranking: $c > a = b$. Attack $a \to b$ is kept ($a \geq b$), attack $b \to c$ is removed ($b < c$), attack $c \to a$ is kept ($c > a$). Pruned framework: $a \to b$, $c \to a$ → Extension: $\{b, c\}$.

**WCT scores** (tolerance-based):

| Arg | Force ($\tau^N$) | Stability | 
|-----|:-----:|:---------:|
| a   | 0.750 | 0.500     |
| b   | 0.750 | 0.500     |
| c   | 0.875 | 0.250     |

Attack weights: $W(a \to b) = 0.250$, $W(b \to c) = 0.500$, $W(c \to a) = 0.375$. With $K = 0.250$ (endogenous natural-break), WCT tolerates the internal attack $a \to b$ within $\{a, b\}$ because its cost (0.250) ≤ $K$ → Extension: $\{a, b\}$.

| Approach | Extension | Reason |
|----------|-----------|--------|
| **Bayesian** | $\{b, c\}$ | $b \to c$ is pruned because $b < c$, so $b$ and $c$ can coexist. |
| **WCT** | $\{a, b\}$ | The $a \to b$ conflict has low cost (0.250 ≤ $K$), so it is tolerated. |

**Key difference:** Bayesian removes weak attacks entirely (pruning), while WCT keeps all attacks but tolerates low-cost conflicts. Here, WCT accepts $\{a, b\}$ despite the $a \to b$ attack because its cost is within the tolerance threshold.

#### Example 3 — Neutral-Aware ≠ WCT

| Arg | $v^-$ | $v^0$ | $v^+$ | Total |
|-----|:-----:|:-----:|:-----:|:-----:|
| a   | 0     | 1     | 1     | 2     |
| b   | 0     | 1     | 1     | 2     |
| c   | 0     | 1     | 2     | 3     |

**Neutral-Aware scores** (pruning-based):

| Arg | NA Score |
|-----|----------|
| a   | 0.705    |
| b   | 0.705    |
| c   | 0.801    |

NA ranking: $c > a = b$. Attack $b \to c$ is removed ($b < c$). Pruned framework: $a \to b$, $c \to a$ → Extension: $\{b, c\}$.

**WCT scores** (tolerance-based):

| Arg | Force ($\tau^N$) | Stability |
|-----|:-----:|:---------:|
| a   | 0.750 | 0.500     |
| b   | 0.750 | 0.500     |
| c   | 0.833 | 0.333     |

Attack weights: $W(a \to b) = 0.250$, $W(b \to c) = 0.417$, $W(c \to a) = 0.333$. With $K = 0.333$ (endogenous median-fallback), WCT tolerates the $a \to b$ conflict (cost 0.250 ≤ $K$) → Extension: $\{a, b\}$.

| Approach | Extension | Reason |
|----------|-----------|--------|
| **Neutral-Aware** | $\{b, c\}$ | $b \to c$ is pruned because $b < c$, freeing $b$ and $c$ to coexist. |
| **WCT** | $\{a, b\}$ | The $a \to b$ conflict is tolerated (cost ≤ $K$), allowing both to be accepted. |

**Key difference:** The Neutral-Aware method and WCT use fundamentally different mechanisms. NA adjusts scores and then prunes attacks, which here removes $b \to c$. WCT instead computes a tolerance threshold and allows arguments to coexist even if they attack each other, as long as the total cost stays low.

---

### General Observations

#### How each approach handles neutral votes

| Approach | Neutral votes | Mechanism |
|----------|---------------|-----------|
| **Base** | Completely ignored | Only $v^+$ and $v^-$ are used. Neutral voters are invisible. |
| **Neutral-Aware** | Influence depends on context | The more neutral voters there are **and** the more unanimous the decided voters are, the stronger the pull toward 0.5 (via the NIC coefficient). |
| **Bayesian** | Fixed weight of 0.5 each | Each neutral vote always counts as half a positive vote in the numerator, regardless of context. |
| **WCT** | Fixed weight of 0.5 each + stability | Neutral votes contribute to both the force (like Bayesian) **and** the stability of an argument. High stability makes an argument harder to attack. |

#### When to use each approach

1. **Base COSAR** — Use when **all voters have a clear opinion** (no neutral votes), or when neutral votes should be deliberately excluded. It produces the most extreme scores and is the simplest method. However, it can be misleading when many voters are neutral, because it treats an argument with 2 votes in favor out of 2 decided voters the same as one with 2 in favor out of 100 voters (98 neutral).

2. **Neutral-Aware** — Use when **the proportion of neutral votes matters more than their absolute count**. This method is best suited for scenarios where a high consensus among few decided voters should be tempered by a large undecided majority. For example, if 2 out of 10 voters support an argument and 8 are neutral, the NA method will strongly reduce the score because the apparent consensus is based on very few decided voters. The correction is context-sensitive: it depends on both the neutral proportion and the polarization of decided votes (DPI).

3. **Bayesian** — Use when **each neutral vote should have a uniform, predictable impact** regardless of the voting context. Every neutral vote always contributes exactly 0.5 to the numerator. This is simpler and more transparent than NA: you can easily predict how adding or removing a neutral voter will change the score. It is well-suited when a neutral voter represents someone who is **undecided but not uninformed** — their uncertainty deserves a fixed, moderate contribution.

4. **WCT (Weighted Conflict Tolerance)** — Use when **you want to maximize the number of accepted arguments**, even if some of them attack each other. Unlike the three pruning-based methods (which remove attacks and then compute extensions on the simplified graph), WCT keeps all attacks but assigns them a cost and allows arguments to coexist as long as the total cost of their internal conflicts stays below a tolerance threshold $K$. This makes WCT the only method that can produce extensions when **no votes exist at all** (total indecision), and it tends to produce **larger extensions** than the other methods.

#### Summary table

| Scenario | Recommended approach |
|----------|---------------------|
| No neutral votes | **Base** (simplest, no bias) |
| Many neutral voters, few decided voters | **Neutral-Aware** (context-sensitive correction) |
| Neutral voters should each count equally | **Bayesian** (fixed 0.5 weight, predictable) |
| Maximize accepted arguments, tolerate conflicts | **WCT** (tolerance-based, no pruning) |
| No information at all (nobody votes) | **WCT** (only method that produces extensions) |
| Need strict conflict-free extensions | **Base / NA / Bayesian** (pruning guarantees no internal attacks) |
