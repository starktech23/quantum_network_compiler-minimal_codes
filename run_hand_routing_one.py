import random
from copy import deepcopy
from time import time
#import Mapping_v3 as Mapping
#import Router as router
from Scheduling_v1_1 import Scheduler,Validater,Scheduler_baseline
#import circuit
import tools
import connG
import hand_routing
import os
import traceback
from math import sqrt

from hand_routing import generate_regular_graph


# qbit, qpu, and rack IDs start from 0
def run_one(kwargs):
    seed=kwargs['seed']
    test_mapper_type=kwargs['test_mapper_type']
    test_router_type=kwargs['test_router_type']
    test_scheduler_type=kwargs['test_scheduler_type']
    test_program_type=kwargs['test_program_type']
    test_conn_G_type=kwargs['test_conn_G_type']
    rack_num=kwargs['rack_num']
    qpu_per_rack=kwargs['qpu_per_rack']
    qbit_per_qpu=kwargs['qbit_per_qpu']
    outer_router_edge_weight=kwargs['outer_router_edge_weight']
    commqbit_num=kwargs['commqbit_num']
    rack_router_bsm_num=kwargs['rack_router_bsm_num']
    cache_size=kwargs['cache_size']
    cache_reserve_size=kwargs['cache_reserve_size']
    scheduling_reserve_size=kwargs['scheduling_reserve_size']
    schedu_depth=kwargs['schedu_depth']
    inter_time=kwargs['inter_time']
    switch_time=kwargs['switch_time']
    exter_time=kwargs['exter_time']
    split_mul=kwargs['split_mul']
    look_ahead=kwargs['look_ahead']
    join_map=kwargs['join_map']
    split=kwargs['split']
    prefix=kwargs['prefix']
    father_dir=kwargs['father_dir']
    repeat_num=kwargs['repeat_num']
    auto_retry_length=kwargs['auto_retry_length']
    retry_length=kwargs['retry_length']
    shoot_gap=kwargs['shoot_gap']
    check_CAT_sTP=kwargs['check_CAT_sTP']
    check_dTP=kwargs['check_dTP']
    check_split_num=kwargs['check_split_num']
    qec_program=kwargs['qec_program']
    code_dist=kwargs['code_dist']
    random.seed(seed) 
    qpu_num=qpu_per_rack*rack_num
    qubit_num=qpu_num*qbit_per_qpu

    end_edge_weight = commqbit_num 
    mid_edge_weight = outer_router_edge_weight # Two edges = total rack bandwidth

    dirs=father_dir+"/"+prefix+"/"
    if not os.path.exists(dirs):
        os.makedirs(dirs)
    file_name=dirs+test_mapper_type+'_'+test_router_type+'_'+test_scheduler_type+'_'+test_conn_G_type+\
        '_'+test_program_type+'_'+str(rack_num)+'_'+str(qpu_per_rack)+\
        '_'+str(qbit_per_qpu)+'_'+str(outer_router_edge_weight)+'_'+str(commqbit_num)+\
        '_'+str(rack_router_bsm_num)+'_'+str(cache_size)+'_'+str(cache_reserve_size)+\
        '_'+str(scheduling_reserve_size)+'_'+str(schedu_depth)+'_'+str(inter_time)+'_'+\
        str(switch_time)+'_'+str(exter_time)+'_'+str(split_mul)+'_'+str(look_ahead)+'_'+\
        str(join_map)+'_'+str(split)+'_'+str(auto_retry_length)+'_'+str(retry_length)+\
        '_'+str(shoot_gap)+'_'+'_'+str(check_CAT_sTP)+'_'+str(check_dTP)+'_'+str(check_split_num)+\
        '_'+str(qec_program)+'_'+str(code_dist)+'_'+str(seed)
    
    file = open(file_name +'.txt', 'w')
    file.write(str(kwargs)+"\n")
    
    if(test_conn_G_type=='fat_tree_L2'):
        conn_G = connG.gen_L2_fat_tree(edge_weight=mid_edge_weight,node_weight=rack_router_bsm_num)
    elif(test_conn_G_type=='fat_tree_L3'):
        conn_G = connG.gen_L3_fat_tree(edge_weight=mid_edge_weight,node_weight=rack_router_bsm_num)
    elif(test_conn_G_type=='clos'):
        conn_G = connG.gen_clos_conn(n=2*sqrt(rack_num),edge_weight=mid_edge_weight,node_weight=rack_router_bsm_num)
    else:
        file.write('invalid test conn_G type')
        raise ValueError("invalid test conn_G type")

    qpu_mapping_result = tools.base_mapping(rack_num=rack_num,qpu_per_rack=qpu_per_rack)
    conn_G_with_qpu,qpu_connG_mapping_result = tools.addqpu(G=conn_G,edge_weight=end_edge_weight,qpu_mapping_result=qpu_mapping_result)
    if(qec_program):
        if(test_program_type=="qft"):
            routing_result=hand_routing.gen_qec_qft_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,code_dist=code_dist)
        elif(test_program_type=="qaoa"):
            routing_result=hand_routing.gen_qec_qaoa_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,
                                                                    # edges=edges,
                                                                    code_dist=code_dist)
        elif(test_program_type=="rca"):
            routing_result=hand_routing.gen_qec_rca_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,code_dist=code_dist,repeat_num=repeat_num)
        elif(test_program_type=="grover"):
            routing_result=hand_routing.gen_qec_grover_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,code_dist=code_dist,repeat_num=repeat_num)
        elif(test_program_type=='xor'):
            routing_result=hand_routing.gen_qec_xor_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,code_dist=code_dist,repeat_num=1)
        else:
            raise ValueError("invalid test program type")
    else:
        if(test_program_type=="qft"):
            routing_result=hand_routing.gen_qft_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu)
        elif(test_program_type=="qaoa"):
            qpu_num = rack_num * qpu_per_rack
            total_qubits = qpu_num * qbit_per_qpu
            edges=generate_regular_graph(total_qubits, 3)
            routing_result=hand_routing.gen_qaoa_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,
                                                                edges=edges)
        elif(test_program_type=="rca"):
            routing_result=hand_routing.gen_rca_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,repeat_num=repeat_num)
        elif(test_program_type=="grover"):
            routing_result=hand_routing.gen_grover_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,repeat_num=repeat_num)
        elif(test_program_type=='xor'):
            routing_result=hand_routing.gen_xor_routing_result(rack_num=rack_num,qpu_per_rack=qpu_per_rack,qbit_per_qpu=qbit_per_qpu,repeat_num=1)
        else:
            raise ValueError("invalid test program type")
    crossEPR,interEPR=tools.count_EPR(routing_result=routing_result,qpu_mapping_result=qpu_mapping_result)
    file.write("routing_result: cross EPR:"+str(crossEPR)+' inter EPR:'+str(interEPR)+'\n')
    DAG = tools.gen_dag(routing_result=routing_result,qpu_connG_mapping_result=qpu_connG_mapping_result)
    crossEPR,interEPR=tools.count_DAG_EPR(DAG=DAG,connG=conn_G_with_qpu)
    if(auto_retry_length):
        retry_length=min(50,max(int(crossEPR/5+interEPR/50),1))
        shoot_gap=retry_length*4
    file.write("DAG: cross EPR:"+str(crossEPR)+' inter EPR:'+str(interEPR)+'\n')
    file.write("Scheduling start\n")
    ts=time()
    try:
        if(test_scheduler_type=='our'):
            s=Scheduler(connG=conn_G_with_qpu,DAG=DAG,commqbit_num=commqbit_num,cache_size=cache_size+commqbit_num,
                        reserve_size=cache_reserve_size,schedu_depth=schedu_depth,inter_time=inter_time,switch_time=switch_time,exter_time=exter_time,
                        split_mul=split_mul,shoot_num=20,shoot_gap=shoot_gap,retry_length=retry_length,retry_length_mul=2,
                        check_CAT_sTP=check_CAT_sTP,check_dTP=check_dTP,check_split_num=check_split_num)
            v=Validater(QPUs=s.QPUs,DAG=DAG)
            time_schedule,cross_pair,in_pair,post_in_pair,cross_wait_time,in_wait_time,retry_num,total_step,schedule_result_list=\
                s.run(look_ahead=look_ahead,join_map=join_map,split=split,ahead_split=True)
            v.run(final_QPUs=s.QPUs)
        elif(test_scheduler_type=='baseline_no_ahead'):
            s=Scheduler_baseline(connG=conn_G_with_qpu,DAG=DAG,commqbit_num=commqbit_num,cache_size=cache_size+commqbit_num,
                                 reserve_size=cache_reserve_size,inter_time=inter_time,switch_time=switch_time,exter_time=exter_time,
                                 check_CAT_sTP=check_CAT_sTP,check_dTP=check_dTP,check_split_num=check_split_num)
            v=Validater(QPUs=s.QPUs,DAG=DAG)
            time_schedule,cross_pair,in_pair,post_in_pair,cross_wait_time,in_wait_time,retry_num,total_step,schedule_result_list=\
                s.run(ahead_epr=False)
            v.run(final_QPUs=s.QPUs)
        to=time()
        file.write("Scheduling time:"+str(to-ts)+"\n")
        file.write("rack_num "+str(rack_num)+" qpu_per_rack "+str(qpu_per_rack)+" qbit_per_qpu "+str(qbit_per_qpu)+"\n")
        file.write("time_schedule "+str(time_schedule)+" cross_pair "+str(cross_pair)+" in_pair "+str(in_pair)+
              " post_in_pair "+str(post_in_pair)+"\n")
        file.write('cross_wait_time '+str(cross_wait_time)+' in_wait_time '+str(in_wait_time)+"\n")
        file.write('retry_num '+str(retry_num)+' total_step '+str(total_step)+"\n")
        file.write('thruput '+str((cross_pair+in_pair)/time_schedule)+' avg_wait_time '+
                   str((cross_wait_time+in_wait_time)/(cross_pair+in_pair+post_in_pair))+
                   ' avg_retry_overhead '+str(total_step/time_schedule)+"\n")
    except BaseException:
        to=time()
        file.write("test Error!,time:"+str(to-ts)+"\n")
        file.write(traceback.format_exc())
    print("test finish!")
    #print(schedule_result_list)
    #return 0




    # --- Add near the end of run_one(), before the final 'return 0' ---
    import json as _json  # add at top of file if not present

    # ... after scheduling section (inside try block or after) but before file.close()
    # Build metrics dict (guard against missing locals)
    metrics = {
        'time_schedule': locals().get('time_schedule', None),
        'cross_pair': locals().get('cross_pair', None),
        'in_pair': locals().get('in_pair', None),
        'post_in_pair': locals().get('post_in_pair', None),
        'cross_wait_time': locals().get('cross_wait_time', None),
        'in_wait_time': locals().get('in_wait_time', None),
        'retry_num': locals().get('retry_num', None),
        'total_step': locals().get('total_step', None),
        'throughput': None,
        'cross_EPR_cache_time': locals().get('cross_EPR_cache_time', None),
        'inter_EPR_cache_time': locals().get('inter_EPR_cache_time', None),
        'distill_pair': locals().get('distill_pair', None),
        'schedule_result_list_len': len(
            locals().get('schedule_result_list', [])) if 'schedule_result_list' in locals() else None
    }
    if metrics['time_schedule'] and metrics['cross_pair'] is not None and metrics['in_pair'] is not None:
        try:
            metrics['throughput'] = (metrics['cross_pair'] + metrics['in_pair']) / metrics['time_schedule']
        except Exception:
            metrics['throughput'] = None

    # Append JSON block to the same log file for easy parsing
    try:
        file.write("\nMETRICS_JSON:\n")
        file.write(_json.dumps(metrics) + "\n")
        file.flush()
    except Exception:
        # best-effort — don't crash
        file.write("\nMETRICS_JSON:WRITE_ERROR\n")
        file.flush()

    # Ensure file closed (if not already)
    try:
        file.close()
    except Exception:
        pass

    return metrics
# --- End patch ---
