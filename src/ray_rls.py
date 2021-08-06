import ray
import time
import csv
import pandas as pd

from parse.trap_data import TrapData
from parse.rls_params import RLSParams

"""
Ray Notes

Dashboard launches for duration, can be seen at http://127.0.0.1:8265/

Ray = 54 seconds
Regular = 94 seconds

class RLSParams:

    def __init__(self,
                 peak_distance=5,
                 next_cells_1_obj_range=5,
                 next_cells_1_obj_count=5,
                 num_divisions_threshold=2,
                 std_change_range=7,
                 std_change_threshold=4.5,
                 obj_drop_current=6,
                 obj_drop_next=2,
                 obj_drop_noise_range=21,
                 obj_drop_noise_threshold=2,
                 avg_peak_constant=1.25,
                 avg_peak_time_threshold=150):

        self.peak_distance = peak_distance
        self.next_cells_1_obj_range = next_cells_1_obj_range
        self.next_cells_1_obj_count = next_cells_1_obj_count
        self.num_divisions_threshold = num_divisions_threshold
        self.std_change_range = std_change_range
        self.std_change_threshold = std_change_threshold
        self.obj_drop_current = obj_drop_current
        self.obj_drop_next = obj_drop_next
        self.obj_drop_noise_range = obj_drop_noise_range
        self.obj_drop_noise_threshold = obj_drop_noise_threshold
        self.avg_peak_constant = avg_peak_constant
        self.avg_peak_time_threshold = avg_peak_time_threshold
"""

ray.init()

trap_data = TrapData("BC8_yolo_v1.csv")

# Not final structure
PARAM_SEARCH = [
    RLSParams(),
    RLSParams(peak_distance=4),
    RLSParams(peak_distance=6),
    RLSParams(num_divisions_threshold=5, peak_distance=6)
]


@ray.remote
def get_rls(trap_num):
    return trap_data.get_rls_peak(trap_num, params=RLSParams())


@ray.remote
def get_rls_param_search(param):
    return trap_data.get_rls_peak_all(params=param, as_sum_res=True)


def main():

    # start_time = time.time()
    #
    # futures = [get_rls.remote(i) for i in trap_data.traps]
    # print(ray.get(futures))
    #
    # print("Ray Time: ", time.time() - start_time)

    # start_time = time.time()
    #
    # regular = [trap_data.get_rls_peak(i) for i in trap_data.traps]
    #
    # print("Regular Time: ", time.time() - start_time)
    # print(regular)

    print("Starting Param Search")

    futures = [get_rls_param_search.remote(v) for v in PARAM_SEARCH]

    print("Param search done")

    print(ray.get(futures))

    futures_list = ray.get(futures)

    res = [["sum_residual"] + RLSParams.get_param_headers()]
    for v in futures_list:
        res.append(v[0])

    with open("ray_param_search.csv", "w") as w_file:
        writer = csv.writer(w_file, delimiter=",")
        for row in res:
            writer.writerow(row)


if __name__ == "__main__":

    main()

