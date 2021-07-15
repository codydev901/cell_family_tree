import pandas as pd
import numpy as np
import sys
import os
from scipy.signal import argrelextrema
from scipy.signal import find_peaks, find_peaks_cwt
import plotly.graph_objs as go
from .helpers import write_csv

"""
Doc Doc Doc
"""


class TrapGraphPeak:

    def __init__(self, df, file_name=None):
        self.df = df
        self.file_name = file_name
        self.trap_num = None
        self.t_stop = 0
        self.stop_condition = "Full"
        self.time_num = []
        self.time_sum_area = []
        self.time_num_obj = []
        self.peaks = []
        self.num_divisions = 0
        self.index_div = []
        self._on_init()

    def _on_init(self):
        """
        Doc Doc Doc
        """

        starting_num_objs = self.df.query("time_num == 1")["total_objs"].tolist()[0]
        if starting_num_objs != 1:
            raise ValueError("Multiple or No Objects at T1 - Not supported at the moment")

        self.trap_num = self.df["trap_num"].tolist()[0]

        self.t_stop = self.df["time_num"].max()
        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {}".format(t))
            total_obj = time_df["total_objs"].unique()[0]
            sum_area = sum(time_df["area"])
            self.time_num_obj.append(total_obj)
            self.time_sum_area.append(sum_area)
            self.time_num.append(t)

        self._find_peaks()
        self._determine_stop_time_num()

    def _find_peaks(self):

        self.peaks = find_peaks(self.time_sum_area, distance=5)
        self.peaks = list(self.peaks)[0]

    def _determine_stop_time_num(self):

        print(self.peaks)
        for i, sum_area in enumerate(self.time_sum_area):

            time_num = self.time_num[i]
            num_obj = self.time_num_obj[i]

            if i in self.peaks:
                print("AT PEAK")
                print(i, time_num, num_obj)
                self.num_divisions += 1
                self.index_div.append(i)

            # No Cells Detected
            if num_obj == 0:
                self.stop_condition = "No Cells"
                self.t_stop = time_num
                print("Break No Cells", time_num, self.num_divisions)
                break

            # Next X Cells 1 Obj
            if self.time_num_obj[i:i + 5].count(1) == 5 and self.num_divisions >= 2:
                self.stop_condition = "No Divisions - Num Obj 1"
                self.t_stop = time_num
                print("Break No Divisions - Num Obj 1", time_num, self.num_divisions)
                break

            # Next X Cells Little Area Change
            if np.std(self.time_sum_area[i:i + 5]) <= 5.0 and self.num_divisions >= 2:
                self.stop_condition = "No Divisions - Area STD"
                self.t_stop = time_num
                print("Break No Divisions - Area STD", time_num, self.num_divisions)
                break

            # # Sudden Drop in Area (TESTING)
            # if sum_area - self.time_sum_area[i+1] >= 125 and self.num_divisions >= 2:
            #     self.stop_condition = "Sudden Area Drop"
            #     self.t_stop = time_num
            #     print("Break No Divisions - Area Drop", time_num, self.num_divisions)
            #     break

    def plot_peaks(self):

        print("Plot Single Trap - Hardcoded Atm")

        fig = go.Figure()

        fig.layout.title["text"] = "TrapNum:{} TStop:{} SumArea/TimeNum PeakFind".format(self.trap_num, self.t_stop)

        peak_all = [self.time_sum_area[i] if i in self.peaks else 0.0 for i in range(len(self.time_sum_area))]
        peak_stop = [self.time_sum_area[i] if i in self.index_div else 0.0 for i in range(len(self.time_sum_area))]

        ones = list(np.ones(len(self.time_num_obj)))

        fig.add_trace(go.Scatter(x=self.time_num, y=self.time_sum_area, mode="lines+markers"))
        fig.add_trace(go.Scatter(x=self.time_num, y=peak_all, mode="markers"))
        fig.add_trace(go.Scatter(x=self.time_num, y=peak_stop, mode="markers"))
        fig.add_trace(go.Scatter(x=self.time_num, y=ones, text=self.time_num_obj, mode="text"))

        fig.show()

