import sys
import pandas as pd
import os

from parse.trap_data import TrapData


"""
Doc Doc Doc
"""


def main():

    trap_num = sys.argv[1]

    if not os.path.exists("reports"):
        os.mkdir("reports")

    file_name = "BC8_yolo_v1.csv"

    trap_data = TrapData(file_name)
    rls_res = trap_data.get_rls_combined(trap_num=int(trap_num), get_rls_obj=True)

    if rls_res:
        rls_res.plot_sum_area_signal()
        # rls_res.plot_animation_x_y()
        print("OK")
        print(rls_res.exp_count)
        print(rls_res.num_divisions)
    else:
        print("Unsupported Exp Res")



if __name__ == "__main__":

    main()