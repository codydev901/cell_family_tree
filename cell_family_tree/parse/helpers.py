import csv

"""
Doc Doc Doc
"""


def write_csv(file_path, data_arr):

    with open(file_path, "w") as w_file:
        writer = csv.writer(w_file, delimiter=",")
        for row in data_arr:
            writer.writerow(row)
