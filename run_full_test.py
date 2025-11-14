from run_hand_routing_one import run_one
from multiprocessing import Pool
from copy import deepcopy
import time
import os
if __name__=='__main__':
    p = Pool(245)
    kwargs={}
    father_dir="rawdata_test_scheduler_type_"+time.asctime()
    for prefix in ["circuit_size","qpu_per_rack","cache_size","commqbit_num",
                   "rack_router_bsm_num","outer_router_edge_weight",'inter_time',
                   'exter_time','split_mul','test_conn_G_type','opt_test',
                   'schedu_depth_test','cross_in_rack_ratio','diff_retry_length_tests'
                   ,'check_reserve_test','qec_program']:
        if not os.path.exists(father_dir+"/"+prefix+"/"):
            os.makedirs(father_dir+"/"+prefix+"/")
    kwargs['test_mapper_type']='baseline'
    kwargs['test_router_type']='hand'
    kwargs['test_scheduler_type']='baseline_no_ahead'
    kwargs['test_program_type']='qft'
    kwargs['test_conn_G_type']='clos'
    kwargs['rack_num']=4
    kwargs['qpu_per_rack']=4
    kwargs['qbit_per_qpu']=30
    kwargs['commqbit_num']=2
    kwargs['cache_reserve_size']=2 # default=commqbit_num
    kwargs['outer_router_edge_weight']=8 # qpu_per_rack*commqbit_num
    kwargs['rack_router_bsm_num']=4  # qpu_per_rack*commqbit_num/2
    kwargs['cache_size']=10
    kwargs['scheduling_reserve_size']=3
    kwargs['schedu_depth']=10
    kwargs['inter_time']=1
    kwargs['switch_time']=10
    kwargs['exter_time']=100
    kwargs['split_mul']=2
    kwargs['look_ahead']=True
    kwargs['join_map']=True
    kwargs['split']=True
    kwargs['prefix']='circuit_size'
    kwargs['father_dir']=father_dir
    kwargs['seed']=45541
    kwargs['total_test_num']=1
    kwargs['repeat_num']=100
    kwargs['auto_retry_length']=True
    kwargs['retry_length']=50
    kwargs['shoot_gap']=200 # retry_length*4
    kwargs['check_CAT_sTP']=True
    kwargs['check_dTP']=True
    kwargs['check_split_num']=True
    kwargs['qec_program']=False
    kwargs['code_dist']=5
    default_kwargs=deepcopy(kwargs)

    for seed_iter in range(default_kwargs['total_test_num']):
        default_kwargs['seed']+=1
        for test_scheduler_type in ['baseline_no_ahead','our']:
            default_kwargs['test_scheduler_type']=test_scheduler_type
            for test_program_type in ['grover','rca','qft','xor', 'qaoa']:      # ['grover','rca','qft','xor', 'qaoa']
                if(test_program_type not in ['grover','rca'] and seed_iter!=0):
                    continue
                default_kwargs['test_program_type']=test_program_type
                kwargs=deepcopy(default_kwargs)
                
                kwargs['prefix']='circuit_size'
                for qbit_per_qpu,cache_size,scheduling_reserve_size in [(30,10,3),(38,12,3),(45,15,4)]:
                   kwargs['qbit_per_qpu']=qbit_per_qpu
                   kwargs['cache_size']=cache_size
                   kwargs['scheduling_reserve_size']=scheduling_reserve_size
                   print(kwargs)
                   p.apply_async(run_one, args=(deepcopy(kwargs),))
                kwargs=deepcopy(default_kwargs)

                kwargs['prefix']='qpu_per_rack'
                for qpu_per_rack in range(2,7):
                   kwargs['qpu_per_rack']=qpu_per_rack
                   kwargs['outer_router_edge_weight']=int(qpu_per_rack*kwargs['commqbit_num'])
                   kwargs['rack_router_bsm_num']=int(qpu_per_rack*kwargs['commqbit_num']/2)
                   print(kwargs)
                   p.apply_async(run_one, args=(deepcopy(kwargs),))
                kwargs=deepcopy(default_kwargs)

                kwargs['prefix']='rack_num'
                kwargs['qpu_per_rack']=3
                kwargs['qbit_per_qpu']=20
                kwargs['cache_size']=7
                for rack_num in [4,9,16]:
                   kwargs['rack_num']=rack_num
                   print(kwargs)
                   p.apply_async(run_one, args=(deepcopy(kwargs),))
                kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='test_conn_G_type'
                #kwargs['outer_router_edge_weight']=1
                #for test_conn_G_type,rack_num in [('clos',4),('fat_tree_L2',8),('fat_tree_L3',6)]:
                #    kwargs['test_conn_G_type']=test_conn_G_type
                #    kwargs['rack_num']=rack_num
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='qec_program'
                #kwargs['qec_program']=True
                #kwargs['code_dist']=5
                #kwargs['rack_num']=4
                #kwargs['qpu_per_rack']=4
                #kwargs['qbit_per_qpu']=4
                #kwargs['commqbit_num']=2
                #kwargs['cache_reserve_size']=2 # default=commqbit_num
                #kwargs['outer_router_edge_weight']=8 # qpu_per_rack*commqbit_num
                #kwargs['rack_router_bsm_num']=4  # qpu_per_rack*commqbit_num/2
                #kwargs['cache_size']=12
                #kwargs['repeat_num']=1
                #for schedu_depth in range(1,21):
                #    if(schedu_depth!=1 and test_scheduler_type!='our'):
                #        continue
                #    kwargs['schedu_depth']=schedu_depth
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='cross_in_rack_ratio'
                #kwargs['qbit_per_qpu']=45
                #kwargs['cache_size']=15
                #kwargs['scheduling_reserve_size']=4
                ##if('baseline' in test_scheduler_type):
                #for exter_time,switch_time in [(100,10),(0,10),(0,0)]:
                #    kwargs['exter_time']=exter_time
                #    kwargs['switch_time']=switch_time
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='cache_size'
                #for scheduling_reserve_size,cache_size in enumerate(list(range(3,26,1))+list(range(30,65,5))):
                #    kwargs['cache_size']=cache_size
                #    kwargs['scheduling_reserve_size']=scheduling_reserve_size
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='schedu_depth_test'
                ##if(test_scheduler_type=='our'):
                #for schedu_depth in range(1,21):
                #    if(schedu_depth!=1 and test_scheduler_type!='our'):
                #        continue
                #    kwargs['schedu_depth']=schedu_depth
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='commqbit_num'
                #for commqbit_num in range(1,7):
                #    kwargs['commqbit_num']=commqbit_num
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
# 
                #kwargs['prefix']='inter_time'
                #for inter_time in [1,2,4,5,6,8,10,20,40,60,80,100]:
                #    kwargs['inter_time']=inter_time
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs['inter_time']=10
#
                ## 5 10 15 20
                #kwargs['prefix']='exter_time'
                #for exter_time in [100,200,500,1000,1500,2000,2500,3000,3500,4000,4500,5000]:
                #    kwargs['exter_time']=exter_time
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='split_mul'
                #for split_mul in range(1,31):
                #    if(test_scheduler_type!='our' and split_mul!=1):
                #        continue
                #    kwargs['split_mul']=split_mul
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                # kwargs['prefix']='opt_test'
                # for look_ahead,join_map,split in [(False,False,False),(True,False,False),(False,True,False),
                #                                   (False,False,True),(False,True,True),(True,False,True),
                #                                   (True,True,False),(True,True,True)]:
                #     if(test_scheduler_type!='our' and (look_ahead,join_map,split)!=(False,False,False)):
                #         continue
                #     kwargs['look_ahead']=look_ahead
                #     kwargs['join_map']=join_map
                #     kwargs['split']=split
                #     print(kwargs)
                #     p.apply_async(run_one, args=(deepcopy(kwargs),))
                # kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='rack_router_bsm_num'
                #for rack_router_bsm_num in range(2,11):
                #    kwargs['rack_router_bsm_num']=rack_router_bsm_num
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='outer_router_edge_weight'
                #for outer_router_edge_weight in [1,2,4,8,16]:
                #    kwargs['outer_router_edge_weight']=outer_router_edge_weight
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
                #
                #kwargs['switch_time']=100 # Minimum time unit 0.01ms
                #kwargs['exter_time']=1000
