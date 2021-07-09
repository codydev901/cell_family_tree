import os
from parse.trap_data import TrapData
from parse.trap_graph import TrapGraph
from parse.trap_data_raw import TrapDataRaw
from parse.trap_graph_raw import TrapGraphRaw
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


def rls_area_analysis(source_file):
    """
    Writes .csv with following info for all traps in a given source file:
    trap_num, branch_count, time_num_endpoint (the time_num the algo cuts off)
    """

    print("Running RLS ObjCount Meta-Analysis")

    exp_rls_results = parse_experimental_results("experimental_results/BC8_rls_exp.csv")

    print(exp_rls_results)

    trap_data = TrapDataRaw(source_file)
    for t in exp_rls_results:
        try:
            trap_graph = TrapGraphRaw(df=trap_data.get_single_trap_df(t))
            exp_rls_results[t][source_file] = {"num_divisions": trap_graph.num_divisions,
                                     "t_stop": trap_graph.t_stop,
                                     "stop_condition": trap_graph.stop_condition
                                     }
        except ValueError:
            continue

    print(exp_rls_results)

    res = [["trap_num", "experimental", "predicted", "t_stop", "stop_condition"]]
    for t in exp_rls_results:
        if source_file in exp_rls_results[t]:
            res.append([t,
                        exp_rls_results[t]["ground_truth"],
                        exp_rls_results[t][source_file]["num_divisions"],
                        exp_rls_results[t][source_file]["t_stop"],
                        exp_rls_results[t][source_file]["stop_condition"]
                        ])

    write_csv("reports/{}_AreaRLS.csv".format(source_file.replace(".csv", "")), res)


def main():

    if not os.path.exists("reports"):
        os.mkdir("reports")

    # source_files = os.listdir("data")

    source_files = ["FT_BC8_yolo_short.csv"]

    # trap_data_meta_analysis(source_files)

    # root_cell_endpoint_analysis(source_files)

    # rls_analysis(source_files)

    source_files = ["BC8_yolo_v1.csv"]

    rls_area_analysis(source_files[0])


if __name__ == "__main__":

    main()
