import re
import os
import ast
import matplotlib
from dataclasses import dataclass, field
from collections import defaultdict
MATCH_PARA = re.compile(r'(\w+)\s+([\d.]+)')
import matplotlib.pyplot as plt
# matches = MATCH_PARA.findall()
# dist = {key: float(value) for key, value in matches}
import math
from matplotlib.ticker import FixedLocator
@dataclass(frozen=True, eq= False)
class file_data:
    file_p : dict = field(init=False, repr = True)
    dic_l2 :dict= field(init=False, repr = True)
    dic_l3 : dict= field(init=False, repr = True)
    dic_l4 : dict = field(init=False, repr=True)
    metric_t: int= field(init=False, repr = True)
    metric_w: int = field(init=False, repr = True)
    epr : float = field(init= False, repr = True )

    def from_file(self,file_path):
        with open(file_path,'r') as fl:
            lines = fl.readlines()
        if len(lines) == 0:
            print('results not yet')
            raise ValueError("Data is still computing")
        l1 = lines[0]
        l2 = lines[-4]
        l3 = lines[-3]
        l4 = lines[-1]
        retry = lines[-2]
        file_para = ast.literal_eval(l1)
        object.__setattr__(self,"file_p", file_para)
        match_l2 = MATCH_PARA.findall(l2)
        dist_l2 = {key : float(value) for key, value in match_l2}
        match_l3 = MATCH_PARA.findall(l3)
        dist_l3 = {key: float(value) for key, value in match_l3}
        object.__setattr__(self, 'dic_l2', dist_l2)
        object.__setattr__(self, "dic_l3", dist_l3)
        match_l4 = MATCH_PARA.findall(l4)
        dist_l4 = {key: float(value) for key, value in match_l4}
        object.__setattr__(self,"dic_l4", dist_l4)
        match_retry = MATCH_PARA.findall(retry)
        dist_retry = {key: float(value) for key, value in match_retry}
        object.__setattr__(self,"dist_retry", dist_retry)
    def cal_metric(self):
        overhead = self.dic_l2['cross_pair'] + self.dic_l2['in_pair'] / 3 + self.dic_l2['post_in_pair'] * math.pow(0.7,int(self.file_p['split_mul'])-1) / 3
        object.__setattr__(self,'epr',overhead)
        # math.pow(0.7,int(match_split.group(1))-1) / 3

def process_files_by_seed(folder_path):
    seed_dict = defaultdict(list)
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            data_instance = file_data()
            data_instance.from_file(file_path)
            data_instance.cal_metric()
            seed = data_instance.file_p.get('seed')
            seed_dict[seed].append(data_instance)
    result = list(seed_dict.values())
    return result

def calculate_cross_sublist_averages(big_list):
    metric_sums = defaultdict(lambda: {'metric_t_sum': 0.0, 'metric_w_sum': 0.0,'epr_sum':0.0, 'count': 0, "retry_num": 0, 'retry_time':0, 'avg_retry_overhead':0,'cross':0,'in':0,'distill':0})
    for sublist in big_list:
        for instance in sublist:
            filtered_file_p = {k: v for k, v in instance.file_p.items() if k != 'seed'}
            # if 'baseline'
            file_p_key = frozenset(filtered_file_p.items())
            metric_sums[file_p_key]['metric_t_sum'] += instance.dic_l2['time_schedule']
            metric_sums[file_p_key]['metric_w_sum'] = instance.dic_l4['avg_wait_time']
            metric_sums[file_p_key]['epr_sum'] += instance.epr
            metric_sums[file_p_key]['count'] += 1
            metric_sums[file_p_key]['retry_num'] = instance.dist_retry['retry_num']
            metric_sums[file_p_key]['retry_time'] = instance.dist_retry['total_step']
            metric_sums[file_p_key]['avg_retry_overhead'] = instance.dic_l4['avg_retry_overhead']
            metric_sums[file_p_key]['cross'] = instance.dic_l2['cross_pair']
            metric_sums[file_p_key]['in'] = instance.dic_l2['in_pair']
            metric_sums[file_p_key]['distill'] = instance.dic_l2['post_in_pair']
    averages = []
    for file_p_key, values in metric_sums.items():
        avg_metric_t = values['metric_t_sum'] / values['count']
        avg_metric_w = values['metric_w_sum'] / values['count']
        epr = values['epr_sum'] / values['count']
        retry_num = values['retry_num']
        retry_time = values['retry_time']
        avg_retry_overhead = values['avg_retry_overhead']
        cross = values['cross']
        in_pair = values['in']
        distill = values['distill']
        # print( values['count'])
        averages.append({'file_p': dict(file_p_key), 'avg_metric_t': avg_metric_t, 'avg_metric_w': avg_metric_w, 'eproverhead':epr,'retry_num':retry_num,'retry_time':retry_time, 'avg_retry_overhead':avg_retry_overhead,'cross':cross,'in_pair':in_pair,'distill':distill })
    return averages

