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
NIC(x) = \min(1, N(x) * DPI(x))
$$

Finally, the neutral-aware score is computed as:

$$\tau_{\epsilon}^N(x) = (1 - NIC(x)) * \tau_{\epsilon}(x) + NIC(x) * 0.5$$

Once we have obtained $\tau_{\epsilon}^N$ for all arguments in $Ar$, we can use it to prune the OBAF by removing all attacks from an argument $x$ on another argument $y$ if $\tau_{\epsilon}^N(x) < \tau_{\epsilon}^N(y)$.

## Bayesian score ($\tau_{\epsilon}^B$)

Let $O = <<Ar, att>, V_{Ar}>$ be an $OBAF$ and $x \in Ar$. $\tau_{\epsilon}^B$ is an opinion aggregation function that computes the strength of an argument using a Bayesian approach, treating neutral votes with a specific weight. It is defined as follows:

Let $neutral\_weight \in [0, 1]$ be the designated weight assigned to neutral opinions (e.g., $0.5$ for an exactly intermediate opinion).

$$
\tau_{\epsilon}^B(x) = \frac{|v^+(x)| + neutral\_weight \cdot |v^0(x)|}{|v^+(x)| + |v^-(x)| + |v^0(x)| + \epsilon}
$$

Once we have obtained $\tau_{\epsilon}^B$ for all arguments in $Ar$, we can use it to prune the OBAF by removing all attacks from an argument $x$ on another argument $y$ if $\tau_{\epsilon}^B(x) < \tau_{\epsilon}^B(y)$.