import pandas as pd
import math
import os
from .helpers import write_csv
pd.options.mode.chained_assignment = None   # For predID assignment on query


"""
First parsing step. Concerned with the data files as a whole.
"""


class TrapData:

    def __init__(self, file_name):
        self.file_name = file_name
        self.df = pd.read_csv("data/{}".format(self.file_name))
        self.traps = list(self.df["trap_num"].unique())
        self.data_info = []

    def set_data_info(self, do_write=False):
        """
        Doc Doc Doc
        """

        print("TrapData:{} Setting Data Info...".format(self.file_name))

        data_info = [["trap_num", "time_max", "root_cell_count", "total_cell_count", "unique_pred_ids"]]
        all_pred_ids = []
        for trap_num in self.traps:
            trap_df = self.get_single_trap_df(trap_num)
            time_min, time_max = trap_df["time_num"].min(), trap_df["time_num"].max()
            root_cell_count = trap_df.query("time_num == {}".format(time_min))["total_objs"].unique()[0]
            total_cell_count = len(trap_df[trap_df["total_objs"] != 0].index)
            pred_ids = list(trap_df["predecessorID"].unique())
            pred_ids.sort()
            if 0 not in pred_ids:   # Represents a row with 0 cells, not present in all traps
                pred_ids = [0] + pred_ids
            pred_id_count = [len(trap_df[trap_df["predecessorID"] == p]) for p in pred_ids]
            if len(pred_ids) > len(all_pred_ids):
                all_pred_ids = pred_ids.copy()
            data_info.append([trap_num, time_max, root_cell_count, total_cell_count, len(pred_ids) - 1] + pred_id_count)

        data_info[0] += ["predId:{} Count".format(v) for v in all_pred_ids]
        data_info[0][5] = "empty_count"

        self.data_info = data_info

        if do_write:

            write_csv("reports/{}_TrapDataMetaAnalysis.csv".format(self.file_name.replace(".csv", "")), self.data_info)

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

        # Assign PredID NaN's to Roots
        next_pred_id = 1
        for i, row in df.iterrows():
            if row["total_objs"] == 0:  # Reset predId count upon reaching a row w/ no objects (see trap 9)
                next_pred_id = 1
                continue
            if math.isnan(row["predecessorID"]):
                df.loc[i, "predecessorID"] = next_pred_id
                next_pred_id += 1

        # Set remaining NaNs to 0 (these represent empty rows)
        df = df.fillna(0)

        # Convert to Ints (PredID initializes as floats due to NaN)
        df = df.applymap(int)

        # Remove Image Num
        try:
            del df["image_num"]
        except KeyError:
            pass

        if not os.path.exists("recent"):
            os.mkdir("recent")

        df.to_csv("recent/recent_query.csv", index=False)

        return df
