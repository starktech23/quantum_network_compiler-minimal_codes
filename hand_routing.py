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
def gen_qaoa_routing_result(rack_num,qpu_per_rack,qbit_per_qpu):
    qpu_num=rack_num*qpu_per_rack
    temp_routing_result=[]
    routing_result=[]
    for loop_start in range(0,qpu_num-1):
        temp_result=[]
        for _ in range(qbit_per_qpu):
            for tp_start in range(loop_start,qpu_num-1):
                temp_result.append([tp_start,tp_start+1,'T'])
            temp_result.append([qpu_num-1,loop_start,'T'])
        temp_routing_result.append(temp_result)
    random.shuffle(temp_routing_result)
    for result in temp_routing_result:
        routing_result+=result
    return routing_result
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
def gen_qec_qaoa_routing_result(rack_num,qpu_per_rack,qbit_per_qpu,code_dist, p, gamma, beta, G, repeat_num=1):
    qpu_num=rack_num*qpu_per_rack
    qbit_num=qpu_num*qbit_per_qpu
    circ=create_qaoa_circuit(qbit_num, p, gamma, beta, G)
    return qec_circ_to_EPR(circ=circ,qbit_num=qbit_num,qbit_per_qpu=qbit_per_qpu,
                            code_dist=code_dist,repeat_num=repeat_num)