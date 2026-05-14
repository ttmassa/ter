import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.ticker as mticker

def plot_graph(metadata_file_path: str = "data/OBAF/obaf_metadata.csv", semantics: str = "all", number_of_agents: list[int] = [5, 10, 15, 20, 25, 30], distribution_type: str = "all"):
    """
        Use the .csv metadata file to plot the results of the experiments.
    """
    if semantics not in ["all", "PR", "CO"]:
        raise ValueError(f"Invalid semantics: {semantics}. Expected 'all', 'PR' or 'CO'.")
    if number_of_agents not in [[5], [5, 10], [5, 10, 15], [5, 10, 15, 20], [5, 10, 15, 20, 25], [5, 10, 15, 20, 25, 30]]:
        raise ValueError(f"Invalid number of agents: {number_of_agents}. Expected one of [5], [5, 10], [5, 10, 15], [5, 10, 15, 20], [5, 10, 15, 20, 25], or [5, 10, 15, 20, 25, 30].")
    if distribution_type not in ["all", "uniform", "average"]:
        raise ValueError(f"Invalid distribution type: {distribution_type}. Expected 'all', 'uniform' or 'average'.")
    
    # Read the metadata file
    df = pd.read_csv(metadata_file_path)

    # Filter the dataframe based on the input parameters
    if semantics != "all":
        df = df[df["semantics"] == semantics]
    if number_of_agents != [5, 10, 15, 20, 25, 30]:
        df = df[df["number_of_agents"].isin(number_of_agents)]
    if distribution_type != "all":
        df = df[df["distribution_type"] == distribution_type]
    
    score_columns = [
        "cosar_base_score",
        "cosar_na_score",
        "cosar_bayesian_score",
        "wct_score",
        "css_score",
    ]

    # Plot the efficiency for each algorithm based on the reliability of the agents
    # The efficiency is the sum of obafs with a score of 1 divided by the total number of obafs for each reliability value
    markers = ["o", "s", "^", "D", "v"]
    linestyles = ["-", "--", "-.", ":", "-"]
    n = len(score_columns)
    for i, score_column in enumerate(score_columns):
        efficiency = df.groupby("reliability")[score_column].apply(lambda x: (x == 1).sum() / len(x))
        # Convert index and values to numpy arrays
        x = efficiency.index.astype(float).to_numpy()
        y = efficiency.to_numpy(dtype=float)

        # Apply a small horizontal jitter per series so overlapping markers/lines are visible
        jitter = (i - (n - 1) / 2) * 0.002
        x_j = x + jitter

        plt.plot(
            x_j,
            y,
            label=score_column,
            linestyle=linestyles[i % len(linestyles)],
            linewidth=2,
            marker=markers[i % len(markers)],
            markersize=6,
            markeredgecolor="white",
            markeredgewidth=0.8,
            alpha=0.95,
        )

    # Set y-axis bounds to [0, 1.0] so efficiency scale is consistent across plots
    plt.ylim(0, 1.0)
    ax = plt.gca()
    # Major ticks every 0.1, minor ticks every 0.05 for better precision
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.1))
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(0.05))
    ax.set_yticks(np.arange(0, 1.001, 0.05))
    ax.grid(which="major", alpha=0.5)
    ax.grid(which="minor", alpha=0.2)

    # Use a short main title and put the input parameters into a smaller, wrapped subtitle
    fig = plt.gcf()
    fig.suptitle("Algorithm Efficiency vs Reliability", fontsize=14)

    param_str = (
        f"semantics={semantics}, number_of_agents={number_of_agents}, "
        f"distribution_type={distribution_type}, efficiency_method=non-drastic"
    )
    # Set a wrapped subtitle on the Axes (will wrap when the figure is resized)
    ax.set_title(param_str, fontsize=11, loc="center", pad=1, wrap=True)

    # Leave space for the suptitle/subtitle when laying out
    plt.xlabel("Reliability")
    plt.ylabel("Efficiency")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot_graph()
    plot_graph(semantics="PR")
    plot_graph(semantics="CO")
