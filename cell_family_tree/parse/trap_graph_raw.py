import pandas as pd
import numpy as np
import sys
import os
from scipy.signal import argrelextrema
from .helpers import write_csv

"""
Doc Doc Doc
"""


class TrapGraphRaw:

    def __init__(self, df, file_name=None):
        self.df = df
        self.file_name = file_name
        self.trap_num = None
        self.graph = {}
        self.t_stop = self.df["time_num"].max()
        self.time_sum_area = []
        self.time_sum_area_minima = []
        self.time_sum_area_maxima = []
        self.time_num_obj = []
        self.branch_nodes = []
        self._on_init()

    def _on_init(self):

        starting_num_objs = self.df.query("time_num == 1")["total_objs"].tolist()[0]
        if starting_num_objs != 1:
            raise ValueError("Multiple or No Objects at T1 - Not supported at the moment")

        self._make_graph()

    def _next_extrema_helper(self, i, return_minima=True):

        if return_minima:
            next_minima_index = self.t_stop-1
            for i1, v in enumerate(self.time_sum_area_minima):
                if v == 1 and i1 > i:
                    next_minima_index = i1
                    break

            return self.time_sum_area[next_minima_index], self.time_num_obj[next_minima_index], next_minima_index+1

        next_maxima_index = self.t_stop-1
        for i1, v in enumerate(self.time_sum_area_maxima):
            if v == 1 and i1 > i:
                next_maxima_index = i1
                break

        return self.time_sum_area[next_maxima_index], self.time_num_obj[next_maxima_index], next_maxima_index+1

    def _make_graph(self):
        """
        Doc Doc Doc
        """

        # Pre-Populate SumArea & TimeNumObjs
        for t in self.df["time_num"].unique():

            time_df = self.df.query("time_num == {}".format(t))
            total_obj = time_df["total_objs"].unique()[0]
            sum_area = sum(time_df["area"])
            self.time_num_obj.append(total_obj)
            self.time_sum_area.append(sum_area)

        # Determine Changes in Sum Area From 1 to 2 Objs. Used for same_cell_noise below.
        observed_area_division_increments = []
        for i, v in enumerate(self.time_num_obj[:-1]):
            if v == 1 and self.time_num_obj[i+1] == 2:
                curr_area = self.time_sum_area[i]
                next_area = self.time_sum_area[i+1]
                observed_area_division_increments.append(next_area - curr_area)

        # Determine Sum Area Local Minima. Equate to time_num by assigning 1 to existence of local minima, 0 to not.
        sum_area_local_minima = list(argrelextrema(np.array(self.time_sum_area), np.less)[0])
        for i in range(len(self.time_sum_area)):
            if i in sum_area_local_minima:
                self.time_sum_area_minima.append(1)
            else:
                self.time_sum_area_minima.append(0)

        # Determine Sum Area Local Maxima. Equate to time_num by assigning 1 to existence of local maxima, 0 to not.
        sum_area_local_maxima = list(argrelextrema(np.array(self.time_sum_area), np.greater)[0])
        for i in range(len(self.time_sum_area)):
            if i in sum_area_local_maxima:
                self.time_sum_area_maxima.append(1)
            else:
                self.time_sum_area_maxima.append(0)

        # Parameters
        same_cell_noise = np.min(observed_area_division_increments)  # Threshold to ignore a local minima.

        # Track State
        is_dividing = False     # Mother cell in process of dividing cannot bud into another cell. Branching Locked.
        will_divide = False     # Mother cell division detected beginning next time step.
        last_mc_node_name = None
        last_sum_area = self.time_sum_area[0]
        num_divisions = 0
        clean_divisions = 0

        # RLS Logic
        for i, t in enumerate(self.df["time_num"].unique()):

            # Early Stop - No Cells Detected
            if self.time_num_obj[i] == 0:
                break

            mc_node_name = "{}.1".format(t)

            current_area = self.time_sum_area[i]
            current_obj_count = self.time_num_obj[i]
            next_area = self.time_sum_area[i+1] if t != self.t_stop else self.time_sum_area[i]
            at_local_minima = self.time_sum_area_minima[i]

            if at_local_minima:  # Reach Local Minima means we MIGHT have a branch start NEXT step

                nlmax_area, nlmax_obj_count, nlmax_time_num = self._next_extrema_helper(i, return_minima=False)
                nlmin_area, nlmin_obj_count, nlmin_time_num = self._next_extrema_helper(i, return_minima=True)

                print("*")
                # Clean Division
                if current_obj_count == 1 and nlmin_obj_count == 1 and nlmax_obj_count == 2:
                    print("Clean Division")
                    print(nlmax_time_num)
                    clean_divisions += 1

                print("At Local Minima!")
                print(current_area, t, self.time_num_obj[i])
                print(nlmax_area, nlmax_time_num, nlmax_obj_count)
                print(nlmin_area, nlmin_time_num, nlmin_obj_count)

                # sys.exit()

        print("Clean Divisions:{}".format(clean_divisions))






       #  sys.exit()

        # Debug
        # for i in range(len(self.time_sum_area)):
        #     print(i+1, self.time_num_obj[i], self.time_sum_area[i], self.time_sum_area_minima[i], self.time_sum_area_maxima[i])



        # avg_cell_area = sum([a/c for a, c in zip(self.time_sum_area, self.time_num_obj)]) / len(self.time_sum_area)
        #
        # last_mc_node_name = None
        # branch_active = False
        # branch_start_area = None
        # last_area = self.time_sum_area[0]
        #
        # num_branches = 0
        #
        # cats = argrelextrema(np.array(self.time_sum_area), np.less)
        #
        # print(self.time_sum_area)
        # print(cats)

        # for i, t in enumerate(self.df["time_num"].unique()):
        #
        #     mc_node_name = "{}.1".format(t)
        #
        #     current_area = self.time_sum_area[i]
        #     next_area = self.time_sum_area[i+1] if t != self.t_stop else self.time_sum_area[i]
        #
        #     if not branch_active:
        #         if next_area - current_area >= 15:
        #             print("Branch Starting: ", t)
        #             branch_active = True
        #             num_branches += 1
        #     else:
        #         dc_node_name = "{}.2".format(t)
        #         if current_area - next_area >= 15:
        #             print("Branch Ending: ", t)
        #             branch_active = False
        #
        #     if not branch_active:
        #         self.graph[mc_node_name] = []
        #         if last_mc_node_name:
        #             self.graph[mc_node_name].append(last_mc_node_name)
        #             self.graph[last_mc_node_name].append(mc_node_name)
        #         last_mc_node_name = mc_node_name
        #
        #     if self.time_num_obj[i] == 0:
        #         break
        #
        #     if next_area - current_area > 100:
        #         break
        #
        # print(self.graph)
        # print(num_branches)
        # print(self.time_sum_area)
        # print(self.time_num_obj)



    def write_cytoscape_network_csv(self):

        if not self.file_name:
            raise ValueError("Must Supply FileName to Generate CytoScape Network CSV")

        if len(self.root_nodes) != 1:
            raise ValueError("Currently Only 1 Root Node Supported")

        if not os.path.exists("cytoscape"):
            os.mkdir("cytoscape")

        # print(self.graph)

        res = [["source", "target", "interaction", "directed", "symbol", "value"]]
        has_parsed = []
        for source_node in self.graph:
            for target_node in self.graph[source_node]:
                if target_node in has_parsed:
                    continue
                symbol = source_node
                value = 1.0
                directed = True
                interaction = "pp"
                if source_node in self.root_nodes:
                    directed = False

                res.append([source_node, target_node, interaction, directed, symbol, value])
                has_parsed.append(source_node)

        write_csv("cytoscape/{}_TrapNum_{}_cytoscape_network.csv".format(self.file_name.replace(".csv", ""), self.trap_num), res)

