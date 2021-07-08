import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats

"""
Doc Doc Doc
"""

def parse_results():
    result_df = pd.read_csv("reports/FT_BC8_yolo_short_RLSAnalysis.csv")

    trap_nums = result_df["trap_num"].tolist()
    ground_truth = result_df["experimental"].tolist()
    branch_rls = result_df["root_branch_count"].tolist()

    # Associate RLS with trap num
    ground_truth = [[t, v] for t, v in zip(trap_nums, ground_truth)]
    branch_rls = [[t, v] for t, v in zip(trap_nums, branch_rls)]

    # Assign 0 to Empty for Ground_Truth ("replace non_int_e") & set as int
    for v in ground_truth:
        try:
            v[1] = int(v[1])
        except ValueError:
            v[1] = 0

    # Set int on branch RLS and remove parse_fails
    branch_rls_temp = []
    for v in branch_rls:
        try:
            v[1] = int(v[1])
            branch_rls_temp.append(v)
        except ValueError:
            continue
    branch_rls = branch_rls_temp

    # Remove associated parse_fail traps from ground_truth
    ground_truth = [v for v in ground_truth if v[0] in [v1[0] for v1 in branch_rls]]

    # Sort Ground_Truth RLS from least to greatest
    ground_truth.sort(key=lambda x: x[1])

    # Sort Predicted RLS by Ground_Truth trap_num
    branch_rls_temp = []
    for v1 in ground_truth:
        for v2 in branch_rls:
            if v1[0] == v2[0]:
                branch_rls_temp.append(v2)
                break
    branch_rls = branch_rls_temp

    return branch_rls, ground_truth


def lin_reg(x, y):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    return {"slope": slope,
            "intercept": intercept,
            "r_value": r_value,
            "p_value": p_value,
            "std_error": std_err}


def predict_lin_reg(reg_dict, trap_index):
    x = [v[0] for v in trap_index]
    y = [v * reg_dict["slope"] + reg_dict["intercept"] for v in x]

    return y


def plot_scatter(branch_rls, ground_truth, trap_index,
                 branch_rls_reg, ground_truth_reg):

    fig = go.Figure()
    fig.update_layout(
        title="Ground Truth vs Branch RLS",
        xaxis_title="Trap Index (Sorted Least to Greatest by Ground Truth RLS)",
        yaxis_title="RLS (Branch Count/Mother Cell Divisions)",
        legend_title="Legend",
    )

    fig.add_trace(go.Scatter(x=[v[0] for v in trap_index],
                             y=[v[1] for v in ground_truth],
                             mode='markers',
                             name='ground_truth',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[0] for v in trap_index],
                             y=[v[1] for v in branch_rls],
                             mode='markers',
                             name='experimental_branch',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[0] for v in trap_index],
                             y=predict_lin_reg(ground_truth_reg, trap_index),
                             mode='lines',
                             name='ground_truth_reg',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[0] for v in trap_index],
                             y=predict_lin_reg(branch_rls_reg, trap_index),
                             mode='lines',
                             name='experimental_branch_reg',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.show()


def main():

    branch_rls, ground_truth = parse_results()

    trap_index = [[i, v[0]] for i, v in enumerate(branch_rls)]

    ground_reg = lin_reg(x=[v[0] for v in trap_index], y=[v[1] for v in ground_truth])
    branch_reg = lin_reg(x=[v[0] for v in trap_index], y=[v[1] for v in branch_rls])

    print("Ground Truth Regression Stats")
    print(ground_reg)
    print("Branch RLS Regression Stats")
    print(branch_reg)

    plot_scatter(branch_rls, ground_truth, trap_index, branch_reg, ground_reg)






if __name__ == "__main__":

    main()
