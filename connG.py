import networkx as nx
import numpy as np
def create_fat_tree(edge_weight,node_weight):
    G=nx.Graph()
    for i in range(0,10):
        G.add_node(i,is_router=True,is_rack_router=False,state=[])
    for i in range(0,4):
        G.nodes[i]['is_rack_router']=True
        G.nodes[i]['state']=[0]*node_weight
    edges = [(0, 4), (0, 5), (1, 4), (1, 6), (2, 5), (2, 7),
              (3, 6), (3, 7), (4, 8), (4, 9), (5, 8), (5, 9), 
              (6, 8), (6, 9), (7, 8), (7, 9)]
    for edge in edges:
        G.add_edge(*edge,weight=edge_weight,state=[0]*edge_weight)
    return G
def gen_clos_conn(n,node_weight,edge_weight):
    n=int(n)
    bandwidth = edge_weight
    num_ToR = 3 # number of qpus per rack                       #unused
    num_core = n // 2
    num_agg = n
    num_edge = n**2 // 4
    num_nodes = num_edge * num_ToR # number of q nodes          #unused

    num_vertices = num_core + num_agg + num_edge + num_nodes    #unused
    core_bw = 4*bandwidth
    agg_bw = 2*bandwidth
    edge_bw = bandwidth

    G = nx.Graph()

    edge_switches = range(0,num_edge)
    G.add_nodes_from(edge_switches, is_router=True,is_rack_router=True,state=[0]*node_weight)

    core_switches = range(num_edge,num_edge+num_core)
    G.add_nodes_from(core_switches, is_router=True,is_rack_router=False,state=[])
    agg_switches = range(num_edge+num_core,num_edge+num_core+num_agg)
    G.add_nodes_from(agg_switches, is_router=True,is_rack_router=False,state=[])
    
    for core in core_switches:
        for agg in agg_switches:
            G.add_edge(core,agg, weight=core_bw,state=[0]*core_bw)

    agg_conn = np.ones(num_agg)* (n//2)
    for i, edge in enumerate(edge_switches):
        i1 = np.argwhere(agg_conn>0)[0,0]
        G.add_edge(edge,agg_switches[i1], weight=agg_bw,state=[0]*agg_bw)
        agg_conn[i1] -= 1 
        G.add_edge(edge,agg_switches[i1+1], weight=agg_bw,state=[0]*agg_bw)
        agg_conn[i1+1] -= 1 
    return G#,core_switches,agg_switches,edge_switches,node_list
def gen_L2_fat_tree(edge_weight,node_weight):# rack:8, up_router:4
    G=nx.Graph()
    for i in range(0,12):
        G.add_node(i,is_router=True,is_rack_router=False,state=[])
    for i in range(0,8):
        G.nodes[i]['is_rack_router']=True
        G.nodes[i]['state']=[0]*node_weight
    for up_router in range(8,12):
        for rack_router in range(0,8):
            edge=(up_router,rack_router)
            G.add_edge(*edge,weight=edge_weight,state=[0]*edge_weight)
    return G
def gen_L3_fat_tree(edge_weight,node_weight):# rack:6, mid:4 up:2
    G=nx.Graph()
    for i in range(0,12):
        G.add_node(i,is_router=True,is_rack_router=False,state=[])
    for i in range(0,6):
        G.nodes[i]['is_rack_router']=True
        G.nodes[i]['state']=[0]*node_weight
    for mid_router in range(6,10):
        for rack_router in range(0,6):
            edge=(mid_router,rack_router)
            G.add_edge(*edge,weight=edge_weight,state=[0]*edge_weight)
    for up_router in range(10,12):
        for mid_router in range(6,10):
            edge=(up_router,mid_router)
            G.add_edge(*edge,weight=edge_weight,state=[0]*edge_weight)
    return G