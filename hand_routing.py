from copy import deepcopy
import random
from circuit import create_qft_circuit,create_rca_circuit,create_grover_circuit,create_xor_circuit, create_qaoa_circuit

def gen_qft_routing_result(rack_num,qpu_per_rack,qbit_per_qpu):
    qpu_num=rack_num*qpu_per_rack
    routing_result=[]
    for loop_start in range(qpu_num-1):
        for _ in range(qbit_per_qpu):
            for tp_start in range(loop_start,qpu_num-1):
                routing_result.append([tp_start,tp_start+1,'T'])
            routing_result.append([qpu_num-1,loop_start,'T'])
    return routing_result
# def gen_qaoa_routing_result(rack_num,qpu_per_rack,qbit_per_qpu):
#    qpu_num=rack_num*qpu_per_rack
#    temp_routing_result=[]
#    routing_result=[]
#    for loop_start in range(0,qpu_num-1):
#        temp_result=[]
#        for _ in range(qbit_per_qpu):
#            for tp_start in range(loop_start,qpu_num-1):
#                temp_result.append([tp_start,tp_start+1,'T'])
#             temp_result.append([qpu_num-1,loop_start,'T'])
#         temp_routing_result.append(temp_result)
#     random.shuffle(temp_routing_result)
#     for result in temp_routing_result:
#         routing_result+=result
#     return routing_result

from copy import deepcopy

def gen_qaoa_routing_result(rack_num, qpu_per_rack, qbit_per_qpu, edges):
    """
    Generates the inter-QPU routing schedule for a QAOA algorithm.

    The function identifies the required connections between QPUs to execute the
    two-qubit CX gates defined by the problem graph's edges.

    Args:
        rack_num (int): The number of racks in the quantum hardware.
        qpu_per_rack (int): The number of QPUs per rack.
        qbit_per_qpu (int): The number of qubits per QPU.
        edges (list of tuples): A list of tuples, where each tuple (u, v)
                                represents an edge in the problem graph,
                                corresponding to a CX(u,v)-Rz(v)-CX(u,v) operation.
        p (int): The number of QAOA layers (or rounds). Defaults to 1.

    Returns:
        list: A list of required connections, where each connection is formatted as
              [source_qpu, target_qpu, 'CX']. The list is repeated for p rounds.
    """
    # Calculate the total number of QPUs and qubits in the system
    qpu_num = rack_num * qpu_per_rack
    qbit_num = qpu_num * qbit_per_qpu

    # --- Build the routing plan for a SINGLE QAOA layer ---
    # This list will hold the required connections for one application of the
    # Problem Unitary (U_C). The Mixer Unitary only uses single-qubit gates
    # and thus requires no inter-QPU routing.
    one_layer_connections = []



    # Iterate over every edge in the problem graph
    for u, v in edges:
        # Check if qubits u and v are within the total number of available qubits
        if u >= qbit_num or v >= qbit_num:
            print(f"Warning: Edge ({u}, {v}) is out of bounds for the {qbit_num} available qubits. Skipping.")
            continue

        # Determine the QPU for each qubit in the edge using integer division
        qpu_u = u // qbit_per_qpu
        qpu_v = v // qbit_per_qpu

        # CORE ROUTING LOGIC:
        # Only record a connection if the two qubits are on DIFFERENT QPUs.
        if qpu_u != qpu_v:
            # The edge (u, v) corresponds to a CX(u, v) -> Rz(v) -> CX(u, v) sequence.
            # The Rz gate is local and requires no routing.
            # Both CX gates require the same remote connection between qpu_u and qpu_v.

            # Schedule the connection for the first CX gate
            one_layer_connections.append([qpu_u, qpu_v, 'CX'])

            # Schedule the connection for the second CX gate
            one_layer_connections.append([qpu_u, qpu_v, 'CX'])

    # --- Assemble the full routing plan by repeating the layer p times ---
    routing_result = []
    # for _ in range(p=1):
        # Use deepcopy to ensure each layer is a distinct object in the list
    routing_result += deepcopy(one_layer_connections)

    return routing_result


import random


def generate_all_to_all_graph(num_qubits):
    """
    Generates the edge list for a complete (all-to-all) graph.
    Every qubit is connected to every other qubit.

    Args:
        num_qubits (int): The total number of qubits (nodes) in the graph.

    Returns:
        list: A list of tuples representing the graph edges.
    """
    edges = []
    if num_qubits < 2:
        return []
    # Iterate through all unique pairs of qubits
    for i in range(num_qubits):
        for j in range(i + 1, num_qubits):
            edges.append((i, j))
    return edges


