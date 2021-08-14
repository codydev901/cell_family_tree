from parse.pred_id_assignment import PredIDAssignment

"""
Doc Doc Doc
"""


def main():

    trap_data = PredIDAssignment("BC8_yolo_v1.csv")
    trap_data.assign_pred_ids(2)


if __name__ == "__main__":

    main()
