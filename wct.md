# Weighted Conflict Tolerance (WCT) 


---

## Definition ($WCT$)

Let
- $O = \langle\langle Ar, att\rangle, V_{Ar}\rangle$ be an OBAF,
- $E \subseteq Ar$ be a proposed extension (a subset of arguments),
- $K \ge 0$ be the conflict tolerance threshold.

For argument $x$, we define the vote counts as:
- $p(x) = |v^+(x)|$ — the number of agents who support $x$
- $m(x) = |v^-(x)|$ — the number of agents who oppose $x$
- $z(x) = |v^0(x)|$ — the number of agents who are neutral on $x$
- $n(x) = p(x) + m(x) + z(x)$ — the total number of agents who participated

---

## Neutral-Aware Force ($\tau^N$)

### Intuition

The force of an argument represents how much offensive power it carries. An argument with many supporters is "strong" — it can credibly attack other arguments. An argument with few supporters is "weak" — its attacks carry little weight.

But what about neutral votes? A neutral vote is not support, but it is not opposition either. In WCT, we treat each neutral vote as contributing **half a unit of support**. The reasoning is as follows: a neutral agent does not actively oppose the argument, so the argument retains some passive backing from that agent. If 10 people vote on argument $A$ and 8 are neutral while 2 support it, then $A$ has active support from 2 people and passive non-opposition from 8. Its force should reflect that it is not strongly supported, but also not actively rejected.

### Formal Definition

$$
\tau^N(x) = 
\begin{cases}
    0 & \text{if } n(x) = 0 \\
    \frac{p(x) + 0.5 \cdot z(x)}{n(x)} & \text{otherwise}
\end{cases}
$$

### Interpretation

The force $\tau^N(x)$ always falls in $[0, 1]$.

- If every agent supports $x$: $\tau^N(x) = 1$. Maximum offensive power.
- If every agent opposes $x$: $\tau^N(x) = 0$. No offensive power at all.
- If every agent is neutral: $\tau^N(x) = 0.5$. The argument has a middling force — it is neither strong nor weak, reflecting the collective indecision.
- If support and opposition are equal with no neutrals: $\tau^N(x) = 0.5$. Same middling force, but for a different reason (polarization rather than indecision).

The key observation is that **neutral votes pull the force toward 0.5**. An argument that would be very strong based on its active supporters alone (e.g., 2 for, 0 against) becomes moderate if many agents are neutral (e.g., 2 for, 0 against, 8 neutral gives $\tau^N = 0.4/1.0 = 0.60$, not $1.0$).

---

## inertia neutrality ($IN$)

### Intuition

inertia neutrality measures how resistant an argument is to being disturbed by attacks. The idea comes from a physical analogy: an object with high inertia is hard to move. In the context of argumentation, an argument about which most people have no opinion is "inert" — there is no strong collective will to either accept or reject it. Attacking such an argument is like pushing against a wall of indifference: the attack does not have much effect because the population does not care enough about the target for the attack to matter.

Conversely, an argument about which everyone has a strong opinion (whether for or against) has low inertia neutrality. The population is already engaged with this argument, so an attack on it has a real audience and a real impact.

### Formal Definition

$$
IN(x) = 
\begin{cases}
    0 & \text{if } n(x) = 0 \\
    \frac{z(x)}{n(x)} & \text{otherwise}
\end{cases}
$$

### Interpretation

- $IN(x) = 1$: every agent is neutral. The argument is maximally stable — it exists in a state of total indifference. Any attack on it is absorbed.
- $IN(x) = 0$: no agent is neutral. Every agent has taken a side. The argument is maximally exposed — attacks on it carry full weight.
- $IN(x) = 0.7$: 70% of agents are neutral. The argument is mostly stable, but 30% of the population is engaged, so attacks still have some (reduced) effect.

The stability captures the following real-world phenomenon: **in a debate, attacking a topic that nobody cares about is a waste of energy. Attacking a topic that everyone has an opinion on is where the real conflict happens.**

---

## Attack Cost ($W$)

### Intuition

Not all attacks are equal. The destructive power of an attack from argument $A$ to argument $B$ depends on two things:

1. **How strong is the attacker?** An attack from a widely supported argument carries more weight than an attack from an argument that almost nobody supports. This is captured by $\tau^N(A)$.

