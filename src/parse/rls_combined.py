import sys
import math
import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
pd.options.mode.chained_assignment = None  # default='warn'

"""
Use's Sum Area Curve + Obj Coordinates and Area To Construct A Simple Tree and Count Mother Cell Related RLS.


Logic
1. Calculate SumAreaSignal. Sum of all cell area's at each time_num. We will reference this later on when looking for
"missed" cell divisions.

2. Find and Assign Mother Cell Lineage. Mother cell assumed to be present at time_num 0. If single cell at time_num 1,
then that single cell is set automatically as mother cell. If multiple cells, cost function runs for each starting cell
to assign a continuation sequence out to 150 nodes. The starting cell with the lowest sum cost of this calculation is 
then set as mother cell. Assumes that mother cell will stay more consistent in both location and size in relation 
to daughter and debris cells. By assigning mother cell lineage at start, we simplify the search for daughters. 
The full mother cell calculation runs for entire trap. We limit the starting search to first 150 since there seemed 
to be a higher likely-hood of things getting messy after that point than before it.
"""


class RLSCombined:

    def __init__(self, trap_number, trap_df, experimental_count):
        # Args
        self.trap_num = trap_number
        self.raw_df = trap_df.copy()
        self.df = trap_df
        self.experimental_count = experimental_count
        # On Init
        self.start_num_obj = 0
        self.t_stop = 0
        self.sum_area_signal = []
        self.mother_cell_costs = []
        self.peak_indices = []
        self.trough_indices = []
        self.num_divisions = 0
        self.division_events = []

        # Presentation Support
        self.mother_cell_info = {}

        self._on_init()

    def _on_init(self):
        """
        Doc Doc Doc
        """

        # Calc some preliminary information
        self.start_num_obj = self.df.query("time_num == 1")["total_objs"].tolist()[0]
        self.t_stop = self.df["time_num"].max()

        # Add new columns. Will update below.
        self.df["is_mother_cell"] = [False] * len(self.df)
        self.df["is_daughter_cell"] = [False] * len(self.df)
        self.df["last_mother_cost"] = [0.0] * len(self.df)

        # Calc SumArea Signal With All Objs
        self._calc_sum_area_signal()

        # Determine Mother and Daughter Cells. Remove other cell from DataFrame.
        self._assign_mother_cell_lineage()

        self._assign_daughter_cell_lineage()
        self.df = self.df.loc[(self.df['is_mother_cell'] == 1) | (self.df["is_daughter_cell"] == 1)]
        # self.df = self.df.loc[(self.df['is_mother_cell'] == 1)] # | (self.df["is_daughter_cell"] == 1)]
        # self.df = self.df.loc[(self.df["is_daughter_cell"] == 1)]

        # Re-calculate SumArea Signal with only mother and daughter
        self._calc_sum_area_signal()

        # Find Peak and Trough From Mother-Daughter Signal
        self._find_peaks()
        self._find_troughs()

        # Write .csv
        self.df.to_csv("recent/{}_MD.csv".format(self.trap_num))

        # Run RLS Algorithm
        self._run_rls()

    def _find_peaks(self):
        sum_area = [v["area"] for v in self.sum_area_signal]
        self.peak_indices = list(find_peaks(sum_area, distance=5))[0]

    def _find_troughs(self):
        inverted_area = [v["area"]*-1 for v in self.sum_area_signal]
        self.trough_indices = list(find_peaks(inverted_area, distance=5))[0]

    def _calc_sum_area_signal(self):
        self.sum_area_signal = []
        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {}".format(t))
            total_obj = len(time_df["area"])
            sum_area = sum(time_df["area"])
            self.sum_area_signal.append({"area": sum_area,
                                         "obj_count": total_obj,
                                         "time_num": t})

    @staticmethod
    def _calc_same_cell_cost(old_cell, new_cell):
        """
        Compares two cells (at different, but adjacent) time points. Lower score indicates higher likelihood of then
        being the same cell.
        :param old_cell: row in DF
        :param new_cell: row in DF
        :return: cost score (float)
        """

        xy_distance = math.hypot(new_cell["obj_X"] - old_cell["obj_X"], new_cell["obj_Y"] - old_cell["obj_Y"])
        area_change = abs(1 - new_cell["area"]/old_cell["area"]) * 10.0  # To better relate magnitude to xy_distance

        return xy_distance + area_change

    @staticmethod
    def _calc_potential_daughter_cost(mother_cell, last_daughter_cell, compare_cell):
        """
        Daughter cost is combination of distance to mother + comparison to last assigned daughter.

        :param mother_cell: row in DF
        :param compare_cell: row in DF
        :return: boolean + daughter cost score
        """

        mother_x, mother_y = mother_cell["obj_X"], mother_cell["obj_Y"]
        daughter_x, daughter_y = compare_cell["obj_X"], compare_cell["obj_Y"]

        d_x = abs(mother_x - daughter_x)
        # Minimal Variation in X
        if (abs(mother_x - daughter_x)) > 5:
            return False, None

        d_y = abs(10 - abs(mother_y - daughter_y))
        # Y distance around 10
        if abs(mother_y - daughter_y) < 5 or abs(mother_y - daughter_y) > 15:
            return False, None

        mother_distance = d_x + d_y
        last_daughter_cost = 0.0
        if last_daughter_cell is not None:
            last_daughter_cost = RLSCombined._calc_same_cell_cost(last_daughter_cell, compare_cell)

        return True, mother_distance + last_daughter_cost

    def _assign_mother_cell_lineage(self):
        """
        Assigns mother_cell = True to relevant objects in DataFrame.
        """

        # Get cells that exist at the first time step.
        start_time_df = self.df.query("time_num == 1")
        potential_mothers = []

        # Run cost function for above cells to determine which is mother.
        for i, start_cell in start_time_df.iterrows():

            mother_cell = self.df.loc[i]
            mother_cell_costs = []

            for i2, t in enumerate(self.df["time_num"].unique()[:150]):

                # Break if Area Reaches 0/No Cells
                if self.sum_area_signal[i2]["area"] == 0 or self.sum_area_signal[i2]["obj_count"] == 0:
                    break

                # Another DataFrame for iterative time.
                time_df = self.df.query("time_num == {}".format(t))

                # Compare current mother cell to each cell at this time.
                mother_cell_distances = []
                for i3, compare_cell in time_df.iterrows():
                    mother_cell_distances.append([i, self._calc_same_cell_cost(mother_cell, compare_cell)])

                # Sort costs, re-assign mother cell for next step.
                mother_cell_distances.sort(key=lambda x: x[1])
                closest_cell_index = mother_cell_distances[0][0]
                closest_cell_cost = mother_cell_distances[0][1]
                mother_cell_costs.append(closest_cell_cost)
                mother_cell = self.df.loc[closest_cell_index]

            # Update with final result for this starting cell.
            potential_mothers.append([i, sum(mother_cell_costs)])

        # Sort the potential mother cell lineage scores, choose lowest.
        potential_mothers.sort(key=lambda x: x[1])
        mother_cell_i = potential_mothers[0][0]
        mother_cell = self.df.loc[mother_cell_i]

        self.mother_cell_info["potential_mothers"] = potential_mothers

        # Re-run logic with chosen mother cell from above (could be optimized combined).
        for t in self.df["time_num"].unique():

            time_df = self.df.query("time_num == {}".format(t))

            mother_cell_distances = []
            for i, compare_cell in time_df.iterrows():
                mother_cell_distances.append([i, self._calc_same_cell_cost(mother_cell, compare_cell)])

            mother_cell_distances.sort(key=lambda x: x[1])
            closest_cell_index = mother_cell_distances[0][0]
            self.mother_cell_costs.append(mother_cell_distances[0][1])

            self.df.at[closest_cell_index, "is_mother_cell"] = True
            for v in mother_cell_distances:
                self.df.at[v[0], "last_mother_cost"] = v[1]

            mother_cell = self.df.loc[closest_cell_index]

        return

    def _assign_daughter_cell_lineage(self):
        """
        Assigns daughter_cell = True to relevant objects in DataFrame.
        """

        last_daughter_cell = None
        for t in self.df["time_num"].unique():

            # Filter to time_num, separate mother and other cells.
            time_df = self.df.query("time_num == {}".format(t))
            mother_cell = time_df.query("is_mother_cell == 1").iloc[0]
            other_cells = time_df.query("is_mother_cell == 0")

            daughter_cell_costs = []

            # Calc costs for other cells, if potentially a daughter cell, add to daughter_cell_costs
            for i, compare_cell in other_cells.iterrows():
                is_daughter, is_daughter_cost = self._calc_potential_daughter_cost(mother_cell, last_daughter_cell,
                                                                                   compare_cell)
                if is_daughter:
                    daughter_cell_costs.append([i, is_daughter_cost])

            # Select and mark daughter cell with lowest cost.
            if daughter_cell_costs:
                daughter_cell_costs.sort(key=lambda x: x[1])
                last_daughter_cell = self.df.loc[daughter_cell_costs[0][0]]
                self.df.at[daughter_cell_costs[0][0], "is_daughter_cell"] = True
            else:
                last_daughter_cell = None

    def _run_rls(self):
        """
        Runs iterative RLS.
        """

        is_dividing = False
        division_start_time = None
        time_since_last_division = 0
        time_since_current_division = 0
        division_type = None

        for i, sum_area_obj in enumerate(self.sum_area_signal):

            time_num = sum_area_obj["time_num"]
            num_obj = sum_area_obj["obj_count"]
            area = sum_area_obj["area"]

            # ** Division Behavior
            # Start a division Event Due to Obj Change
            if not is_dividing and num_obj == 2:
                is_dividing = True
                division_start_time = time_num
                time_since_last_division = 0
                division_type = "obj"
                continue

            # Stop a division Event Due to Obj Change. Require 4 Time Length for Noise.
            if is_dividing and num_obj == 1 and time_since_current_division >= 4:
                self.num_divisions += 1
                is_dividing = False
                self.division_events.append({"start": division_start_time, "stop": time_num,
                                             "division_num": self.num_divisions, "division_type": division_type,
                                             "area": self.sum_area_signal[i]["area"]})
                time_since_current_division = 0
                continue

            # Stop current/Start new a division Event due to Area Change (Missed Division).
            if is_dividing and i in self.trough_indices and time_since_current_division >= 4:

                # Possible for a single stop condition to trigger here.
                avg_div_area = np.mean([v["area"] for v in self.division_events])
                if (area < avg_div_area*.50 or area > avg_div_area*1.50) and time_num > 150:
                    self.stop_condition = "Div Range"
                    self.t_stop = time_num
                    print("Break Div Range: {}/{}".format(area, avg_div_area), self.trap_num, time_num,
                          self.num_divisions, self.experimental_count)
                    break

                self.num_divisions += 1
                self.division_events.append({"start": division_start_time, "stop": time_num,
                                             "division_num": self.num_divisions, "division_type": division_type,
                                             "area": self.sum_area_signal[i]["area"]})
                division_start_time = time_num
                division_type = "area"
                time_since_last_division = 0
                time_since_current_division = 0

            # Increment Time Since Last Division if Not Dividing & Only Mother Cell, or prolong current division.
            if not is_dividing:
                time_since_last_division += 1
            else:
                time_since_current_division += 1

            # ** Stop Condition Behavior
            # No Cells
            if num_obj == 0 or area == 0:
                self.stop_condition = "No Cells"
                self.t_stop = time_num
                print("Break No Cells", self.trap_num, time_num, self.num_divisions, self.experimental_count)
                break

            # No Divisions
            if time_since_last_division > 10 and self.num_divisions > 2:
                self.stop_condition = "No Calc Divisions"
                self.t_stop = time_num
                print("Break No Div", self.trap_num, time_num, self.num_divisions, self.experimental_count)
                break

            # Flat Signal
            next_area = [v["area"] for v in self.sum_area_signal[i:i + 10]]
            if np.std(next_area) <= 4.5 and time_num > 50:
                self.stop_condition = "No Divisions - Area STD"
                self.t_stop = time_num
                print("Break No Div - Area STD", self.trap_num, time_num, self.num_divisions, self.experimental_count)
                break

            # # No Obj Change 1
            next_obj = [v["obj_count"] for v in self.sum_area_signal[i:i + 10]]
            if next_obj[i:i + 10].count(1) == 10 and self.num_divisions >= 2:
                self.stop_condition = "No Divisions - Num Obj 1"
                self.t_stop = time_num
                print("Break No Divisions - Num Obj 1", self.trap_num, time_num, self.num_divisions,
                      self.experimental_count)
                break

            # # No Obj Change 2
            next_obj = [v["obj_count"] for v in self.sum_area_signal[i:i + 20]]
            if next_obj[i:i + 20].count(2) == 20 and self.num_divisions >= 2:
                self.stop_condition = "No Divisions - Num Obj 2"
                self.t_stop = time_num
                print("Break No Divisions - Num Obj 2", self.trap_num, time_num, self.num_divisions,
                      self.experimental_count)
                break

            # Area Far From Division Stop
            # # # Mother Cell Cost High
            # avg_mother_cell_cost = np.mean(self.mother_cell_costs[:i])
            # if self.mother_cell_costs[i] > avg_mother_cell_cost*1.5 and self.num_divisions > 2 and self.mother_cell_costs[i] > 4.0:
            #     self.stop_condition = "Lost Mother"
            #     print(avg_mother_cell_cost, self.mother_cell_costs[i], self.mother_cell_costs[:i])
            #     self.t_stop = time_num
            #     print("Lost Mother", self.trap_num, time_num, self.num_divisions,
            #           self.experimental_count)
            #     break

    def results(self):
        """
        Doc Doc Doc
        """

        return {"t_stop": self.t_stop, "stop_condition": self.stop_condition,
                "pred_div": self.num_divisions, "trap_num": self.trap_num,
                "start_obj": self.start_num_obj, "exp_div": self.experimental_count}

    def plot_sum_area_signal(self):
        """
        Doc Doc Doc
        """

        fig = go.Figure()

        fig.layout.title["text"] = "TrapNum:{} TStop:{} Division Events".format(self.trap_num, self.t_stop)

        area = [v["area"] for v in self.sum_area_signal]
        time_num = [v["time_num"] for v in self.sum_area_signal]
        obj_count = [v["obj_count"] for v in self.sum_area_signal]

        division_stops = [v["stop"] for v in self.division_events]
        division_starts = [v["start"] for v in self.division_events]

        start_xy_tuple = []
        for t in division_starts:
            i = t-1
            start_xy_tuple.append([t, area[i]])

        stop_xy_tuple = []
        for t in division_stops:
            i = t-1
            stop_xy_tuple.append([t, area[i]])

        fig.add_trace(go.Scatter(x=time_num, y=area, mode="lines+markers", name="sum_area_signal"))
        fig.add_trace(go.Scatter(x=[v[0] for v in stop_xy_tuple], y=[v[1] for v in stop_xy_tuple], mode="markers", name="division_stop"))
        fig.add_trace(go.Scatter(x=[v[0] for v in start_xy_tuple], y=[v[1] for v in start_xy_tuple], mode="markers", name="division_start"))
        fig.add_trace(go.Scatter(x=time_num, y=[1.0]*len(time_num), mode="text", text=obj_count,
                                 name="obj_count"))

        fig.show()

    def support_plot_mother_cell_lineage(self):

        print("Support Plot Mother Cell Lineage")
        fig = go.Figure()

        for v in self.mother_cell_info["potential_mothers"]:
            cost = v[1]
            cell_obj = self.raw_df.loc[v[0]]
            fig.add_trace(go.Scatter(x=[cell_obj["obj_X"]], y=[cell_obj["obj_Y"]], mode="markers+text",
                                     name="potential_mother", text=[cost]))

        mother_cells = self.df.loc[(self.df["is_mother_cell"] == 1)]
        mother_cell_x, mother_cell_y = list(mother_cells["obj_X"])[:150], list(mother_cells["obj_Y"])[:150]

        fig.layout.title["text"] = "TrapNum:{} Mother Cell Determination".format(self.trap_num)
        fig.add_trace(go.Scatter(x=mother_cell_x, y=mother_cell_y, mode="markers", name="mother_cell_lineage"))

        fig.update_layout(
            xaxis_title="obj_X",
            yaxis_title="obj_Y",
        )
        fig.update_xaxes(range=[0, 50])
        fig.update_yaxes(range=[0, 50])

        fig.show()

    def support_plot_daughter_cell_lineage(self):

        print("Support Plot Daughter Cell Lineage")
        t_stop = self.t_stop-1
        fig = go.Figure()

        mother_cells = self.df.loc[(self.df["is_mother_cell"] == 1)]
        daughter_cells = self.df.loc[(self.df["is_daughter_cell"] == 1)]

        all_cell_df = self.raw_df.query("time_num < {}".format(t_stop))

        all_cell_x, all_cell_y = list(all_cell_df["obj_X"]), list(all_cell_df["obj_Y"])
        mother_cell_x, mother_cell_y = list(mother_cells["obj_X"])[:t_stop], list(mother_cells["obj_Y"])[:t_stop]
        daughter_cell_x, daughter_cell_y = list(daughter_cells["obj_X"])[:t_stop], list(daughter_cells["obj_Y"])[:t_stop]

        fig.layout.title["text"] = "TrapNum:{} Cell Lineages".format(self.trap_num)
        fig.add_trace(go.Scatter(x=all_cell_x, y=all_cell_y, mode="markers", name="all_cells"))
        fig.add_trace(go.Scatter(x=mother_cell_x, y=mother_cell_y, mode="markers", name="mother_cell_lineage"))
        fig.add_trace(go.Scatter(x=daughter_cell_x, y=daughter_cell_y, mode="markers", name="daughter_cell_lineage"))

        fig.update_layout(
            xaxis_title="obj_X",
            yaxis_title="obj_Y",
        )
        fig.update_xaxes(range=[0, 50])
        fig.update_yaxes(range=[0, 50])

        fig.show()

    def support_plot_sum_area_signal(self):

        print("Support SumArea Signal")

        mother_daughter = self.df.loc[(self.df['is_mother_cell'] == 1) | (self.df["is_daughter_cell"] == 1)]
        mother_only = self.df.loc[(self.df['is_mother_cell'] == 1)]
        daughter_only = self.df.loc[(self.df["is_daughter_cell"] == 1)]
        all_cell = self.raw_df

        mother_daughter_signal = []
        mother_only_signal = []
        daughter_only_signal = []
        all_cell_signal = []

        time_num = list(self.df["time_num"].unique())

        for t in self.df["time_num"].unique():
            mother_daughter_df = mother_daughter.query("time_num == {}".format(t))
            sum_area = sum(mother_daughter_df["area"])
            mother_daughter_signal.append(sum_area)

            mother_only_df = mother_only.query("time_num == {}".format(t))
            sum_area = sum(mother_only_df["area"])
            mother_only_signal.append(sum_area)

            daughter_only_df = daughter_only.query("time_num == {}".format(t))
            sum_area = sum(daughter_only_df["area"])
            daughter_only_signal.append(sum_area)

            all_cell_df = all_cell.query("time_num == {}".format(t))
            sum_area = sum(all_cell_df["area"])
            all_cell_signal.append(sum_area)

        fig = go.Figure()

        fig.layout.title["text"] = "TrapNum:{} Cell Signals".format(self.trap_num)
        fig.add_trace(go.Scatter(x=time_num, y=all_cell_signal, mode="lines", name="all"))
        fig.add_trace(go.Scatter(x=time_num, y=mother_only_signal, mode="lines", name="mother"))
        fig.add_trace(go.Scatter(x=time_num, y=daughter_only_signal, mode="lines", name="daughter"))
        fig.add_trace(go.Scatter(x=time_num, y=mother_daughter_signal, mode="lines", name="mother+daughter"))

        fig.update_layout(
            xaxis_title="time_num",
            yaxis_title="sum_area",
        )

        fig.show()

    def plot_animation_x_y(self):
        """
        Doc Doc Doc
        """

        cell_coordinates = []

        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {}".format(t))

            cell_c_temp = []
            has_daughter = False
            for i, row in time_df.iterrows():
                if not row["is_mother_cell"]:
                    has_daughter = True
                cell_c_temp.append({"x": row["obj_X"],
                                    "y": row["obj_Y"],
                                    "area": row["area"],
                                    "time": row["time_num"],
                                    "mother_cell": row["is_mother_cell"],
                                    "lcm": row["last_mother_cost"]})
            cell_c_temp.sort(key=lambda x: x["area"], reverse=True)
            for v in cell_c_temp:
                cell_coordinates.append(v)

            # Hack-fix for Plotly - Won't show other cells if single mother cell start
            if not has_daughter:
                cell_coordinates.append({"x": 0,
                                         "y": 0,
                                         "area": 0,
                                         "time": t,
                                         "mother_cell": False,
                                         "lcm": 15.0})

        df = pd.DataFrame(cell_coordinates)

        fig = px.scatter(df, x="x", y="y", color="mother_cell", title="Trap:{} X/Y Over Time".format(self.trap_num),
                         animation_frame="time", range_x=[0, 60], range_y=[0, 60], size="area",
                         color_continuous_scale=[(0, "cyan"), (1, "red")])

        fig.show()