def generate_regular_graph(num_qubits, degree):
    """
    Generates the edge list for a k-regular graph where each node has a
    fixed degree. This uses the "pairing model".
    Note: May not succeed for all combinations of num_qubits and degree.

    Args:
        num_qubits (int): The total number of qubits (nodes).
        degree (int): The desired degree for each node (e.g., 3 for 3-regular).

    Returns:
        list: A list of tuples representing the graph edges.
    """
    if (num_qubits * degree) % 2 != 0:
        raise ValueError("For a regular graph, the product of num_qubits and degree must be even.")

    # Create a list of 'stubs' for each node
    stubs = [node for node in range(num_qubits) for _ in range(degree)]
    random.shuffle(stubs)

    edges = set()  # Use a set to automatically handle multi-edges

    # Pair up stubs to create edges
    while stubs:
        u = stubs.pop()
        v = stubs.pop()

        # Avoid self-loops (a node connecting to itself)
        if u != v:
            # Add the edge in a canonical order (min, max) to prevent duplicates like (1,0) and (0,1)
            edge = tuple(sorted((u, v)))
            edges.add(edge)

    return list(edges)


def generate_random_graph(num_qubits, edge_probability):
    """
    Generates the edge list for a random G(n, p) graph.
    An edge is created between any two nodes with a given probability.

    Args:
        num_qubits (int): The total number of qubits (nodes), n.
        edge_probability (float): The probability of an edge existing, p. Must be between 0.0 and 1.0.

    Returns:
        list: A list of tuples representing the graph edges.
    """
    if not (0 <= edge_probability <= 1):
        raise ValueError("Edge probability must be between 0 and 1.")

    edges = []
    if num_qubits < 2:
        return []
    # Consider every possible edge
    for i in range(num_qubits):
        for j in range(i + 1, num_qubits):
            # Add the edge if a random roll succeeds
            if random.random() < edge_probability:
                edges.append((i, j))
    return edges

def gen_grover_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,repeat_num=50):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    routing_result=[]
    # one iter
    iter_result=[]
    cx_result=[]
    # cx
    for sbit in range(2,qbit_num-2,3):#sbit+1<qbit_num-1
        sqpu,mqpu,eqpu=sbit//qbit_per_qpu,(sbit+1)//qbit_per_qpu,(sbit+2)//qbit_per_qpu
        if(sqpu!=eqpu):
            cx_result.append([sqpu,eqpu,'T'])
        if(mqpu!=eqpu):
            cx_result.append([mqpu,eqpu,'T'])
    #Toffoli
    toffoli_result=[]
    for sbit in range(1,qbit_num-4,3):#sbit+3<qbit_num-1
        sqpu,eqpu=sbit//qbit_per_qpu,(sbit+3)//qbit_per_qpu
        if(sqpu!=eqpu):
            toffoli_result.append([sqpu,eqpu,'T'])
    half_result=deepcopy(toffoli_result[::-1])
    for tp in half_result:
        toffoli_result.append([tp[1],tp[0],'T'])
    iter_result+=deepcopy(cx_result)
    iter_result+=deepcopy(toffoli_result*2) #tow toffli
    half_result=deepcopy(cx_result[::-1])
    for tp in half_result:
        iter_result.append([tp[1],tp[0],'T'])
    for _ in range(repeat_num):
        routing_result+=deepcopy(iter_result)
    return routing_result
def gen_rca_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,repeat_num=50):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    routing_result=[]
    # init_midqbit
    for sbit in range(0,qbit_num-3,2):# without The last qbit,sbit+2<qbit_num-1
        mqpu,eqpu=(sbit+1)//qbit_per_qpu,(sbit+2)//qbit_per_qpu
        if(mqpu!=eqpu):
            routing_result.append([mqpu,eqpu,'T'])
    # one iter
    iter_result=[]
    #Toffoli
    for sbit in range(0,qbit_num-3,2):# without The last qbit,sbit+2<qbit_num-1
        sqpu,eqpu=sbit//qbit_per_qpu,(sbit+2)//qbit_per_qpu
        if(sqpu!=eqpu):
            iter_result.append([sqpu,eqpu,'T'])
    half_result=deepcopy(iter_result[::-1])
    for tp in half_result:
        iter_result.append([tp[1],tp[0],'T'])
    for _ in range(repeat_num):
        routing_result+=deepcopy(iter_result)
    return routing_result
