import pandas as pd
import sys
import os
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
        self.time_num_obj = []
        self.branch_nodes = []
        self._on_init()

    def _on_init(self):

        starting_num_objs = self.df.query("time_num == 1")["total_objs"].tolist()[0]
        if starting_num_objs != 1:
            raise ValueError("Multiple or No Objects at T1 - Not Supported")

        self._make_graph()

    def _process_time_step(self, step_info):
        """
        Doc Doc Doc
        """

        pass

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

        avg_cell_area = sum([a/c for a, c in zip(self.time_sum_area, self.time_num_obj)]) / len(self.time_sum_area)

        last_mc_node_name = None
        branch_active = False
        branch_start_area = None
        last_area = self.time_sum_area[0]

        num_branches = 0

        for i, t in enumerate(self.df["time_num"].unique()):

            mc_node_name = "{}.1".format(t)

            current_area = self.time_sum_area[i]
            next_area = self.time_sum_area[i+1] if t != self.t_stop else self.time_sum_area[i]

            if not branch_active:
                if next_area - current_area >= 15:
                    print("Branch Starting: ", t)
                    branch_active = True
                    num_branches += 1
            else:
                dc_node_name = "{}.2".format(t)
                if current_area - next_area >= 15:
                    print("Branch Ending: ", t)
                    branch_active = False

            if not branch_active:
                self.graph[mc_node_name] = []
                if last_mc_node_name:
                    self.graph[mc_node_name].append(last_mc_node_name)
                    self.graph[last_mc_node_name].append(mc_node_name)
                last_mc_node_name = mc_node_name

            if self.time_num_obj[i] == 0:
                break

            if next_area - current_area > 100:
                break

        print(self.graph)
        print(num_branches)
        print(self.time_sum_area)
        print(self.time_num_obj)



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

