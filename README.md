# cell_family_tree
Contains code focused around the reconstruction and analysis of cell family lineages from time lapsed image data.

### Installation
clone repo, make a virtual env if desired, pip install requirements.txt.
<br>
pandas and numpy only real requirements, so venv may not be necessary.

### Structure
/data: contains raw source files. These are in a standardized format
<br>
/parse: contains code used to convert the raw source files into a graph
<br>
Additionally /recent and /cytoscape folders will be generated if applicable. Recent will the most recent query. Cytoscape will hold generated cyotoscape networks.
<br>
Various analysis scripts are located in the outer level.

### Use
Source file parsing is divided into two stages.
trap_data.py is the first stage, it does the initial load of the .csv and queries which traps are present.
<br>
trap_graph.py is the second stage, it takes data from a single trap and converts to a graph.
```python
from cell_family_tree.parse.trap_data import TrapData
from cell_family_tree.parse.trap_graph import TrapGraph

# Initial load of a soruce file
trap_data = TrapData("FT_BC8_yolo_short.csv")
print(trap_data.traps) # Can shows the traps present in the file

# For some more detailed analysis, can call (not called on init)
trap_data.set_data_info(do_write=True)  # If wish to write this info, set do_write to True

# To get a df of a trap 1
df = trap_data.get_single_trap_df(1, t_stop=None)    # Can specify a stop time if desired.

# To parse into a graph
trap_graph = TrapGraph(df, run_graph=True, file_name=None)  # run_graph & file_name are args used in special cases

# Some important attributes on the TrapGraph Obj
trap_graph.graph = {}           # k,v where NodeName: [EdgeNodeName, ...] "X.Y" where X == time_num & Y == pred_id
trap_graph.root_nodes = []      # List of root nodes "X.Y"
trap_graph.root_pred_ids = []   # List of root pred ids
trap_graph.branch_nodes = []    # List of nodes where branches occur (length represents number of divisions)
trap_graph.time_num_obj = []    # time_num associated w/ obj_count
trap_graph.root_endpoints = {}  # Last time_num where a root node was seen
```

### Reports
TODO

### Cytoscape
TODO