#
                #kwargs['prefix']='cache_reserve_test'
                ##if(test_scheduler_type=='our'):
                #for cache_reserve_size in range(1,10):
                #    kwargs['cache_reserve_size']=cache_reserve_size
                #    print(kwargs)
                #    p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='diff_retry_length_tests'
                #kwargs['cache_size']=5
                #kwargs['auto_retry_length']=False
                #if(test_scheduler_type=='our'):
                #    for retry_length in [10,20,40,50,100]:
                #        for shoot_mul in [1,2,3,4,5,6]:
                #            kwargs['retry_length']=retry_length
                #            kwargs['shoot_gap']=retry_length*shoot_mul
                #            print(kwargs)
                #            p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)
#
                #kwargs['prefix']='check_reserve_test'# Best performance: 7.  5-6, also works with some reversal
                #for cache_size in range(5,11):
                #    kwargs['cache_size']=cache_size
                #    for check_CAT_sTP,check_dTP,check_split_num in [(True,True,True),(False,True,True),
                #                                                    (True,False,True),(False,False,True),
                #                                                    (True,True,False),(False,True,False),
                #                                                    (True,False,False),(False,False,False)]:
                #        kwargs['check_CAT_sTP']=check_CAT_sTP
                #        kwargs['check_dTP']=check_dTP
                #        kwargs['check_split_num']=check_split_num
                #        print(kwargs)
                #        p.apply_async(run_one, args=(deepcopy(kwargs),))
                #kwargs=deepcopy(default_kwargs)

    p.close()
    p.join()