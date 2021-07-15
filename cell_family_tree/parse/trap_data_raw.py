import pandas as pd
import math
import os
import sys
from .helpers import write_csv
pd.options.mode.chained_assignment = None   # For predID assignment on query
import plotly.graph_objs as go
import numpy as np
import numpy as np
from scipy.optimize import leastsq
from scipy.signal import find_peaks, find_peaks_cwt

"""
First parsing step. Concerned with the data files as a whole. -- FOR RAW FILES
"""


class TrapDataRaw:

    def __init__(self, file_name):
        self.file_name = file_name
        self.df = pd.read_csv("raw_data/{}".format(self.file_name))
        self.traps = list(self.df["trap_num"].unique())

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

        avg_cell_area = sum([a / c for a, c in zip(sum_area_per_time_num, total_objs_per_time_num)]) / len(sum_area_per_time_num)

        reduced_sum_per_time_num = []

        for a, c in zip(sum_area_per_time_num, total_objs_per_time_num):
            if c <= 2:
                reduced_sum_per_time_num.append(a)
            else:
                diff = c - 2
                reduced_sum_per_time_num.append(a - (diff*avg_cell_area))

        ones = list(np.ones(len(total_objs_per_time_num)))

        fig.add_trace(go.Scatter(x=time_nums, y=sum_area_per_time_num, mode="lines+markers"))
        fig.add_trace(go.Scatter(x=time_nums, y=ones, text=total_objs_per_time_num, mode="text"))

        fig.show()

    def plot_single_trap_df_peak(self, trap_num, t_stop=None):

        print("Plot Single Trap - Hardcoded Atm")

        df = self.get_single_trap_df(trap_num, t_stop)

        fig = go.Figure()

        fig.layout.title["text"] = "TrapNum:{} TStop:{} SumArea/TimeNum PeakFind".format(trap_num, t_stop)

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

        peaks = find_peaks(sum_area_per_time_num, distance=5)
        peaks = list(peaks)[0]
        peak_y = [sum_area_per_time_num[i] if i in peaks else 0.0 for i in range(len(sum_area_per_time_num))]


        ones = list(np.ones(len(total_objs_per_time_num)))

        fig.add_trace(go.Scatter(x=time_nums, y=sum_area_per_time_num, mode="lines+markers"))
        fig.add_trace(go.Scatter(x=time_nums, y=peak_y, mode="markers"))
        fig.add_trace(go.Scatter(x=time_nums, y=ones, text=total_objs_per_time_num, mode="text"))

        fig.show()