def gen_xor_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,repeat_num=1):
    def get_cnx(sqpu,eqpu):
        if(sqpu==eqpu):
            return []
        elif(eqpu-sqpu==1):
            return [[sqpu,eqpu,'T'],[eqpu,sqpu,'T'],[sqpu,eqpu,'C']]# The last fact is TP, but qubits can be discarded after use
        mqpu=(sqpu+eqpu)//2 # decompose to sqpu->mqpu mqpu+1->eqpu,between tow QPU need TP
        result=[]
        up_xor=get_cnx(sqpu=sqpu,eqpu=mqpu)
        low_xor=get_cnx(sqpu=mqpu+1,eqpu=eqpu)
        result+=deepcopy(up_xor)
        result.append([mqpu,mqpu+1,'T']) # maximum ID is qpu_num-1
        result+=deepcopy(low_xor)
        result.append([mqpu+1,mqpu,'T'])
        result+=deepcopy(up_xor)
        result.append([mqpu,mqpu+1,'C']) # in fact, the last one is TP, but epr pair can be discarded after use
        result+=deepcopy(low_xor)
        return result
    def rack_decompose(srack,erack,qpu_per_rack):
        rack_num=erack-srack+1
        if(rack_num%3==0):
            mrack=(erack-srack)//3+srack
            mqpu=(mrack+1)*qpu_per_rack-1
            result=[]
            up_xor=rack_decompose(srack=srack,erack=mrack,qpu_per_rack=qpu_per_rack)
            low_xor=rack_decompose(srack=mrack+1,erack=erack,qpu_per_rack=qpu_per_rack)
            result+=deepcopy(up_xor)
            result.append([mqpu,mqpu+1,'T']) #maximum ID is qpu_num-1
            result+=deepcopy(low_xor)
            result.append([mqpu+1,mqpu,'T'])
            result+=deepcopy(up_xor)
            result.append([mqpu,mqpu+1,'C']) # in fact, the last one is TP, but epr pair can be discarded after use
            result+=deepcopy(low_xor)
            return result
        else:
            return get_cnx(sqpu=srack*qpu_per_rack,eqpu=(erack+1)*qpu_per_rack-1)
    iter_result=rack_decompose(srack=0,erack=rack_num-1,qpu_per_rack=qpu_per_rack)
    routing_result=[]
    for _ in range(repeat_num):
        routing_result+=deepcopy(iter_result)
    return routing_result

def qec_circ_to_EPR(circ:list[list[str,int,int]],qbit_num,qbit_per_qpu,code_dist,repeat_num=1):
    qbit_map=[]
    for qbit in range(qbit_num):
        qbit_map.append(qbit//qbit_per_qpu)
    iter_result=[]
    for gate in circ:
        if(gate[0]=='CX'):
            sqbit,eqbit=gate[1:]
            sqpu,eqpu=qbit_map[sqbit],qbit_map[eqbit]
            if(sqpu!=eqpu):
                iter_result+=[[sqpu,eqpu,'C']]*code_dist
    return deepcopy(iter_result*repeat_num)
def gen_qec_qft_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,code_dist,repeat_num=1):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    circ=create_qft_circuit(nqubit=qbit_num)
    return qec_circ_to_EPR(circ=circ,qbit_num=qbit_num,qbit_per_qpu=qbit_per_qpu,
                            code_dist=code_dist,repeat_num=repeat_num)
def gen_qec_rca_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,code_dist,repeat_num=1):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    circ=create_rca_circuit(nqubit=qbit_num)
    return qec_circ_to_EPR(circ=circ,qbit_num=qbit_num,qbit_per_qpu=qbit_per_qpu,
                            code_dist=code_dist,repeat_num=repeat_num)
def gen_qec_grover_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,code_dist,repeat_num=1):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    circ=create_grover_circuit(nqubit=qbit_num)
    return qec_circ_to_EPR(circ=circ,qbit_num=qbit_num,qbit_per_qpu=qbit_per_qpu,
                            code_dist=code_dist,repeat_num=repeat_num)
def gen_qec_xor_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,code_dist,repeat_num=1):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    circ=create_xor_circuit(nqubit=qbit_num)
    return qec_circ_to_EPR(circ=circ,qbit_num=qbit_num,qbit_per_qpu=qbit_per_qpu,
                            code_dist=code_dist,repeat_num=repeat_num)

def gen_qec_qaoa_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,code_dist, p=1, repeat_num=1):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    G = generate_regular_graph(qbit_num, 3)
    circ=create_qaoa_circuit(qbit_num, G, p)
    return qec_circ_to_EPR(circ=circ,qbit_num=qbit_num,qbit_per_qpu=qbit_per_qpu,
                            code_dist=code_dist,repeat_num=repeat_num)