2. **How resistant is the target?** An attack on a highly stable argument (one with many neutral votes) is partially absorbed. The indifference of the population acts as a buffer. This is captured by $IN(B)$.

The cost of an attack is therefore the difference between the attacker's force and the target's stability. If the target's stability exceeds the attacker's force, the attack is completely absorbed — its cost is zero. The target's wall of indifference is thicker than the attacker's offensive power.

### Formal Definition

$$
W(x, y) = |\tau^N(x) - IN(y)|
$$

### Interpretation

- $W = 0$ (absorbed attack): the target is so stable (so many neutral votes) that the attacker cannot overcome the indifference barrier. This attack exists in the graph but has no practical impact. Example: a strongly supported argument attacks an argument about which 90% of people are neutral. The attack is structurally present but socially irrelevant.

- $W > 0$ (active attack): the attacker's force exceeds the target's stability. There is a real, quantifiable conflict. The higher the value, the more destructive the attack. Example: a popular argument ($\tau^N = 0.8$) attacks a polarized argument ($IN = 0.1$). The cost is $0.7$ — a heavy conflict.

- Typical range: since both $\tau^N$ and $IN$ are in $[0, 1]$, the cost $W$ is also in $[0, 1]$.

### Why this formula and not another?

The subtraction $\tau^N(x) - IN(y)$ captures the asymmetry of argumentation: the attacker projects force, the target absorbs it through indifference. We use $\max(0, \cdot)$ because negative values would imply the target is "healing" from the attack, which has no meaningful interpretation. An attack either does damage or it does not.

---

## Total Extension Cost

### Intuition

When we consider a set of arguments $E$ as a potential extension, some of those arguments may attack each other. Each such internal attack contributes a cost (as defined above). The total cost of the extension is the sum of all these internal conflict costs.

An extension with no internal attacks has cost 0. An extension with one mild internal conflict has a small cost. An extension with many severe internal conflicts has a high cost.

### Formal Definition

$$
Cost(E) = \sum_{(x,y) \in att \cap (E \times E)} W(x, y)
$$

---

## $K$-Tolerance-Free Extensions

### Intuition

The tolerance threshold $K$ is the maximum amount of total internal conflict that we are willing to accept in an extension. It represents a policy decision: "how much disagreement is acceptable in the collective solution?".

When $K = 0$, WCT is equivalent to classical conflict-freeness: no internal conflict is tolerated. The extension must be perfectly harmonious.

When $K > 0$, we accept that some internal friction may exist, provided it is mild enough. The larger $K$, the more disagreement we are willing to absorb. This is useful in scenarios where strict conflict-freeness produces empty or very small extensions — common when the argumentation graph has many cycles and the population is largely neutral.

### Formal Definition

An extension $E$ is **$K$-Tolerance-Free** if and only if:

$$
Cost(E) \le K
$$

### Interpretation

This replaces the traditional conflict-free property. Instead of asking "are there any conflicts?" (binary), we ask "how much total conflict is there, and is it below our tolerance?" (quantitative).

The result is that WCT can produce larger extensions than classical semantics, because it accepts arguments that mildly conflict with each other when the population is largely indifferent about the conflict.

---

## Interpretation of Neutral Votes

Neutral votes play a double role in WCT, and it is important to understand both:

**Role 1 — Force reduction.** A neutral vote on argument $x$ contributes $0.5$ (instead of $1.0$ for a positive vote or $0.0$ for a negative vote) to the force $\tau^N(x)$. This means that an argument with many neutral voters has a moderate force — it cannot dominate attacks the way a unanimously supported argument can. The neutral votes dilute the argument's offensive capability.

**Role 2 — Stability increase.** A neutral vote on argument $x$ directly increases its stability $IN(x)$. This makes the argument harder to attack. The more people are indifferent about $x$, the less effective any attack against $x$ becomes.

These two roles create a specific dynamic: **an argument with many neutral votes is both a weaker attacker and a harder target**. It exists in a state of protected mediocrity. This is a realistic model of arguments in public debates where most people have no opinion: such arguments are neither influential nor vulnerable.

---

## Motivating Examples (Paper Presentation)

