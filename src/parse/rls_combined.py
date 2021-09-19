import sys
import math
import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objs as go
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

"""
Use's Sum Area Curve + Obj Coordinates and Area To Construct A Simple Tree and Count Mother Cell Related RLS.


Logic
1. Find and Assign Mother Cell Lineage. Mother cell assumed to be present at time_num 0. Determine when/if Mother cell
is lost due to physical factors.



"""


class RLSCombined:

    def __init__(self, df, exp_count):
        self.df = df
        self.exp_count = exp_count
        self.trap_num = None
        self.start_num_obj = 0
        self.t_stop = 0
        self.mother_lost_t = 0
        self.time_num = []
        self.time_sum_area = []
        self.time_sum_area_descriptive = []
        self.time_num_obj = []
        self.peaks = []
        self.troughs = []
        self.peak_areas = []
        self.num_divisions = 0
        self.index_div = []
        self.graph = {}
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

        self.df["is_mother_cell"] = [False]*len(self.df)
        self.df["last_mother_cost"] = [0.0]*len(self.df)

        self._assign_mother_cell()
        self._run_rls()

    def _find_peaks(self):

        self.peaks = find_peaks(self.time_sum_area, distance=5)
        self.peaks = list(self.peaks)[0]

    def _find_troughs(self):

        inverted_area = [v*-1 for v in self.time_sum_area]
        self.troughs = find_peaks(inverted_area, distance=5)
        self.troughs = list(self.troughs)[0]

    def _calc_assign_cost(self, old_cell, new_cell):

        xy_distance = math.hypot(new_cell["obj_X"] - old_cell["obj_X"], new_cell["obj_Y"] - old_cell["obj_Y"])
        area_change = abs(1 - new_cell["area"]/old_cell["area"])

        return xy_distance + area_change

    def _link_cells(self, last_time_df, curr_time_df):
        """
        Doc Doc Doc
        """

        costs = []

        for i1, old_cell in last_time_df.iterrows():
            for i2, new_cell in curr_time_df.iterrows():
                print(i1, i2)
                cost = self._calc_assign_cost(old_cell, new_cell)
                costs.append([i1, i2, cost])

        return costs

    def _assign_mother_cell(self):
        """
        Need to clean this up, some repeated logic.
        """

        # In case only 1 Object, Mother Cell assumed to be Object at TimeNum 1.
        if self.start_num_obj == 1:

            mother_cell = self.df.loc[0]
            mother_cell_costs = []

            for t in self.df["time_num"].unique():
                time_df = self.df.query("time_num == {}".format(t))

                mother_cell_distances = []
                for i, row in time_df.iterrows():
                    mother_cell_distances.append([i, self._calc_assign_cost(mother_cell, row)])

                mother_cell_distances.sort(key=lambda x: x[1])
                closest_cell_index = mother_cell_distances[0][0]
                closest_cell_cost = mother_cell_distances[0][1]
                mother_cell_costs.append(closest_cell_cost)
                self.df.at[closest_cell_index, "is_mother_cell"] = True
                self.df.at[closest_cell_index, "last_mother_cost"] = closest_cell_cost
                for v in mother_cell_distances[1:]:
                    self.df.at[v[0], "last_mother_cost"] = v[1]
                mother_cell = self.df.loc[closest_cell_index]

            return

        # In case of multiple starting objects, calculate costs for first X time_nums to find a main branch, then re-run
        # after setting that cell as mother w/ same logic as above.

        start_time_df = self.df.query("time_num == 1")
        potential_mothers = []

        for i, start_cell in start_time_df.iterrows():

            mother_cell = self.df.loc[i]
            mother_cell_costs = []

            for i2, t in enumerate(self.df["time_num"].unique()[:150]):

                # Break if Area Reaches 0/No Cells
                if self.time_sum_area[i2] == 0:
                    break

                time_df = self.df.query("time_num == {}".format(t))

                mother_cell_distances = []
                for i3, row in time_df.iterrows():
                    mother_cell_distances.append([i, self._calc_assign_cost(mother_cell, row)])

                mother_cell_distances.sort(key=lambda x: x[1])
                closest_cell_index = mother_cell_distances[0][0]
                closest_cell_cost = mother_cell_distances[0][1]
                mother_cell_costs.append(closest_cell_cost)
                mother_cell = self.df.loc[closest_cell_index]

            potential_mothers.append([i, sum(mother_cell_costs)])

        potential_mothers.sort(key=lambda x: x[1])
        mother_cell_i = potential_mothers[0][0]
        mother_cell = self.df.loc[mother_cell_i]
        mother_cell_costs = []

        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {}".format(t))

            mother_cell_distances = []
            for i, row in time_df.iterrows():
                mother_cell_distances.append([i, self._calc_assign_cost(mother_cell, row)])

            mother_cell_distances.sort(key=lambda x: x[1])
            closest_cell_index = mother_cell_distances[0][0]
            closest_cell_cost = mother_cell_distances[0][1]
            mother_cell_costs.append(closest_cell_cost)
            self.df.at[closest_cell_index, "is_mother_cell"] = True
            self.df.at[closest_cell_index, "last_mother_cost"] = closest_cell_cost
            for v in mother_cell_distances[1:]:
                self.df.at[v[0], "last_mother_cost"] = v[1]
            mother_cell = self.df.loc[closest_cell_index]

        return

    def _run_rls(self):
        """
        Doc Doc Doc
        """

        last_time_df = self.df.query("time_num == 1")
        for time_num in self.time_num:
            curr_time_df = self.df.query("time_num == {}".format(time_num))
            cell_costs = self._link_cells(last_time_df, curr_time_df)
            last_time_df = curr_time_df

            print(time_num, cell_costs)

            if time_num > 15:
                sys.exit()

    def results(self):
        """
        Doc Doc Doc
        """

        return {"t_stop": self.t_stop, "stop_condition": self.stop_condition,
                "pred_div": self.num_divisions, "trap_num": self.trap_num,
                "start_obj": self.start_num_obj}

    def plot_sum_area_signal(self):
        """
        Doc Doc Doc
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

    def plot_animation_x_y(self, trap_num):
        """
        Doc Doc Doc
        """

        cell_coordinates = []

        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {} & trap_num == {}".format(t, trap_num))

            cell_c_temp = []
            for i, row in time_df.iterrows():
                cell_c_temp.append({"x": row["obj_X"],
                                    "y": row["obj_Y"],
                                    "area": row["area"],
                                    "time": row["time_num"]})
            cell_c_temp.sort(key=lambda x: x["area"], reverse=True)
            for v in cell_c_temp:
                cell_coordinates.append(v)

        df = pd.DataFrame(cell_coordinates)

        print(df.head)

        fig = px.scatter(df, x="x", y="y", color="area", title="Trap:{} X/Y Over Time".format(trap_num),
                         animation_frame="time", range_x=[0, 60], range_y=[0, 60], size="area",
                         color_continuous_scale=[(0, "cyan"), (1, "red")])

        fig.show()