def classify_and_sort_averages_1(averages, eval_key, our = 0):
    # 按 'test_program_type' 分类
    classified_averages = defaultdict(list)
    for average in averages:
        program_type = average['file_p'].get('test_program_type')
        classified_averages[program_type].append(average)
    # 按 eval_key 进行排序
    sorted_classified_averages = {}
    for program_type, avg_list in classified_averages.items():
        # 使用 lambda 和 sorted 函数，根据 eval_key 对列表排序
        sorted_avg_list = sorted(avg_list, key=lambda x: x['file_p'].get(eval_key))
        s_refine = []
        if our == 0:
            for a in sorted_avg_list:
                # print(a['file_p']['test_conn_G_type'])
                if a['file_p']['test_scheduler_type'] == 'our':
                    s_refine.append(a)
        elif our == 1:
            for a in sorted_avg_list:
                # print(a['file_p']['test_program_type'])
                if a['file_p']['test_scheduler_type'] == 'baseline_no_ahead':
                    s_refine.append(a)
        sorted_classified_averages[program_type] = s_refine
    return sorted_classified_averages
def compute_dictionaries(data_path, eval, benchmark):
    big_list = process_files_by_seed(data_path)
    averages = calculate_cross_sublist_averages(big_list)
    result = classify_and_sort_averages_1(averages, eval)
    result_base = classify_and_sort_averages_1(averages, eval, our=1)
    
    diction_baseline = [[[], [], [], []], [[], [], [], []], [[], [], [], []]]
    diction_our = [[[], [], [], []], [[], [], [], []], [[], [], [], []]]
    for index, b in enumerate(benchmark):
        for a in result[b]:
            diction_our[0][index].append(a['avg_metric_t'])
            diction_our[1][index].append(a['avg_metric_w'])
            diction_our[2][index].append(a['eproverhead'])
        for aa in result_base[b]:
            diction_baseline[0][index].append(aa['avg_metric_t'])
            diction_baseline[1][index].append(aa['avg_metric_w'])
            diction_baseline[2][index].append(aa['eproverhead'])
    
    return diction_our, diction_baseline


def extract_data(diction,baseline=False):
    mct_data = [diction[0][0][0], diction[1][0][0], diction[2][0][12]]
    qft_data = [diction[0][1][0], diction[1][1][0], diction[2][1][9]]
    grover_data = [diction[0][2][0], diction[1][2][0], diction[2][2][13]]
    rca_data = [diction[0][3][0], diction[1][3][0], diction[2][3][9]]
    if baseline == True:
        mct_data = [diction[0][0][0], diction[1][0][0], 0]
        qft_data = [diction[0][1][0], diction[1][1][0], 0]
        grover_data = [diction[0][2][0], diction[1][2][0], 0]
        rca_data = [diction[0][3][0], diction[1][3][0], 0]
    return mct_data, qft_data, grover_data, rca_data


def classify_and_sort_averages_optimization_level(averages, eval_key):
    # 按 'test_program_type' 分类
    classified_averages = defaultdict(list)
    for average in averages:
        program_type = average['file_p'].get('test_program_type')
        classified_averages[program_type].append(average)
    # 按 eval_key 进行排序
    sorted_classified_averages = {}
    for program_type, avg_list in classified_averages.items():
        # 使用 lambda 和 sorted 函数，根据 eval_key 对列表排序
        s_refine = [None] * 8
        for i in avg_list:
            for a in avg_list:
                l = 0
                i1 = a['file_p'][eval_key[0]]
                i2 = a['file_p'][eval_key[1]]
                i3 = a['file_p'][eval_key[2]]
                if not i1 and not i2 and not i3:
                    s_refine[0]=a
                if i1 and not i2 and not i3:
                    s_refine[1] = a
                if not i1 and i2 and not i3:
                    s_refine[2] = a
                if not i1 and not i2 and i3:
                    s_refine[3] = a
                if i1 and i2 and not i3:
                    s_refine[4] = a
                if i1 and not i2 and i3:
                    s_refine[5] = a
                if not i1 and i2 and i3:
                    s_refine[6] = a
                if i1 and i2 and i3:
                    s_refine[7] = a
        sorted_classified_averages[program_type] = s_refine
    return sorted_classified_averages