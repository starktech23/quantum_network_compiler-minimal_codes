import networkx as nx
from copy import deepcopy
import random
def addqpu(G,edge_weight,qpu_mapping_result):
    G=deepcopy(G)
    counter=len(list(G.nodes))
    rack_qpu={}# qpus within each rack
    for qpu,rack in enumerate(qpu_mapping_result):
        if(rack not in rack_qpu):
            rack_qpu[rack]=[]
        rack_qpu[rack].append(qpu)
    qpu_connG_mapping_result={}
    for node in list(G.nodes):# copy Gnodes
        if(G.nodes[node]['is_rack_router']):# rackid corresponds, qpuid  not correspond
            for qpu in rack_qpu[node]:
                G.add_node(counter,is_router=False,is_rack_router=False,origin_qpu_id=qpu,state=[])
                qpu_connG_mapping_result[qpu]=counter
                G.add_edge(*(node,counter),weight=edge_weight,state=[0]*edge_weight)
                counter+=1
    return G,qpu_connG_mapping_result
def get_qpu_dist_mat(qpu_mapping_result):# qpu id starts from 0
    qpu_num=len(qpu_mapping_result)
    Weight = [[0 for _ in range(qpu_num)] for _ in range (qpu_num)]
    # Calculate the shortest path between leaf nodes
    for i in range(0,qpu_num-1):# qpu id starts from 0
        for j in range(i+1,qpu_num):
            if qpu_mapping_result[i]==qpu_mapping_result[j]:
                Weight[i][j] = 0.3
                Weight[j][i] = 0.3
            else:
                Weight[i][j] = 1
                Weight[j][i] = 1
    return Weight
def get_qbit_mapping(qpu_qbit):#{qpuid:[qbit,qbit,..]}->[qpuid,qpuid]
    qbit_num=0
    for qpuid,qbit_list in qpu_qbit.items():
        for qbit in qbit_list:
            qbit_num+=1
    print(qbit_num)
    qbit_mapping=[-1]*qbit_num
    for qpuid,qbit_list in qpu_qbit.items():
        for qbit in qbit_list:
            qbit_mapping[qbit]=qpuid
    return qbit_mapping
def get_rack_qpu(qpu_mapping_result):
    rack_qpu={}# qpus within each rack
    for qpu,rack in enumerate(qpu_mapping_result):
        #print(rack)
        if(rack not in rack_qpu):
            rack_qpu[rack]=[]
        rack_qpu[rack].append(qpu)
    rack_qpu_list=[0]*len(rack_qpu)
    for rack,qpu_list in rack_qpu.items():
        rack_qpu_list[rack]=qpu_list
    return rack_qpu_list
def gen_dag(routing_result,qpu_connG_mapping_result,base_offset=0):

    # build DAG
    DAG = nx.DiGraph()

    # create a node for each operation
    for idx, op in enumerate(routing_result):
        node_id = idx+base_offset # id corresponds to the list order 0 1 2 3
        info0, info1, op_type = op
        info0=qpu_connG_mapping_result[info0]
        info1=qpu_connG_mapping_result[info1]
        is_teleport = (op_type == 'T')
        DAG.add_node(node_id, info=(info0, info1), is_teleport=is_teleport)

    # not accurate, best to use qubits instead of qpu
    # Add edges to ensure that the same QPU does not operate on multiple logical gates at the same time.
    last_used = {}  # Record last operation on QPU
    for idx, op in enumerate(routing_result):
        idx+=base_offset
        qpu1, qpu2 = op[0], op[1]
        # find the operation that last used this qpu, build an edge from that operation to the current operation
        for qpu in [qpu1, qpu2]:
            if qpu in last_used:
                DAG.add_edge(last_used[qpu], idx)
        # update the last usage records for these two QPUs
        last_used[qpu1] = idx
        last_used[qpu2] = idx
    return DAG
def count_EPR(routing_result,qpu_mapping_result):
    cross,inter=0,0
    for op in routing_result:
        info0, info1, _ = op
        if(qpu_mapping_result[info0]==qpu_mapping_result[info1]):
            inter+=1
        else:
            cross+=1
    return cross,inter
def count_DAG_EPR(DAG,connG):
    cross,inter=0,0
    for node in DAG.nodes:
        info0, info1 = DAG.nodes[node]['info']
        if(list(connG.neighbors(info0))[0]==list(connG.neighbors(info1))[0]):
            inter+=1
        else:
            cross+=1
    return cross,inter
def base_mapping(rack_num,qpu_per_rack):
    qpu_num=rack_num*qpu_per_rack
    mapping = [-1]*qpu_num # qpu->rack
    for rack in range(rack_num):
        for rack_qpu in range(qpu_per_rack):
            mapping[rack*qpu_per_rack+rack_qpu]=rack
    return mapping
def shuffle_routing_result(rack_num,qpu_per_rack,routing_result):
    all_qpu=[]
    for rack_id in range(rack_num):
        rack=[]
        for qpu_id in range(qpu_per_rack):
            rack.append(rack_id*qpu_per_rack+qpu_id)
        random.shuffle(rack)
        all_qpu.append(rack)
    random.shuffle(all_qpu)
    map=[]
    for rack in all_qpu:
        map+=rack
    for op in routing_result:
        op[0]=map[op[0]]
        op[1]=map[op[1]]
    return routing_result
def gen_mult_DAG(routing_result,qpu_connG_mapping_result,rack_num,qpu_per_rack,mul=10):
    qpu_num=rack_num*qpu_per_rack
    graphs=[]
    for iter in range(mul):
        shuffle_result=shuffle_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,
                                              routing_result=deepcopy(routing_result))
        G_iter=gen_dag(routing_result=shuffle_result,
                       qpu_connG_mapping_result=qpu_connG_mapping_result,base_offset=qpu_num*iter)
        graphs.append(G_iter)
    G=nx.disjoint_union_all(graphs=graphs)
    return G
def gen_mix_DAG(qpu_connG_mapping_result,rack_num,qpu_per_rack,qbit_per_qpu,mul=2):
    qpu_num=rack_num*qpu_per_rack
    base_offset=0
    from hand_routing import gen_qft_routing_result,gen_qaoa_routing_result,gen_grover_routing_result,gen_rca_routing_result
    funcs=[gen_qft_routing_result,gen_qaoa_routing_result,gen_grover_routing_result,gen_rca_routing_result]
    routing_results=[]
    for func in funcs:
        routing_results.append(func(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu))
    graphs=[]
    for _ in range(mul):
        for result in routing_results:
            shuffle_result=shuffle_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,
                                              routing_result=deepcopy(result))
            G_iter=gen_dag(routing_result=shuffle_result,
                           qpu_connG_mapping_result=qpu_connG_mapping_result,base_offset=base_offset)
            graphs.append(G_iter)
            base_offset+=qpu_num
    G=nx.disjoint_union_all(graphs=graphs)
    return G