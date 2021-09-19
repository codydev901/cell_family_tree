from parse.pred_id_assignment import PredIDAssignment

"""
Notes

Mother Cell will be centered around X/Y 30/30
For traps that start with multiple cells, 


"""


def main():

    trap_data = PredIDAssignment("BC8_yolo_v1.csv")
    # trap_data.assign_pred_ids(1)

    trap_data.plot_trap_x_y(1)


if __name__ == "__main__":

    main()
