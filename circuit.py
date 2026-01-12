import random
def cp_to_basegates(cp:list[str,int,int,int]):
    _,log_angle,sqbit,eqbit=cp
    return [['CX',sqbit,eqbit]]*2 # cp--> 2cx + ...
def create_qft_circuit(nqubit):
    qc = []
    # Apply a Hadamard gate to each qubit and add control rotation gates
    for i in range(nqubit):
        qc.append(['H', i])  # Hadamard gate on qubit i
        for j in range(i + 1, nqubit):
            # angle = np.pi / (2 ** (j - i))
            log_angel = j - i
            # qc.append(['CP',angle, i, j])  #  control rotation gate with qubit i controlling qubit j
            cp=['CP',log_angel,i,j]
            qc+=cp_to_basegates(cp=cp)
    return qc


def append_toffoli(gates, a,b,c):
    gates.append(['H', c])
    gates.append(['CX', b, c])
    gates.append(['H', c])
    gates.append(['CX', a, c])
    gates.append(['H', c])
    gates.append(['CX', b, c])
    gates.append(['H', c])
    gates.append(['CX', a, c])
    gates.append(['H', b])
    gates.append(['H', c])
    gates.append(['H', c])
    gates.append(['CX', a, b])
    gates.append(['H', a])
    gates.append(['H', b])
    gates.append(['CX', a ,b])
    

def create_rca_circuit(nqubit):
    gates = []
    grid0 = list(range(3, nqubit - 2, 2))
    grid1 = list(range(2, nqubit - 3, 2))
    grid2 = list(range(0, grid1[-1], 2))

    for i in grid0:
        gates.append(['CX', i + 1, i])
    for i in grid1:
        gates.append(['CX', i + 2, i])
    for i in grid2:
        # gates.append(['toff', i,i+1,i+2])
        append_toffoli(gates, i, i+1, i+2)

    gates.append(['CX', grid1[-1]+2, grid1[-1]+3])
    # gates.append(['toff', grid1[-1], grid1[-1]+1, grid1[-1]+3])
    append_toffoli(gates, grid1[-1], grid1[-1]+1, grid1[-1]+3)
    for i in grid1[::-1]:
        gates.append(['CX', i, i+1])
    for i in grid2[::-1]:
        # gates.append(['toff', i,i+1,i+2])
        append_toffoli(gates, i,i+1,i+2)
    for i in grid1[::-1]:
        gates.append(['CX', i+2, i])
    for i in grid0:
        gates.append(['CX', i+1, i])
    gates.append(['CX', 1, 0])

    return gates


def create_grover_circuit(nqubit):
    gates = []
    grid = list(range(0, nqubit - 3, 2))
    
    for i in grid:
        # gates.append(['toff', i,i+1,i+2])
        append_toffoli(gates, i, i+1, i+2)
    gates.append(['CX', i+2, i+3])
    for i in grid[::-1]:
        # gates.append(['toff', i,i+1,i+2])
        append_toffoli(gates, i, i+1, i+2)
    
    return gates
    
def create_xor_circuit(nqubit):
    def get_xor(sqbit,eqbit):
        if(sqbit==eqbit):
            return []
        elif(eqbit-sqbit==1): # cx
            return [['CX',sqbit,eqbit]]
        elif(eqbit-sqbit==2):# toffoli
            gates=[]
            append_toffoli(gates, sqbit,sqbit+1,eqbit)
            return gates
        mqbit=(sqbit+eqbit)//2 # Decompose to sqbit->mqbit mqbit->eqbit
        up_xor=get_xor(sqbit=sqbit,eqbit=mqbit)
        low_xor=get_xor(sqbit=mqbit,eqbit=eqbit)
        result=(up_xor+low_xor)*2
        return result
    return get_xor(sqbit=0,eqbit=nqubit-1)


import networkx as nx
import numpy as np

