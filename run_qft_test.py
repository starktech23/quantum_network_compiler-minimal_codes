# run_qft_test.py
from copy import deepcopy
import os, time, json
from run_hand_routing_one import run_one

def default_kwargs():
    return {
        'seed': 1,
        'test_mapper_type': 'baseline',
        'test_router_type': 'hand',
        'test_scheduler_type': 'our',        # or 'baseline_no_ahead'
        'test_program_type': 'qft',
        'test_conn_G_type': 'clos',          # 'fat_tree_L2' or 'fat_tree_L3'
        'rack_num': 4,
        'qpu_per_rack': 4,
        'qbit_per_qpu': 30,
        'outer_router_edge_weight': 8,
        'commqbit_num': 2,
        'rack_router_bsm_num': 4,
        'cache_size': 10,
        'cache_reserve_size': 2,
        'scheduling_reserve_size': 3,
        'schedu_depth': 10,
        'inter_time': 1,
        'switch_time': 10,
        'exter_time': 100,
        'split_mul': 2,
        'look_ahead': True,
        'join_map': True,
        'split': True,
        'prefix': 'QFT_single_run',
        'father_dir': './results_qft',
        'repeat_num': 1,
        'auto_retry_length': True,
        'retry_length': 50,
        'shoot_gap': 200,
        'check_CAT_sTP': True,
        'check_dTP': True,
        'check_split_num': True,
        'qec_program': False,
        'code_dist': 5
    }

if __name__ == '__main__':
    kw = default_kwargs()
    os.makedirs(os.path.join(kw['father_dir'], kw['prefix']), exist_ok=True)
    print("Running QFT using run_one() — writing logs to:", os.path.join(kw['father_dir'], kw['prefix']))
    metrics = run_one(deepcopy(kw))
    print("Run finished. Metrics:")
    print(json.dumps(metrics, indent=2))
