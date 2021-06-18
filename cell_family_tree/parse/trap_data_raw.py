import pandas as pd
import math
import os
import sys
from .helpers import write_csv
pd.options.mode.chained_assignment = None   # For predID assignment on query
import plotly.graph_objs as go
import numpy as np

"""
First parsing step. Concerned with the data files as a whole. -- FOR RAW FILES
"""


class TrapDataRaw:

    def __init__(self, file_name):
        self.file_name = file_name
        self.df = pd.read_csv("raw_data/{}".format(self.file_name))
        self.traps = list(self.df["trap_num"].unique())
        self.data_info = []

    def set_data_info(self, do_write=False):
        """
        Doc Doc Doc
        """

        print("TrapDataRaw:{} Setting Data Info...".format(self.file_name))

        data_info = [["trap_num", "time_max", "root_cell_count", "total_cell_count"]]
        all_pred_ids = []
        for trap_num in self.traps:
            trap_df = self.get_single_trap_df(trap_num)
            time_min, time_max = trap_df["time_num"].min(), trap_df["time_num"].max()
            root_cell_count = trap_df.query("time_num == {}".format(time_min))["total_objs"].unique()[0]
            total_cell_count = len(trap_df[trap_df["total_objs"] != 0].index)
            pred_ids = list(trap_df["predecessorID"].unique())
            pred_ids.sort()
            if 0 not in pred_ids:   # Represents a row with 0 cells, not present in all traps
                pred_ids = [0] + pred_ids
            pred_id_count = [len(trap_df[trap_df["predecessorID"] == p]) for p in pred_ids]
            if len(pred_ids) > len(all_pred_ids):
                all_pred_ids = pred_ids.copy()
            data_info.append([trap_num, time_max, root_cell_count, total_cell_count, len(pred_ids) - 1] + pred_id_count)

        data_info[0] += ["predId:{} Count".format(v) for v in all_pred_ids]
        data_info[0][5] = "empty_count"

        self.data_info = data_info

        if do_write:

            write_csv("reports/{}_TrapDataMetaAnalysis.csv".format(self.file_name.replace(".csv", "")), self.data_info)

    def get_single_trap_df(self, trap_num, t_stop=None):
        """
        Returns a new dataframe limited to a single trap_num with optional argument for an end time.
        Used as input for a TrapGraph.
        """

        print("TrapData:{} Getting Single Trap:{}...".format(self.file_name, trap_num))

        query = ""

        if trap_num:
            query += "trap_num == {}".format(trap_num)

        if t_stop:
            query += " and time_num <= {}".format(t_stop)

        if query[0] == " ":
            query = query[5:]

        df = self.df.query(query)

        # Remove Image Num & Image Path
        try:
            del df["image_num"]
        except KeyError:
            pass

        try:
            del df["image_path"]
        except KeyError:
            pass

        if not os.path.exists("recent"):
            os.mkdir("recent")

        df.to_csv("recent/recent_query_raw.csv", index=False)

        return df

    def plot_single_trap_df(self, trap_num, t_stop=None):

        print("Plot Single Trap - Hardcoded Atm")

        df = self.get_single_trap_df(trap_num, t_stop)

        fig = go.Figure()

        fig.layout.title["text"] = "TrapNum:{} TStop:{} SumArea/TimeNum".format(trap_num, t_stop)

        total_objs_per_time_num = []
        time_nums = []
        sum_area_per_time_num = []

        for t in df["time_num"].unique():

            time_df = df.query("time_num == {}".format(t))

            total_obj = time_df["total_objs"].unique()[0]
            sum_area = sum(time_df["area"])

            total_objs_per_time_num.append(total_obj)
            sum_area_per_time_num.append(sum_area)
            time_nums.append(t)

        ones = list(np.ones(len(total_objs_per_time_num)))

        fig.add_trace(go.Scatter(x=time_nums, y=sum_area_per_time_num, mode="lines+markers"))
        fig.add_trace(go.Scatter(x=time_nums, y=ones, text=total_objs_per_time_num, mode="text"))

        fig.show()
