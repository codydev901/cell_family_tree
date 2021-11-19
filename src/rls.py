import pandas as pd
import os
import numpy as np
from parse.trap_data import TrapData
from parse.rls_params import RLSParams

"""
Doc Doc Doc
"""


def main():

    if not os.path.exists("reports"):
        os.mkdir("reports")

    file_name = "BC8_yolo_v1.csv"

    trap_data = TrapData("BC8_yolo_v1.csv")
    rls_res = trap_data.get_rls_combined_all()

    res_df = pd.DataFrame(rls_res)
    res_df.to_csv("reports/{}_combined_rls_2.csv".format(file_name), index=False,
                  columns=["trap_num", "t_stop", "stop_condition", "start_obj", "exp_div", "pred_div"])


def analyse_stop_conditions():

    df = pd.read_csv("reports/BC8_yolo_v1.csv_combined_rls_2.csv")

    stop_conditions = list(df["stop_condition"].unique())

    stop_conditions = {v: [] for v in stop_conditions}

    count = 0
    for i, row in df.iterrows():
        error = abs(1.0 - (row["exp_div"] / row["pred_div"]))
        stop_conditions[row["stop_condition"]].append(error)
        count += 1

    for k in stop_conditions:
        stop_con = k
        percent_total = round(len(stop_conditions[k])/count, 2)
        mean_error = round(np.mean(stop_conditions[k]), 2)
        print("Condition:{}".format(stop_con))
        print("PercentTotal:{}".format(percent_total))
        print("MeanPercentError:{}".format(mean_error))
        print("")


    # print(df)

if __name__ == "__main__":

    # main()

    analyse_stop_conditions()
