import pandas as pd
import os

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
    rls_res = trap_data.get_rls_peak_all(params=RLSParams())

    res_df = pd.DataFrame(rls_res)
    res_df.to_csv("reports/{}_combined_rls.csv".format(file_name), index=False,
                  columns=["trap_num", "t_stop", "stop_condition", "start_obj", "exp_div", "pred_div"])


if __name__ == "__main__":

    main()
