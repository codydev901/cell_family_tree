import sys
import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objs as go


"""
Doc Doc Doc

notes 8/13

Notes fit sin wave
missing event in time lapse micro/frames

"""


class RLSPredID:

    def __init__(self, df, params):
        self.df = df
        self.params = params
        self.trap_num = None
        self.start_num_obj = 0
        self.t_stop = 0
        self.stop_condition = "Full"
        self.time_num = []
        self.time_sum_area = []
        self.time_sum_area_descriptive = []
        self.time_num_obj = []
        self.peaks = []
        self.troughs = []
        self.peak_areas = []
        self.num_divisions = 0
        self.num_divisions_trough = 0
        self.index_div = []
        self._on_init()

    def _on_init(self):
        """
        Doc Doc Doc
        """

        self.trap_num = self.df["trap_num"].tolist()[0]

        self.start_num_obj = self.df.query("time_num == 1")["total_objs"].tolist()[0]

        self.t_stop = self.df["time_num"].max()
        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {}".format(t))
            total_obj = time_df["total_objs"].unique()[0]
            sum_area = sum(time_df["area"])
            self.time_num_obj.append(total_obj)
            self.time_sum_area.append(sum_area)
            self.time_num.append(t)

        self._find_peaks()
        self._find_troughs()

        for t in self.df["time_num"].unique():
            is_peak = False
            is_trough = False

            if t-1 in self.peaks:
                is_peak = True
            if t-1 in self.troughs:
                is_trough = True

            desc = {"time_num": t,
                    "index": t-1,
                    "sum_area": self.time_sum_area[t-1],
                    "num_objs": self.time_num_obj[t-1],
                    "is_peak": is_peak,
                    "is_trough": is_trough}

            self.time_sum_area_descriptive.append(desc)

        self._determine_stop_time_num()

    def _find_peaks(self):

        self.peaks = find_peaks(self.time_sum_area, distance=self.params.peak_distance)
        self.peaks = list(self.peaks)[0]

    def _find_troughs(self):

        inverted_area = [v*-1 for v in self.time_sum_area]
        self.troughs = find_peaks(inverted_area, distance=self.params.peak_distance)
        self.troughs = list(self.troughs)[0]

    def _find_peak_trough_neighbors(self, i):
        """

        """
        next_peak = next((v for v in self.time_sum_area_descriptive[i+1:] if v["is_peak"]), None)
        next_trough = next((v for v in self.time_sum_area_descriptive[i+1:] if v["is_trough"]), None)

        return next_peak, next_trough

    def _determine_stop_time_num(self):
        """
        Check Images/Experimental


        Trap 92
        Trap 59
        """


        print("AHHH")
        print(self.peaks)
        print(self.troughs)

        for i, sum_area in enumerate(self.time_sum_area):

            time_num = self.time_num[i]
            num_obj = self.time_num_obj[i]
            avg_peak_area = 0
            if self.peak_areas:
                avg_peak_area = np.mean(self.peak_areas)

            if i in self.peaks:
                next_peak, next_trough = self._find_peak_trough_neighbors(i)
                print(i, next_peak, next_trough)
                self.num_divisions += 1
                self.index_div.append(i)
                self.peak_areas.append(self.time_sum_area[i])

            if i in self.troughs:
                self.num_divisions_trough += 1

            # No Cells Detected
            if num_obj == 0:
                self.stop_condition = "No Cells"
                self.t_stop = time_num
                print("Break No Cells", time_num, self.num_divisions)
                break

            # Next X Cells 1 Obj
            if self.time_num_obj[i:i + self.params.next_cells_1_obj_range].count(1) == self.params.next_cells_1_obj_count and self.num_divisions >= self.params.num_divisions_threshold:
                self.stop_condition = "No Divisions - Num Obj 1"
                self.t_stop = time_num
                print("Break No Divisions - Num Obj 1", time_num, self.num_divisions)
                break

            # Next X Cells Little Area Change
            if np.std(self.time_sum_area[i:i + self.params.std_change_range]) <= self.params.std_change_threshold and self.num_divisions >= self.params.num_divisions_threshold:
                self.stop_condition = "No Divisions - Area STD"
                self.t_stop = time_num
                print("Break No Divisions - Area STD", time_num, self.num_divisions)
                break

            # Large ObjCount Drop Followed By ObjCount Noise
            if self.time_num_obj[i] >= self.params.obj_drop_current and self.time_num_obj[i+1] <= self.params.obj_drop_next:
                next_obj_counts = list(set(self.time_num_obj[i+1:i+self.params.obj_drop_noise_range]))
                if len(next_obj_counts) > self.params.obj_drop_noise_threshold:
                    print(next_obj_counts)
                    self.stop_condition = "Large Obj Count Drop + Noise"
                    self.t_stop = time_num
                    print("Large Obj Count Drop + Noise", time_num, self.num_divisions)
                    break

            # Increase above Average Peak in Later Time Num
            if (self.time_sum_area[i] > avg_peak_area * self.params.avg_peak_constant) and self.time_num[i] > self.params.avg_peak_time_threshold and (i not in self.peaks):
                self.stop_condition = "Area Surpassed Avg Peak"
                self.t_stop = time_num
                print("Break No Divisions - AvgPeak Max Threshold", time_num, self.num_divisions)
                break

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
                "pred_div": self.num_divisions, "trap_num": self.trap_num,
                "start_obj": self.start_num_obj}

    def plot_peaks(self):
        """
        Doc Doc Doc

        :return:
        """

        fig = go.Figure()

        fig.layout.title["text"] = "TrapNum:{} TStop:{} SumArea/TimeNum PeakFind".format(self.trap_num, self.t_stop)

        peak_all = [self.time_sum_area[i] if i in self.peaks else 0.0 for i in range(len(self.time_sum_area))]
        peak_stop = [self.time_sum_area[i] if i in self.index_div else 0.0 for i in range(len(self.time_sum_area))]
        trough_all = [self.time_sum_area[i] if i in self.troughs else 0.0 for i in range(len(self.time_sum_area))]

        ones = list(np.ones(len(self.time_num_obj)))

        fig.add_trace(go.Scatter(x=self.time_num, y=self.time_sum_area, mode="lines+markers", name="sum_area_signal"))
        fig.add_trace(go.Scatter(x=self.time_num, y=peak_all, mode="markers", name="all_peaks"))
        fig.add_trace(go.Scatter(x=self.time_num, y=peak_stop, mode="markers", name="stop_peaks"))
        fig.add_trace(go.Scatter(x=self.time_num, y=trough_all, mode="markers", name="all_troughs"))
        fig.add_trace(go.Scatter(x=self.time_num, y=ones, text=self.time_num_obj, mode="text", name="obj_count"))

        fig.show()