import sys
import pandas as pd
import os

from parse.trap_data import TrapData
from parse.rls_params import RLSParams


"""
Doc Doc Doc
"""


def main():

    trap_num = sys.argv[1]

    if not os.path.exists("reports"):
        os.mkdir("reports")

    file_name = "BC8_yolo_v1.csv"

    trap_data = TrapData(file_name)
    rls_res = trap_data.get_rls_pred_id(trap_num=int(trap_num), params=RLSParams(), get_rls_obj=True)

    print("Peak Div", rls_res.num_divisions)
    print("Trough Div", rls_res.num_divisions_trough)
    print(rls_res.time_sum_area_descriptive)
    rls_res.plot_peaks()


if __name__ == "__main__":

    main()