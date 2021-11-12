import sys
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats

"""
Doc Doc Doc
"""


def parse_results(rls_df):

    if type(rls_df) == str:
        rls_df = pd.read_csv("reports/{}".format(rls_df))

    trap_nums = rls_df["trap_num"].tolist()
    ground_truth = rls_df["exp_div"].tolist()

    branch_rls = rls_df["pred_div"].tolist()

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

    residuals = [abs(v1[1] - v2[1]) for v1, v2 in zip(ground_truth, branch_rls)]

    return branch_rls, ground_truth, residuals


def lin_reg(x, y):
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    return {"slope": slope,
            "intercept": intercept,
            "r_value": r_value,
            "p_value": p_value,
            "std_error": std_err}


def predict_lin_reg(reg_dict, trap_index):
    try:
        x = [v[0] for v in trap_index]
    except TypeError:
        x = trap_index
    y = [v * reg_dict["slope"] + reg_dict["intercept"] for v in x]

    return y


def plot_scatter(branch_rls, ground_truth, combined_reg, trap_index,
                 branch_rls_reg, ground_truth_reg):

    fig = go.Figure()
    fig.update_layout(
        title="Ground Truth vs Combined RLS",
        xaxis_title="Trap Index (Sorted Least to Greatest by Ground Truth RLS)",
        yaxis_title="RLS (Predicted Cell Divisions)",
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
                             name='predicted',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[1] for v in ground_truth],
                             y=[v[1] for v in branch_rls],
                             mode='markers',
                             name='combined',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[0] for v in trap_index],
                             y=predict_lin_reg(ground_truth_reg, trap_index),
                             mode='lines',
                             name='ground_truth_reg',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[0] for v in trap_index],
                             y=predict_lin_reg(branch_rls_reg, trap_index),
                             mode='lines',
                             name='predicted_reg',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.add_trace(go.Scatter(x=[v[1] for v in ground_truth],
                             y=predict_lin_reg(combined_reg, [v[1] for v in ground_truth]),
                             mode='lines',
                             name='combined_lin_reg',
                             text=["Trap: {}".format(v[1]) for v in trap_index]))

    fig.show()


def main():

    branch_rls, ground_truth, residuals = parse_results("BC8_yolo_v1.csv_combined_rls.csv")

    trap_index = [[i, v[0]] for i, v in enumerate(branch_rls)]

    ground_reg = lin_reg(x=[v[0] for v in trap_index], y=[v[1] for v in ground_truth])
    branch_reg = lin_reg(x=[v[0] for v in trap_index], y=[v[1] for v in branch_rls])
    ground_y = [v[1] for v in ground_truth]
    branch_y = [v[1] for v in branch_rls]

    print("Ground Truth")
    print(ground_y)
    print("Predicted")
    print(branch_y)

    combined_reg = lin_reg(x=ground_y, y=branch_y)

    print("Sum Residuals")
    print(sum(residuals))
    print("Combined Regression Stats")
    print(combined_reg)
    print("R^2 = {}".format(combined_reg["r_value"]*combined_reg["r_value"]))

    plot_scatter(branch_rls, ground_truth, combined_reg, trap_index, branch_reg, ground_reg)






if __name__ == "__main__":

    main()
