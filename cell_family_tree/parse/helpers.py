import csv

"""
Doc Doc Doc
"""


def write_csv(file_path, data_arr):

    with open(file_path, "w") as w_file:
        writer = csv.writer(w_file, delimiter=",")
        for row in data_arr:
            writer.writerow(row)


def read_csv(file_path):

    with open(file_path, "r") as r_file:
        reader = csv.reader(r_file, delimiter=",")
        return [row for row in reader]


def parse_experimental_results(file_path):

    exp_data = read_csv(file_path)

    exp_res = dict()

    for r in exp_data[1:]:
        if not r:
            continue
        try:
            exp_res[int(r[0])] = int(r[1])
        except ValueError:
            if "l" in r[1]:
                exp_res[int(r[0])] = int(r[1].replace("l", ""))
            else:
                exp_res[int(r[0])] = "non_int:{}".format(r[1])

    return exp_res
