
"""
Default RLS Params
"""


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

    # Do this correctly TODO
    def to_param_list(self):

        return [self.peak_distance, self.next_cells_1_obj_range, self.next_cells_1_obj_count,
                self.num_divisions_threshold, self.std_change_range, self.std_change_threshold,
                self.obj_drop_current, self.obj_drop_next, self.obj_drop_noise_range,
                self.obj_drop_noise_threshold, self.avg_peak_constant, self.avg_peak_time_threshold]

    # Do this correctly TODO
    @staticmethod
    def get_param_headers():

        return ["peak_distance",
                "next_cells_1_obj_range",
                "next_cells_1_obj_count",
                "num_divisions_threshold",
                "std_change_range",
                "std_change_threshold",
                "obj_drop_current",
                "obj_drop_next",
                "obj_drop_noise_range",
                "obj_drop_noise_threshold",
                "avg_peak_constant",
                "avg_peak_time_threshold"]

