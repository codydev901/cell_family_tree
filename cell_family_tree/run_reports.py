import os
from parse.trap_data import TrapData
from parse.trap_graph import TrapGraph
from parse.helpers import write_csv, parse_experimental_results

"""
Doc Doc Doc
"""


def trap_data_meta_analysis(source_files):
    """
    Writes .csv with following info for all traps in a given source file:
    trap_num, time_max, root_cell_count, total_cell_count, unique_pred_ids, empty_count, predId counts
    """

    print("Running Trap Data Meta-Analysis")

    for s in source_files:
        trap_data = TrapData(s)
        trap_data.set_data_info(do_write=True)


def root_cell_endpoint_analysis(source_files):
    """
    Writes .csv with following info for all traps in a given source file:
    trap_num, root_pred_id, endpoint_time_num
    """

    print("Running Root Cell Endpoint Meta-Analysis")

    for s in source_files:
        res = [["trap_num", "root_pred_id", "endpoint_time_num"]]
        trap_data = TrapData(s)
        for t in trap_data.traps:
            trap_df = trap_data.get_single_trap_df(trap_num=t)
            trap_graph = TrapGraph(trap_df, run_graph=False)
            for root_pred_id in trap_graph.root_endpoints:
                res.append([t, root_pred_id, trap_graph.root_endpoints[root_pred_id]])

        write_csv("reports/{}_RootCellEndpointAnalysis.csv".format(s.replace(".csv", "")), res)


def rls_analysis(source_files):
    """
    Writes .csv with following info for all traps in a given source file:
    trap_num, branch_count, root_node_endpoints (the time_num the root_node was first last seen/algo cuts off)
    """

    print("Running RLS Meta-Analysis")

    exp_rls_results = parse_experimental_results("experimental_results/BC8_rls_exp.csv")

    for s in source_files:
        res = [["trap_num", "total_branch_count", "root_branch_count", "experimental", "t_stop"]]
        trap_data = TrapData(s)
        for t in trap_data.traps:
            trap_df = trap_data.get_single_trap_df(trap_num=t)
            trap_graph = TrapGraph(trap_df, run_graph=False)
            if len(trap_graph.root_nodes) != 1:
                continue
            try:
                trap_graph = TrapGraph(trap_df, run_graph=True)
            except ValueError:
                res.append([t, "ParseFail", "ParseFail"] + [exp_rls_results[t]])
                continue
            res.append([t, len(trap_graph.branch_nodes), len(trap_graph.root_branch_nodes)] + [exp_rls_results[t]] + [trap_graph.t_stop])

        write_csv("reports/{}_RLSAnalysis.csv".format(s.replace(".csv", "")), res)


def rls_from_obj_analysis(source_files):
    """
    Writes .csv with following info for all traps in a given source file:
    trap_num, branch_count, time_num_endpoint (the time_num the algo cuts off)
    """

    print("Running RLS ObjCount Meta-Analysis")

    exp_rls_results = parse_experimental_results("experimental_results/BC8_rls_exp.csv")

    results = {}
    traps = []
    for s in source_files:
        results[s] = {}
        trap_data = TrapData(s)
        for t in trap_data.traps:
            results[s][t] = {}
            trap_df = trap_data.get_single_trap_df(trap_num=t)
            trap_graph = TrapGraph(trap_df, run_graph=False)
            if len(trap_graph.root_nodes) != 1:
                continue
            if t not in traps:
                traps.append(t)
            results[s][t] = trap_graph.get_divisions_from_obj_count()

    file_names = list(results.keys())
    res = [["trap_num"] + file_names + ["experimental"] + ["{}_EndPoint".format(v) for v in file_names]]
    for t in traps:
        trap_res = [t]
        end_points = []
        for s in source_files:
            trap_res.append(results[s][t]["num_branches"])
            end_points.append(results[s][t]["break_time_num"])
        trap_res.append(exp_rls_results[t])
        res.append(trap_res + end_points)

    write_csv("reports/all_source_obj_count_branch_count.csv", res)


def main():

    if not os.path.exists("reports"):
        os.mkdir("reports")

    # source_files = os.listdir("data")

    source_files = ["FT_BC8_yolo_short.csv"]

    # trap_data_meta_analysis(source_files)

    # root_cell_endpoint_analysis(source_files)

    rls_analysis(source_files)

    # rls_from_obj_analysis(source_files)


if __name__ == "__main__":

    main()
