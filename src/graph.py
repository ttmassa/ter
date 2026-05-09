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
        # convert index and values to numpy arrays
        x = efficiency.index.astype(float).to_numpy()
        y = efficiency.to_numpy(dtype=float)

        # apply a small horizontal jitter per series so overlapping markers/lines are visible
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

    # set y-axis bounds to [0, 1.0] so efficiency scale is consistent across plots
    plt.ylim(0, 1.0)
    ax = plt.gca()
    # Major ticks every 0.1, minor ticks every 0.05 for better precision
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.1))
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(0.05))
    ax.set_yticks(np.arange(0, 1.001, 0.05))
    ax.grid(which="major", alpha=0.5)
    ax.grid(which="minor", alpha=0.2)
    plt.tight_layout()
    plt.xlabel("Reliability")
    plt.ylabel("Efficiency")
    plt.title(f"Efficiency of algorithms for semantics={semantics}, number_of_agents={number_of_agents}, distribution_type={distribution_type}")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    plot_graph()
    plot_graph(semantics="PR")
    plot_graph(semantics="CO")
    # This main guard is for showing the issue with some obafs not returning the truth extension when reliability is 1.0
    # df = pd.read_csv("data/OBAF/obaf_metadata.csv")
    # print(f"Number of rows in the dataframe: {len(df)}")
    # print(f"Number of rows where reliability is 1.0: {len(df[df['reliability'] == 1.0])}")
    # print(f"Number of rows where reliability is 1.0 and cosar_base_score is 1: {len(df[(df['reliability'] == 1.0) & (df['cosar_base_score'] == 1)])}")
    # print(f"Number of rows where reliability is 1.0 and cosar_base_score is 0: {len(df[(df['reliability'] == 1.0) & (df['cosar_base_score'] == 0)])}")

    # df_reliability_1_cosar_base_score_0 = df[(df['reliability'] == 1.0) & (df['cosar_base_score'] == 0)]

    # def _fmt_num(val, field: str | None = None):
    #     if pd.isna(val):
    #         return ""
    #     try:
    #         f = float(val)
    #     except Exception:
    #         return str(val)

    #     # Preserve one decimal for reliability (e.g. 1.0 -> '1.0')
    #     if field == 'reliability':
    #         return f"{f:.1f}"

    #     # For beta and base_degree we want to drop trailing .0 when integer
    #     if field in ('beta', 'base_degree'):
    #         if f.is_integer():
    #             return str(int(f))
    #         return str(f)

    #     # Default: drop .0 for integer-valued fields like instance, number_arguments, number_of_agents
    #     if f.is_integer():
    #         return str(int(f))
    #     return str(f)

    # def _clean_truth(ext):
    #     if pd.isna(ext):
    #         return ""
    #     s = str(ext)
    #     if s.lower() in ("nan", "none", ""):
    #         return ""
    #     # remove pipe separators if present (e.g. a1|a2 -> a1a2)
    #     return s.replace("|", "")

    # file_names = []
    # for _, row in df_reliability_1_cosar_base_score_0.iterrows():
    #     sa = row.get('source_af_type', '')
    #     truth = _clean_truth(row.get('truth_extension', ''))
    #     num_args = _fmt_num(row.get('number_arguments', ''), 'number_arguments')
    #     pb = _fmt_num(row.get('cycle_probability', ''), 'cycle_probability')
    #     inst = _fmt_num(row.get('instance_number', ''), 'instance_number')
    #     rel = _fmt_num(row.get('reliability', ''), 'reliability')
    #     numagt = _fmt_num(row.get('number_of_agents', ''), 'number_of_agents')
    #     dist = str(row.get('distribution_type', ''))
    #     sem = str(row.get('semantics', ''))

    #     if sa == 'BA':
    #         file_name = (
    #             f"data/OBAF/BA/BA-numArg{num_args}-pbCycle{pb}-{inst}-sem{sem}-rel{rel}"
    #             f"-numAgt{numagt}-dist{dist}-truth{truth}.apx"
    #         )
    #     elif sa == 'WS':
    #         beta = _fmt_num(row.get('beta', ''), 'beta')
    #         base_degree = _fmt_num(row.get('base_degree', ''), 'base_degree')
    #         file_name = (
    #             f"data/OBAF/WS/WS-numArg{num_args}-pbCycle{pb}-beta{beta}-baseDegree{base_degree}-{inst}-sem{sem}-rel{rel}"
    #             f"-numAgt{numagt}-dist{dist}-truth{truth}.apx"
    #         )
    #     else:
    #         file_name = f"data/OBAF/{sa}/{sa}-numArg{num_args}-pbCycle{pb}-{inst}-sem{sem}-rel{rel}-numAgt{numagt}-dist{dist}-truth{truth}.apx"

    #     file_names.append(file_name)

    # print("File names where reliability is 1.0 and cosar_base_score is 0:")
    # from parser import read_apx
    # from cosar import run
    # count = 0
    # for file_name in file_names:
    #     if count >= 1:
    #         break
    #     print(file_name)
    #     obaf = read_apx(file_name)
    #     extensions, _ = run(obaf, "PR", aggregation_method="na")
    #     print("COSAR extensions:", extensions)
    #     count += 1
