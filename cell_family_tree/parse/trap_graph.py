import pandas as pd
import math
import sys
import json
pd.options.mode.chained_assignment = None   # For predID assignment on query


"""
Doc Doc Doc
"""


class TrapDataParse:

    def __init__(self, file_name):
        self.file_name = file_name
        self.df = pd.read_csv("data/{}".format(self.file_name))

    def get_single_trap(self, trap_num, t_stop=None):
        """
        Returns a new dataframe limited to a single trap_num with optional argument for an end time.
        """

        query = ""

        if trap_num:
            query += "trap_num == {}".format(trap_num)

        if t_stop:
            query += " and time_num <= {}".format(t_stop)

        if query[0] == " ":
            query = query[5:]

        df = self.df.query(query)

        # Assign PredID Nan's
        next_pred_id = 1
        for i, row in df.iterrows():
            if math.isnan(row["predecessorID"]):
                df.loc[i, "predecessorID"] = next_pred_id
                next_pred_id += 1

        # Convert to Ints (PredID initializes as floats due to NaN)
        df = df.applymap(int)

        # Remove Image Num
        try:
            del df["image_num"]
        except KeyError:
            pass

        df.to_csv("recent/recent_query.csv", index=False)

        return df

    @staticmethod
    def _establish_root_nodes(df, graph_dict, graph_helper):
        """
        :param df: intermediate used in to_graph_info()
        :return:
        """

        start_time = df["time_num"].unique()[0]
        start_time_df = df.query("time_num == {}".format(start_time))
        len_time_step = len(start_time_df.index)
        graph_dict["time_num_obj"].append([start_time, len_time_step])
        graph_helper["last_num_obj"] = len_time_step

        for i, node in enumerate(start_time_df.to_dict('records')):

            pred_id = node["predecessorID"]
            time_num = node["time_num"]
            node_name = "{}.{}".format(time_num, pred_id)
            graph_dict["graph"][node_name] = []
            graph_dict["root_nodes"].append(node_name)
            graph_helper["pred_id_last_node"][pred_id] = node_name
            graph_dict["root_pred_ids"].append(pred_id)

    @staticmethod
    def _handle_step_info(step_info, graph_dict, graph_helper):
        """
        :param step_info:
        :param graph_dict:
        :param graph_helper:
        :return:
        """

        # Get Pred ID's in Current Time Step
        active_pred_ids = [v["predecessorID"] for v in step_info]

        # Get Pred ID's in next Time Step (Branches will be these) Sort.
        assign_pred_ids = list(set(graph_helper["next_pred_ids"]) - set(active_pred_ids))
        assign_pred_ids.sort(reverse=True)

        # Check to see if the root_pred_ids are active in this step, if they are not, we assume the mother cell has died
        root_pred_ids = graph_dict["root_pred_ids"]

        # Sort Step Info, Assignment will try to associate the lower current pred_id to the next lowest etc.
        step_info.sort(key=lambda x: x["predecessorID"])
        isolated_pred_id = None
        parsed_steps = []
        for step in step_info:
            step_arr = [step[k] for k in step]
            if step_arr in parsed_steps:
                branch_node_name = "{}.{}".format(step["time_num"], step["predecessorID"])
                graph_dict["branch_nodes"].append(branch_node_name)

                try:
                    next_pred_id = assign_pred_ids.pop()    # Pull from sorted assign_pred_ids, de-que
                except IndexError:
                    if not isolated_pred_id:
                        try:
                            isolated_pred_id = max(graph_helper["next_pred_ids"]) + 1
                        except ValueError:
                            isolated_pred_id = step["predecessorID"] + 1
                    else:
                        isolated_pred_id += 1

                    next_pred_id = isolated_pred_id
                    print("POP ERROR")
                    print(step_info)
                    print(step)
                    print(active_pred_ids)
                    print(graph_helper["next_pred_ids"])
                    # sys.exit()

                print("GOT BRANCH:", branch_node_name, step_arr, "NextPredID:{}".format(next_pred_id))
                step["predecessorID"] = next_pred_id
                graph_helper["pred_id_last_node"][step["predecessorID"]] = branch_node_name
                active_pred_ids += [next_pred_id]

            parsed_steps.append(step_arr)

        # Clear Non-Active Pred Id's
        # for k in graph_helper["pred_id_last_node"]:
        #     if k not in active_pred_ids:
        #         graph_helper["pred_id_last_node"][k] = None

        return step_info

    def to_graph_info(self, trap_num, t_stop):
        """
        Attempts to parse a yolo.csv into a tree data structure that can then be used for further analysis.
        Good amount of in-line doc to cover how its done.
        """

        # graph_dict is returned
        graph_dict = dict()
        graph_dict["file_name"] = self.file_path.rsplit("/", 1)[-1]
        graph_dict["trap_num"] = trap_num
        graph_dict["t_stop"] = t_stop
        graph_dict["graph"] = {}
        graph_dict["check_ts"] = []
        graph_dict["time_num_obj"] = []
        graph_dict["root_nodes"] = []
        graph_dict["branch_nodes"] = []
        graph_dict["root_pred_ids"] = []

        # graph_helper is used in parsing
        graph_helper = dict()
        graph_helper["pred_id_last_node"] = {}

        # Return a copy of the source data filtered to specific trap number and t_stop.
        df = self.query(trap_num=trap_num, t_start=0, t_stop=t_stop, write_csv=True)

        # Establish Root Nodes. Assumes sorted/in order.
        self._establish_root_nodes(df, graph_dict, graph_helper)

        # We are interested in changes that occur between time steps. So will create sub-df's using those times.
        # Start at 2nd index because _establish_root_nodes() handles above
        for t in df["time_num"].unique()[1:]:

            # Run another filter of our initial filtered df from above on loop time step.
            time_df = df.query("time_num == {}".format(t))
            next_time_df = df.query("time_num == {}".format(t+1))

            # The number of data points per time-step may dictate behavior.
            len_time_step = len(time_df.index)
            len_next_time_step = len(next_time_df.index)
            next_time_step_pred_ids = list(next_time_df["predecessorID"].unique())
            graph_helper["current_num_obj"] = len_time_step
            graph_helper["next_num_obj"] = len_next_time_step
            graph_helper["next_pred_ids"] = next_time_step_pred_ids

            # Tracks number of obj seen per time step. Used in debug/display purposes.
            graph_dict["time_num_obj"].append([t, len_time_step])

            step_info = time_df.to_dict('records')
            step_info = self._handle_step_info(step_info, graph_dict, graph_helper)

            graph_helper["last_num_obj"] = len(step_info)

            for node in step_info:

                pred_id = node["predecessorID"]
                time_num = node["time_num"]
                node_name = "{}.{}".format(time_num, pred_id)

                graph_dict["graph"][node_name] = []
                pred_id_last_node_name = graph_helper["pred_id_last_node"][pred_id]

                graph_dict["graph"][node_name].append(pred_id_last_node_name)
                try:
                    graph_dict["graph"][pred_id_last_node_name].append(node_name)
                except KeyError:
                    print("Error Pred_Id_Last_Node_Name")
                    print(node)
                    print(pred_id_last_node_name)
                    print(node_name)
                    print(graph_helper)
                    sys.exit()

                graph_helper["pred_id_last_node"][pred_id] = node_name

        for k in graph_dict["graph"]:
            vals = [float(v) for v in graph_dict["graph"][k]]
            vals = sorted(vals)
            vals = [str(round(v, 1)) for v in vals]
            graph_dict["graph"][k] = vals

        return graph_dict, df

    def to_root_branch_info(self, trap_num, t_stop):
        """
        Determines the numbers of branches that occur off of the root nodes by finding where they branch (indicated by
        a time_step in which their pred_id shows up twice).
        """

        # graph_dict is returned
        root_branch_dict = dict()
        root_branch_dict["trap_num"] = trap_num
        root_branch_dict["t_stop"] = t_stop
        root_branch_dict["graph"] = {}
        root_branch_dict["root_nodes"] = []
        root_branch_dict["root_branches"] = {}
        root_branch_dict["time_num_obj"] = []

        # graph_helper is used in parsing (Not used atm in this function)
        graph_helper = dict()
        graph_helper["pred_id_last_node"] = {}

        # Return a copy of the source data filtered to specific trap number and t_stop.
        df = self.query(trap_num=trap_num, t_start=0, t_stop=t_stop, write_csv=True)

        # Establish Root Nodes. Assumes sorted/in order.
        self._establish_root_nodes(df, root_branch_dict, graph_helper)

        # Kinda hacky, but in order to share some code w/ self.to_graph_info, delete unused keys
        del root_branch_dict["graph"]
        del root_branch_dict["time_num_obj"]

        # Assign keys to root_branches (keys are root pred_ids, values will be time_num where they branch)
        for root_node in root_branch_dict["root_nodes"]:
            root_pred_id = root_node.split(".", 1)[-1]
            root_branch_dict["root_branches"][root_pred_id] = []

        # print("To Root Branch Info")
        # print(root_branch_dict)

        for t in df["time_num"].unique()[1:]:

            # Run another filter of our initial filtered df from above on loop time step.
            time_df = df.query("time_num == {}".format(t))

            step_info = time_df.to_dict('records')
            active_pred_ids = [v["predecessorID"] for v in step_info]

            # Iterate through root_pred_ids:
            for root_pred_id in root_branch_dict["root_branches"]:

                # Check how many times it occurs in active_pred_ids:
                num_occur = active_pred_ids.count(int(root_pred_id))

                # 0 means didn't occur, 1 means continuation, 2 or more is a branch(s), subtract 1 and check remaining
                num_occur -= 1

                # Add time_nums for when the branch occurred
                if num_occur >= 1:
                    for i in range(num_occur):
                        root_branch_dict["root_branches"][root_pred_id].append(t)

        return root_branch_dict