The following examples use the same graph structure but vary only the number of neutral votes to demonstrate how WCT behaves differently from classical (conflict-free) semantics.

### Setup

Consider three arguments $A$, $B$, $C$ with attacks $A \to B$ and $B \to C$. There are 10 agents voting on each argument.

### Example 1 — No neutral votes (polarized debate)

| Argument | $v^+$ | $v^0$ | $v^-$ | $\tau^N$ | $IN$ |
|----------|--------|--------|--------|----------|--------|
| A | 7 | 0 | 3 | 0.70 | 0.00 |
| B | 5 | 0 | 5 | 0.50 | 0.00 |
| C | 3 | 0 | 7 | 0.30 | 0.00 |

Attack costs:
- $W(A \to B) = \max(0, 0.70 - 0.00) = 0.70$
- $W(B \to C) = \max(0, 0.50 - 0.00) = 0.50$

The extension $E = \{A, B, C\}$ has cost $Cost(E) = 0.70 + 0.50 = 1.20$.

With any reasonable $K$ (e.g., $K < 1.0$), this extension is rejected. In a polarized debate, conflicts are heavy and WCT correctly refuses to accept conflicting arguments together. The classical preferred extension $\{A, C\}$ remains the only viable option.

### Example 2 — Moderate neutrality (mixed debate)

Same graph, but now half the voters on $B$ are neutral:

| Argument | $v^+$ | $v^0$ | $v^-$ | $\tau^N$ | $IN$ |
|----------|--------|--------|--------|----------|--------|
| A | 7 | 0 | 3 | 0.70 | 0.00 |
| B | 3 | 5 | 2 | 0.55 | 0.50 |
| C | 3 | 0 | 7 | 0.30 | 0.00 |

Attack costs:
- $W(A \to B) = \max(0, 0.70 - 0.50) = 0.20$
- $W(B \to C) = \max(0, 0.55 - 0.00) = 0.55$

$Cost(\{A, B, C\}) = 0.20 + 0.55 = 0.75$.

The cost has dropped from 1.20 to 0.75. The attack $A \to B$ is now much weaker because $B$ has high stability (50% neutral). With $K = 0.8$, the full extension $\{A, B, C\}$ becomes acceptable — something impossible under classical semantics.

### Example 3 — High neutrality (apathetic debate)

Now most voters on both $B$ and $C$ are neutral:

| Argument | $v^+$ | $v^0$ | $v^-$ | $\tau^N$ | $IN$ |
|----------|--------|--------|--------|----------|--------|
| A | 7 | 0 | 3 | 0.70 | 0.00 |
| B | 1 | 8 | 1 | 0.50 | 0.80 |
| C | 1 | 8 | 1 | 0.50 | 0.80 |

Attack costs:
- $W(A \to B) = \max(0, 0.70 - 0.80) = 0.00$ (absorbed)
- $W(B \to C) = \max(0, 0.50 - 0.80) = 0.00$ (absorbed)

$Cost(\{A, B, C\}) = 0.00$.

Both attacks are completely absorbed. The extension $\{A, B, C\}$ is conflict-free even under $K = 0$. When almost nobody cares about $B$ and $C$, the conflicts become socially irrelevant and WCT reflects this by nullifying the attack costs.

### Summary of the three examples

| Scenario | Neutral proportion | $Cost(\{A,B,C\})$ | Accepted at $K=0.8$? |
|----------|-------------------|--------------------|-----------------------|
| Polarized (0% neutral on B,C) | 0% | 1.20 | No |
| Mixed (50% neutral on B) | 25% | 0.75 | Yes |
| Apathetic (80% neutral on B,C) | 60% | 0.00 | Yes (even at $K=0$) |

This demonstrates the central property of WCT: **as the proportion of neutral votes increases, the cost of internal conflicts decreases, and larger extensions become acceptable**. The semantics adapts to the "temperature" of the debate.

---


## Endogenous Determination of $K$ (Natural Break Method)

A key limitation of WCT as defined above is that $K$ is a free parameter set by the user. This introduces a subjective bias: a low $K$ favours strict conflict rejection, a high $K$ artificially inflates tolerance. To guarantee objectivity, $K$ must be derived entirely from the structure of the debate itself.

