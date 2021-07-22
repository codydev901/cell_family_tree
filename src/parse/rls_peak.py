import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objs as go


"""
Doc Doc Doc
"""


class RLSPeak:

    def __init__(self, df):
        self.df = df
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
        """
        Check Images/Experimental


        Trap 92
        Trap 59
        """

        for i, sum_area in enumerate(self.time_sum_area):

            time_num = self.time_num[i]
            num_obj = self.time_num_obj[i]

            if i in self.peaks:
                # print("AT PEAK")
                # print(i, time_num, num_obj)
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
            if np.std(self.time_sum_area[i:i + 7]) <= 4.5 and self.num_divisions >= 2:
                self.stop_condition = "No Divisions - Area STD"
                self.t_stop = time_num
                print("Break No Divisions - Area STD", time_num, self.num_divisions)
                break

            # Large ObjCount Drop Followed By ObjCount Noise
            if self.time_num_obj[i] >= 6 and self.time_num_obj[i+1] <= 2:
                next_obj_counts = list(set(self.time_num_obj[i+1:i+21]))
                if len(next_obj_counts) > 2:
                    print(next_obj_counts)
                    self.stop_condition = "Large Obj Count Drop + Noise"
                    self.t_stop = time_num
                    print("Large Obj Count Drop + Noise", time_num, self.num_divisions)
                    break

            # # Massive Increase in Area
            # if self.time_sum_area[i+1] - self.time_sum_area[i] >= 300:
            #     self.stop_condition = "Area Increase"
            #     self.t_stop = time_num
            #     print("Break No Divisions - Area Increase", time_num, self.num_divisions)
            #     break

            # # Sudden Drop in Area (TESTING)
            # if sum_area - self.time_sum_area[i+1] >= 125 and self.num_divisions >= 2:
            #     self.stop_condition = "Sudden Area Drop"
            #     self.t_stop = time_num
            #     print("Break No Divisions - Area Drop", time_num, self.num_divisions)
            #     break

            # Sudden Drop in Area Followed By Rise - TrapNum 46 Time 200
            # Massive Increase In Area - TrapNum 39 Time 200
            # 4 ObjCountDrop Post 200 - TrapNum 33 Time 391

    def results(self):
        """
        Doc Doc Doc

        :return:
        """

        return {"t_stop": self.t_stop, "stop_condition": self.stop_condition,
                "pred_div": self.num_divisions, "trap_num": self.trap_num}

    def plot_peaks(self):
        """
        Doc Doc Doc

        :return:
        """

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
