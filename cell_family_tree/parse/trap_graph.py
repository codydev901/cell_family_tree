import pandas as pd
import sys
import os
from .helpers import write_csv

"""
Doc Doc Doc
"""


class TrapGraph:

    def __init__(self, df, run_graph=True, file_name=None):
        self.df = df
        self.run_graph = run_graph
        self.file_name = file_name
        self.trap_num = None
        self.graph = {}
        self.root_nodes = []
        self.root_pred_ids = []
        self.branch_nodes = []
        self.time_num_obj = []
        self.root_endpoints = {}
        self.graph_helper = {}
        self._on_init()

    def _on_init(self):

        self.graph_helper["pred_id_last_node"] = {}  # For each predID, tracks the last node of that id.
        self.graph_helper["current_num_obj"] = 0     # total_objs for current time_step
        self.graph_helper["last_num_obj"] = 0        # total_objs for last time_step
        self.graph_helper["next_num_obj"] = 0        # total_objs for next time_step
        self.graph_helper["next_pred_ids"] = []      # predID's present in next time_step

        self._establish_root_nodes()
        self._set_root_endpoints()

        if self.run_graph:
            self._make_graph()

            # Some post-processing on self.graph to put edge nodes in numerical order.
            for k in self.graph:
                vals = [float(v) for v in self.graph[k]]
                vals = sorted(vals)
                vals = [str(round(v, 1)) for v in vals]
                self.graph[k] = vals

    def _establish_root_nodes(self):
        """
        Doc Doc Doc
        """

        start_time = self.df["time_num"].unique()[0]
        start_time_df = self.df.query("time_num == {}".format(start_time))
        len_time_step = len(start_time_df.index)
        self.time_num_obj.append([start_time, len_time_step])
        self.graph_helper["last_num_obj"] = len_time_step

        for i, node in enumerate(start_time_df.to_dict('records')):

            pred_id = node["predecessorID"]
            time_num = node["time_num"]
            node_name = "{}.{}".format(time_num, pred_id)
            self.graph[node_name] = []
            self.root_nodes.append(node_name)
            self.root_pred_ids.append(pred_id)
            self.graph_helper["pred_id_last_node"][pred_id] = node_name
            self.trap_num = node["trap_num"]

    def _set_root_endpoints(self):
        """
        Doc Doc Doc
        """

        self.root_endpoints = {k: 0 for k in self.root_pred_ids}

        remaining_root_pred_ids = self.root_pred_ids.copy()

        for t in self.df["time_num"].unique()[1:]:

            if not remaining_root_pred_ids:
                return

            time_df = self.df.query("time_num == {}".format(t))
            step_info = time_df.to_dict('records')
            active_pred_ids = [v["predecessorID"] for v in step_info]

            for root_pred_id in self.root_pred_ids:
                if root_pred_id not in remaining_root_pred_ids:
                    continue
                if root_pred_id not in active_pred_ids:
                    self.root_endpoints[root_pred_id] = max(t - 1, 1)
                    remaining_root_pred_ids.remove(root_pred_id)

        for root_endpoint in self.root_endpoints:
            if self.root_endpoints[root_endpoint] == 0:
                self.root_endpoints[root_endpoint] = self.df["time_num"].max()

    def _process_time_step(self, step_info):
        """
        Doc Doc Doc
        """

        # print(step_info)

        # Get Pred ID's in Current Time Step
        active_pred_ids = [v["predecessorID"] for v in step_info]

        # Get Pred ID's in next Time Step (Branches will be these) Sort.
        assign_pred_ids = list(set(self.graph_helper["next_pred_ids"]) - set(active_pred_ids))
        assign_pred_ids.sort(reverse=True)

        # Sort Step Info, Assignment will try to associate the lower current pred_id to the next lowest etc.
        step_info.sort(key=lambda x: x["predecessorID"])
        isolated_pred_id = None
        parsed_steps = []
        for step in step_info:
            step_arr = [step[k] for k in step]
            if step_arr in parsed_steps:
                branch_node_name = "{}.{}".format(step["time_num"], step["predecessorID"])
                self.branch_nodes.append(branch_node_name)
                try:
                    next_pred_id = assign_pred_ids.pop()    # Pull from sorted assign_pred_ids, de-que
                except IndexError:
                    if not isolated_pred_id:
                        try:
                            isolated_pred_id = max(self.graph_helper["next_pred_ids"]) + 1
                            print("POP ERROR - Isolated New Max:", step_arr, isolated_pred_id)
                        except ValueError:
                            isolated_pred_id = step["predecessorID"] + 1
                            print("POP ERROR - Isolated New +1", step_arr, isolated_pred_id)
                    else:
                        isolated_pred_id += 1
                        print("POP ERROR - Isolated Existing", step_arr, isolated_pred_id)
                    next_pred_id = isolated_pred_id

                # print("GOT BRANCH:", branch_node_name, step_arr, "NextPredID:{}".format(next_pred_id))
                step["predecessorID"] = next_pred_id
                self.graph_helper["pred_id_last_node"][step["predecessorID"]] = branch_node_name
                active_pred_ids += [next_pred_id]

            parsed_steps.append(step_arr)

        return step_info

    def _make_graph(self):
        """
        Doc Doc Doc
        """

        # We are interested in changes that occur between time steps. So will create sub-df's using those times.
        # Start at 2nd index because _establish_root_nodes() handles above
        for t in self.df["time_num"].unique()[1:]:

            # Run another filter of our initial filtered df from above on loop time step.
            time_df = self.df.query("time_num == {}".format(t))
            next_time_df = self.df.query("time_num == {}".format(t+1))

            # The number of data points per time-step may dictate behavior.
            len_time_step = len(time_df.index)
            len_next_time_step = len(next_time_df.index)
            next_time_step_pred_ids = list(next_time_df["predecessorID"].unique())
            self.graph_helper["current_num_obj"] = len_time_step
            self.graph_helper["next_num_obj"] = len_next_time_step
            self.graph_helper["next_pred_ids"] = next_time_step_pred_ids

            # Tracks number of obj seen per time step. Used in debug/display purposes.
            self.time_num_obj.append([t, len_time_step])

            step_info = time_df.to_dict('records')

            # Check for existence of root/mother cell, if not present, return since main branch has ended.
            active_pred_ids = [v["predecessorID"] for v in step_info]
            for root_pred_id in self.root_pred_ids:
                if root_pred_id not in active_pred_ids:
                    print("Root:{} absent in step:{}".format(root_pred_id, step_info))
                    return

            step_info = self._process_time_step(step_info)

            self.graph_helper["last_num_obj"] = len(step_info)

            for node in step_info:

                pred_id = node["predecessorID"]
                time_num = node["time_num"]
                node_name = "{}.{}".format(time_num, pred_id)

                self.graph[node_name] = []
                try:
                    pred_id_last_node_name = self.graph_helper["pred_id_last_node"][pred_id]
                except KeyError:
                    print("Error Pred_Id_Last_Node_Name 1, Setting Isolated Node:{}".format(node_name))
                    self.graph_helper["pred_id_last_node"][pred_id] = node_name
                    continue
                    # print(pred_id)
                    # print(step_info)
                    # print(self.graph_helper)
                    # print(node_name)
                    # sys.exit()

                self.graph[node_name].append(pred_id_last_node_name)
                try:
                    self.graph[pred_id_last_node_name].append(node_name)
                except KeyError:
                    print("Error Pred_Id_Last_Node_Name 2")
                    print(node)
                    print(pred_id_last_node_name)
                    print(node_name)
                    print(self.graph_helper)
                    sys.exit()

                self.graph_helper["pred_id_last_node"][pred_id] = node_name

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

    def get_divisions_from_obj_count(self):
        """
        Separate from the graph. Attempts to determine branching(life-cycle) behavior through change in obj count.
        """

        print("Get Obj Count Info")

        time_num_objs_lu = {}

        for i, row in self.df.iterrows():

            time_num = row["time_num"]
            num_objs = row["total_objs"]

            time_num_objs_lu[time_num] = num_objs

        cell_divisions = []
        break_time_num = None
        for time_num in time_num_objs_lu:

            if time_num == 1:
                continue

            if time_num == len(time_num_objs_lu):
                continue

            last_num_objs = time_num_objs_lu[time_num - 1]
            curr_num_objs = time_num_objs_lu[time_num]
            next_num_objs = time_num_objs_lu[time_num + 1]

            # Stop Criteria
            if curr_num_objs >= 5 and next_num_objs >= 5:
                break_time_num = time_num
                break

            # Detect a Cell Division
            if curr_num_objs > last_num_objs:       # Increase over last step means new division
                if next_num_objs >= curr_num_objs:  # Check that it persists in next step (not an abnormality)
                    cell_divisions.append([time_num, curr_num_objs - last_num_objs])

            # print(last_num_objs, curr_num_objs, next_num_objs)

        if not break_time_num:
            break_time_num = max(list(time_num_objs_lu.keys()))

        num_branches = sum([v[1] for v in cell_divisions])
        res = {"cell_divisions": cell_divisions, "break_time_num": break_time_num, "num_branches": num_branches}

        return res