### Intuition

The set of active attack weights in any OBAF is rarely uniform. There typically exists a *natural gap* separating low-cost attacks (tolerable friction between compatible arguments) from high-cost attacks (genuine contradictions). $K$ is placed at this gap: all conflicts below it are absorbed into extensions; all conflicts above it remain prohibitive.

### Formal Definition

Let $W_{act} = \{W(x,y) \mid (x,y) \in att,\; W(x,y) > 0\}$ be the multiset of strictly positive attack weights. Let $m = |W_{act}|$.

**Case 0 — No active attacks.** If $m = 0$, every attack has been absorbed by stability. All extensions are conflict-free and we set:

$$K = 0$$

**Case 1 — Single active attack.** If $m = 1$, let $w_1$ be the unique active weight. No distribution structure exists to analyse. We set:

$$K = w_1$$

This accepts the sole active conflict as tolerable, which is the maximally permissive choice consistent with having only one data point.

**Case 2 — Multiple active attacks ($m \ge 2$).** Sort the active weights in non-decreasing order:

$$w_1 \le w_2 \le \ldots \le w_m$$

Compute the gap sequence:

$$\Delta_i = w_{i+1} - w_i, \quad i \in \{1, \ldots, m-1\}$$

Let $\Delta_{max} = \max_i \Delta_i$.

We now determine whether the largest gap is *salient* — that is, whether it genuinely separates two clusters of weights rather than being a random fluctuation in a near-uniform distribution.

Compute the mean of all gaps excluding the maximum:

$$\bar{\Delta}_{-max} = \frac{1}{m - 2} \sum_{\substack{j=1 \\ \Delta_j \neq \Delta_{max}}}^{m-1} \Delta_j$$

*(If $m = 2$, there is only one gap, so the saliency test is skipped and that gap is used directly.)*

**Saliency condition.** The maximum gap is salient if and only if:

$$\Delta_{max} \ge 2 \cdot \bar{\Delta}_{-max}$$

This condition requires the largest gap to be at least twice the average of all other gaps — i.e., it is not merely the largest by a negligible margin but a structural discontinuity.

**Case 2a — Salient gap exists.** Let $i^*$ be the index of the first occurrence of $\Delta_{max}$ (conservative tie-breaking: if multiple gaps share the maximum value, choose the leftmost one):

$$i^* = \min\{i \mid \Delta_i = \Delta_{max}\}$$

Then:

$$K = w_{i^*}$$

$K$ is set to the weight immediately *below* the gap. All attacks at or below this value are tolerable; all attacks above the gap are structural contradictions.

**Case 2b — No salient gap (fallback).** If $\Delta_{max} < 2 \cdot \bar{\Delta}_{-max}$, the distribution of weights has no clear discontinuity. We fall back to the median:

$$K = \text{med}(W_{act}) = \begin{cases} w_{\frac{m+1}{2}} & \text{if } m \text{ is odd} \\ \frac{w_{\frac{m}{2}} + w_{\frac{m}{2}+1}}{2} & \text{if } m \text{ is even} \end{cases}$$

### Summary

$$
K = \begin{cases}
0 & \text{if } m = 0 \\
w_1 & \text{if } m = 1 \\
w_{i^*} & \text{if } m \ge 2 \text{ and } \Delta_{max} \ge 2\bar{\Delta}_{-max} \\
\text{med}(W_{act}) & \text{if } m \ge 2 \text{ and } \Delta_{max} < 2\bar{\Delta}_{-max}
\end{cases}
$$

### Properties

1. **Fully endogenous.** $K$ depends only on the attack weights, which themselves depend only on votes and the argumentation graph. No external parameter is introduced.
2. **Conservative tie-breaking.** When multiple gaps of equal maximum size exist, the first (leftmost) is chosen, yielding the lowest possible $K$. This minimises the quantity of tolerated conflict in ambiguous situations.
3. **Graceful degradation.** When the weight distribution carries no structural signal (near-uniform), the method does not force a spurious cut but defaults to the median — a robust central tendency measure immune to outliers.
4. **Scale-invariant.** The saliency test uses a ratio ($2\times$), not an absolute threshold. It functions identically whether weights range in $[0, 0.1]$ or $[0, 10]$.
