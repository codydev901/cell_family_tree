import sys
import math
import csv
import numpy as np
from scipy.signal import find_peaks
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px

"""
Doc Doc Doc
"""


class PredIDAssignment:

    def __init__(self, file_name):
        self.file_name = file_name
        self.df = pd.read_csv("data/{}".format(self.file_name))
        self.traps = list(self.df["trap_num"].unique())
        self.params = {"mdt": 5.0}

    def assign_pred_ids(self, trap_num):
        """
        Assumptions

        The starting cell is the mother cell. Ideally there is one starting cell.
        Starting position of mother cell obtained at time_num 1.
        Daughter cells will form at either above or below the mother cell. Most variation expected in Y.
        Only a single daughter cell will be active at a time.
        Any additional cells that appear while a division is in process or not above/below the mother cell are ignored.
        Loss of mother cell leads to all future cells being ignored.
        Mother Cell is predID 1
        Daughter Cells are predID 2->X. New predIDs assigned to new daughter cells.
        Ignore Cells are predID 0 - No reason to track them.
        """

        start_num_obj = self.df.query("time_num == 1 & trap_num == {}".format(trap_num))["total_objs"].tolist()[0]

        print("Assign PredID TrapNum:{} StartNumObj:{}".format(trap_num, start_num_obj))

        if start_num_obj != 1:
            raise ValueError("Only Supporting Single Obj Atm")

        parsed_data = [["trap_num", "time_num", "total_objs", "obj_num", "obj_x", "obj_y", "pred_id"]]

        mother_x = 0.0
        mother_y = 0.0
        daughter_x = 0
        daughter_y = 0
        is_dividing = False
        lost_mother = False
        next_daughter_id = 2

        last_step_mother_distance = 0.0
        last_step_daughter_distance = 0.0

        # Clean this up..
        time_df = self.df.query("time_num == 1 & trap_num == {}".format(trap_num))
        for i, row in time_df.iterrows():
            mother_x = row["obj_X"]
            mother_y = row["obj_Y"]

        for t in self.df["time_num"].unique():
            time_df = self.df.query("time_num == {} & trap_num == {}".format(t, trap_num))
            # found_mother = False

            # First Try to Identify Mother Cell (Done first on purpose/two iteration steps)
            mother_cell_distances = []
            for i, row in time_df.iterrows():
                obj_x = row["obj_X"]
                obj_y = row["obj_Y"]

                # Each row is an obj (cell) at this trap & time_num. We have the starting mother cell coordinates.
                # We calculate distance to mother cell
                dis = math.hypot(obj_x - mother_x, obj_y - mother_y)
                mother_cell_distances.append([dis, obj_x, obj_y])

            mother_cell_distances.sort(key=lambda x: x[0])
            closest_cell = mother_cell_distances[0]
            mother_x = closest_cell[1]
            mother_y = closest_cell[2]

            if closest_cell[0] > 2:
                print("Mother Distance: ", t, closest_cell[0])
                print(mother_cell_distances)
                print("\n")

            # sys.exit()

            # Log If Not Found
            # if not found_mother:
            #     lost_mother = True
            #     print("Lost Mother: Trap_Num:{} Time_Num:{} Closest Distance:{}".format(trap_num, t, closest_distance_mother))
            #     time.sleep(10)

            # Now Re-iterate to assign IDs
            for i, row in time_df.iterrows():
                trap_num = row["trap_num"]
                time_num = row["time_num"]
                total_objs = row["total_objs"]
                obj_num = row["obj_num"]
                obj_x = row["obj_X"]
                obj_y = row["obj_Y"]
                pred_id = 0

                # Each row is an obj (cell) at this trap & time_num. We have the starting mother cell coordinates.
                # We calculate distance to mother cell
                dis = math.hypot(obj_x - mother_x, obj_y - mother_y)
                # if dis <= closest_distance_mother:
                #     closest_distance_mother = dis

                # If Distance to Mother Cell < MDT. New Mother Cell Coordinates (So next step compares to this one)
                if obj_x == mother_x and obj_y == mother_y:
                    pred_id = 1
                    mother_x = obj_x
                    mother_y = obj_y
                    parsed_data.append([trap_num, time_num, total_objs, obj_num, obj_x, obj_y, pred_id])
                    continue

                # If Not Dividing And Distance to Mother Cell within Daughter Cell Range
                # print("Not Mother")
                # print("X/Y Distance: ", abs(obj_x - mother_x), abs(obj_y - mother_y), t)
                parsed_data.append([trap_num, time_num, total_objs, obj_num, obj_x, obj_y, pred_id])

        f_name = self.file_name.replace(".csv", "_") + str(trap_num) + "_" + "NewPredID.csv"

        with open("new_pred_id_data/{}".format(f_name), "w") as w_file:
            writer = csv.writer(w_file, delimiter=",")
            for row in parsed_data:
                writer.writerow(row)

    def plot_trap_x_y(self, trap_num):

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


        # fig = go.Figure()
        #
        # fig.layout.title["text"] = "TrapNum:{} Cell X/Y".format(trap_num)
        #
        # for i, c_c in enumerate(cell_coordinates):
        #     fig.add_trace(go.Scatter(x=[v[0] for v in c_c], y=[v[1] for v in c_c], mode="markers", name="t_{}".format(i+1)))
        #
        # fig.show()








