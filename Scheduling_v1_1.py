import networkx as nx
import matplotlib.pyplot as plt
import random
from copy import deepcopy
import yaml
from networkx.readwrite import json_graph
#random.seed(1556)
def draw_G(G,nlables,elabes):
    random.seed(15)
    node_lables={}
    for i in G.nodes:
        nlist=[]
        for j in nlables:
            nlist.append(G.nodes[i][j])
        node_lables[i]=(i,nlist)
    edge_lables={}
    for i in G.edges:
        elist=[]
        for j in elabes:
            elist.append(G.edges[i][j])
        edge_lables[i]=elist
    pos=nx.shell_layout(G)
    plt.figure()
    nx.draw_networkx(G,pos=pos,with_labels=False)
    nx.draw_networkx_labels(G,pos=pos,labels=node_lables)
    nx.draw_networkx_edge_labels(G, pos=pos,edge_labels=edge_lables)
    plt.show()
class CommQbit:
    def __init__(self):
        self.endtime=0 #endtime=x before x busy, x free
        self.to_QPU=0
        self.to_commqbit=0
        self.path=[] # [rack_router(id,statei),edges[((n1,n2),statei)]]
    def print(self):
        print("endtime:",self.endtime," to_QPU:",self.to_QPU,
              " to_commqbit:",self.to_commqbit," path:",self.path)
    def inter_free(self,to_QPU,t):# have communication, destination QPU same
        return to_QPU==self.to_QPU and t<self.endtime , self.to_commqbit # edges->((n1,n2),statei)->(n1,n2)->n2
    def normal_free(self,t):
        return self.endtime<=t
class QPU:
    def __init__(self,id,commqbit_num=2,cache_size=10,reserve_size=2,
                check_CAT_sTP=True,check_dTP=True,check_split_num=True):
        self.id=id
        self.commqbits=[]
        self.cache_size=cache_size
        self.max_cache_size=cache_size
        self.reserve_size=reserve_size
        self.split_reserve=0
        self.check_CAT_sTP=check_CAT_sTP
        self.check_dTP=check_dTP
        self.check_split_num=check_split_num
        for _ in range(commqbit_num):
            self.commqbits.append(CommQbit()) 
        ###############
        self.aheadpairs=[]#[[to_qpu,endt]]，Only pairs generated during spare time are stored
    def print(self):
        print("id:",self.id," cache_size:",self.cache_size,"max_cache_size",self.max_cache_size,
                  " reserve_size:",self.reserve_size,"split_reserve",self.split_reserve)
        for i in self.commqbits:
            i.print()
    def cache_enough(self,is_front,is_split,is_teleport_sub):# Usage: 1. cache enough 2. free commqbits
        #if is_teleport and not is_split, then after max_cache_size-1 can do split_reserve 
        if(self.cache_size<=0):
            return False
        if(self.cache_size<=self.reserve_size and (not is_front) and self.check_CAT_sTP):
            return False
        if(is_teleport_sub and not is_split and self.check_dTP): 
            if(self.max_cache_size-1<self.split_reserve):
                return False
            if((not is_front) and self.max_cache_size-1-self.reserve_size<self.split_reserve):# Ensure not front split has enough space
                return False
        return True
    def normal_map_id(self,t):# return this qpu commqbit id
        for i in range(0,len(self.commqbits)):
            if(self.commqbits[i].normal_free(t=t)):
                return i
        return -1
    def join_map_id(self,to_QPU,t):# return this qpu+ outher qpu commqbit id
        for i in range(0,len(self.commqbits)):
            flag,id=self.commqbits[i].inter_free(t=t,to_QPU=to_QPU)
            if(flag):
                return i,id
        return -1,-1
    def get_comm_endt_path(self,id):
        return self.commqbits[id].endtime,self.commqbits[id].path
    def map(self,end_t,to_QPU,commqbit_id,is_teleport_sub,is_split,path,to_commqbit):
        self.cache_size-=1
        if(is_teleport_sub):
            self.max_cache_size-=1
        if(is_teleport_sub and is_split):# decrease the split_reserve on time to prevent cache not enough after reducing the max_cache_size
            self.split_reserve-=1
        commqbit=self.commqbits[commqbit_id]
        assert end_t>=commqbit.endtime
        commqbit.endtime=end_t
        commqbit.path=path
        commqbit.to_QPU=to_QPU
        commqbit.to_commqbit=to_commqbit
        assert self.max_cache_size>=self.cache_size
        assert self.max_cache_size>=self.split_reserve or not self.check_CAT_sTP or not self.check_dTP or not self.check_split_num 
        assert self.cache_size>=0
        assert self.split_reserve>=0 or not self.check_CAT_sTP or not self.check_dTP or not self.check_split_num 
    def free(self,t,is_front):# This function is intended to find the middle QPU of a split, so it does not involve teleport
        # only ensure has commqbits and cache space , not guarantee that max_cache_size or split_reserve meet the requirements
        if(not self.cache_enough(is_front=is_front,is_split=False,is_teleport_sub=False)):
            return False
        return self.normal_map_id(t=t)>=0
    def split_can_map(self,split_num,is_front):
        if(not self.check_split_num):
            return True
        if(is_front):
            self.split_reserve+split_num<=self.max_cache_size
        return self.split_reserve+split_num<=self.max_cache_size-self.reserve_size
    def map_aheadpair_to_qpu(self,end_t,to_QPU,commqbit_id,path,to_commqbit):
        self.aheadpairs.append([to_QPU,end_t])
        commqbit=self.commqbits[commqbit_id]
        assert end_t>=commqbit.endtime
        commqbit.endtime=end_t
        commqbit.path=path
        commqbit.to_QPU=to_QPU
        commqbit.to_commqbit=to_commqbit
        assert self.max_cache_size>=self.cache_size
        assert self.max_cache_size>=self.split_reserve or not self.check_CAT_sTP or not self.check_dTP or not self.check_split_num 
        assert self.cache_size>=0
        assert self.split_reserve>=0 or not self.check_CAT_sTP or not self.check_dTP or not self.check_split_num 
    def get_aheadpairs_id_endt(self,to_QPU):#Get the ID of the pre-generated pair
        for id,[to_qpu,endt] in enumerate(self.aheadpairs):
            if(to_QPU==to_qpu):
                return id,endt
        return -1,0
    def remove_aheadpairs(self,aheadpair=None):
        if(len(self.aheadpairs)==0):
            return None
        #aheadpairs:[[to_qpu,endt]]
        id=0
        if(aheadpair==None):# The pair furthest in the past from now
            min_t=self.aheadpairs[0][1]
            for i in range(len(self.aheadpairs)):
                if(self.aheadpairs[i][1]<min_t):
                    id=i
                    min_t=self.aheadpairs[i][1]
        else:#pair that matches the given record
            for i in range(len(self.aheadpairs)):
                if(self.aheadpairs[i]==aheadpair):
                    id=i
                    break
        aheadpair_record=self.aheadpairs.pop(id) # [to_qpu,endt]
        return aheadpair_record
    def map_with_aheadpairs(self,to_QPU,is_teleport_sub,is_split):
        pair_id,pair_endt=self.get_aheadpairs_id_endt(to_QPU=to_QPU)
        if(pair_id>=0):
            self.aheadpairs.pop(pair_id)
            # same as normal map
            self.cache_size-=1
            if(is_teleport_sub):
                self.max_cache_size-=1
            if(is_teleport_sub and is_split):# decrease the split_reserve on time to prevent cache not enough after reducing the max_cache_size
                self.split_reserve-=1
            return pair_endt
        return -1
    def aheadpairs_full(self):
        return self.cache_size>0 and len(self.aheadpairs)>=self.cache_size
    def free_gen_aheadpairs(self,t):
        return len(self.aheadpairs)<self.cache_size and self.free(t=t,is_front=True)
class QPUS:
    def __init__(self,qpu_list:list[int],commqbit_num,cache_size,reserve_size,check_CAT_sTP,check_dTP,check_split_num):
        self.QPUs={}
        for i in qpu_list:
            self.QPUs[i]=QPU(id=i,commqbit_num=commqbit_num,cache_size=cache_size,reserve_size=reserve_size,
                                    check_CAT_sTP=check_CAT_sTP,check_dTP=check_dTP,check_split_num=check_split_num)
    def free_cache(self,commpair):
        qpu1,qpu2=commpair
        self.QPUs[qpu1].cache_size+=1
        self.QPUs[qpu2].cache_size+=1
    def free_reserve(self,commpair):
        qpu1,qpu2=commpair
        self.QPUs[qpu1].split_reserve-=1
        self.QPUs[qpu2].split_reserve-=1
    def teleport_update(self,commpair,is_split):
        qpu1,qpu2=commpair
        self.QPUs[qpu1].cache_size+=1
        self.QPUs[qpu2].cache_size-=1
        self.QPUs[qpu1].max_cache_size+=1# Increase at release
        if(is_split):# is split node
            self.QPUs[qpu2].split_reserve+=1 # decreased before
    def cache_enough(self,commpair,is_front,is_split,is_teleport_sub):
        flag0=self.QPUs[commpair[0]].cache_enough(is_front=is_front,is_split=is_split,is_teleport_sub=False)
        if(not flag0):
            return False
        flag1=self.QPUs[commpair[1]].cache_enough(is_front=is_front,is_split=is_split,is_teleport_sub=is_teleport_sub)
        return flag1
    def join_map_flag_id(self,commpair,t):
        commqbits_id=self.QPUs[commpair[0]].join_map_id(to_QPU=commpair[1],t=t)
        return commqbits_id[0]>=0 and commqbits_id[1]>=0,commqbits_id
    def get_comm_endt_path(self,commpair,commqbits_id):
        return self.QPUs[commpair[0]].get_comm_endt_path(id=commqbits_id[0])
    def map(self,commpair,end_t,commqbits_id,is_teleport_sub,is_split,path):
        self.QPUs[commpair[0]].map(end_t=end_t,to_QPU=commpair[1],commqbit_id=commqbits_id[0],is_teleport_sub=False
                                        ,is_split=is_split,path=path,to_commqbit=commqbits_id[1])
        self.QPUs[commpair[1]].map(end_t=end_t,to_QPU=commpair[0],commqbit_id=commqbits_id[1],is_teleport_sub=is_teleport_sub
                                        ,is_split=is_split,path=path,to_commqbit=commqbits_id[0])
    def normal_map_flag_id(self,commpair,t):
        id0=self.QPUs[commpair[0]].normal_map_id(t=t)
        if(id0<0):
            return False,(-1,-1)
        id1=self.QPUs[commpair[1]].normal_map_id(t=t)
        return id1>=0,(id0,id1)
    def reserve_QPU_enough(self,QPU_count,is_front):# Check if split is possible and attempt to retain the QPU
        for i in QPU_count:
            if(not self.QPUs[i].split_can_map(split_num=QPU_count[i],is_front=is_front)):
                return False
        return True
    def reserve_QPU(self,QPU_count):# reserve split QPU
        for i in QPU_count:
            self.QPUs[i].split_reserve+=QPU_count[i]
    def free(self,commpair,t,is_front):
        comm_qpu0_free=self.QPUs[commpair[0]].free(t=t,is_front=is_front)
        comm_qpu1_free=self.QPUs[commpair[1]].free(t=t,is_front=is_front)
        return comm_qpu0_free,comm_qpu1_free
    def rack_free_qpu_id(self,t,rack_qpu,is_front):
        for i in rack_qpu:
            if(i in self.QPUs and self.QPUs[i].free(t=t,is_front=is_front)):
                return i
        return -1
    def print_QPU(self):
        for i in self.QPUs:
            self.QPUs[i].print()
    def map_aheadpair_to_qpu(self,end_t,commpair,commqbits_id,path):
        self.QPUs[commpair[0]].map_aheadpair_to_qpu(end_t=end_t,to_QPU=commpair[1],commqbit_id=commqbits_id[0],
                                                    path=path,to_commqbit=commqbits_id[1])
        self.QPUs[commpair[1]].map_aheadpair_to_qpu(end_t=end_t,to_QPU=commpair[0],commqbit_id=commqbits_id[1],
                                                    path=path,to_commqbit=commqbits_id[0])
    def map_with_aheadpairs(self,commpair,end_t,commqbits_id,is_teleport_sub,is_split,path):
        QPU0,QPU1=self.QPUs[commpair[0]],self.QPUs[commpair[1]]
        end_t0=QPU0.map_with_aheadpairs(to_QPU=commpair[1],is_teleport_sub=False,is_split=is_split)
        if(end_t0>=0):
            end_t1=QPU1.map_with_aheadpairs(to_QPU=commpair[0],is_teleport_sub=is_teleport_sub,is_split=is_split)
            assert end_t0==end_t1
            return end_t0
        self.map(commpair=commpair,end_t=end_t,commqbits_id=commqbits_id,is_teleport_sub=is_teleport_sub
                 ,is_split=is_split,path=path)
        while(QPU0.aheadpairs_full()):
            record=QPU0.remove_aheadpairs(aheadpair=None)
            QPU_to=self.QPUs[record[0]]
            record[0]=commpair[0]
            QPU_to.remove_aheadpairs(aheadpair=record)
        while(QPU1.aheadpairs_full()):
            record=QPU1.remove_aheadpairs(aheadpair=None)
            QPU_to=self.QPUs[record[0]]
            record[0]=commpair[1]
            QPU_to.remove_aheadpairs(aheadpair=record)
        return end_t
    def get_free_gen_aheadpairs_qpu_list(self,t):
        free_list=[]
        for qpu_id in self.QPUs.keys():
            if(self.QPUs[qpu_id].free_gen_aheadpairs(t=t)):
                free_list.append(qpu_id)
        return free_list
class CacheDAG:
    def __init__(self,DAG):
        self.DAG=deepcopy(DAG)# node:count,is_teleport,info,commpairs,teleport_sub_flag
        for i in self.DAG.nodes:
            self.DAG.nodes[i]["count"]=1
            self.DAG.nodes[i]["commpairs"]=[[self.DAG.nodes[i]["info"],1,0]]#[(commpair),count,start_distill_flag]
            is_teleport=self.DAG.nodes[i]["is_teleport"]
            self.DAG.nodes[i]["teleport_sub_flag"]=is_teleport
            self.DAG.nodes[i]['start_end_cache_time_sum']=[[0,0],[0,0]] #[cross[start,end],inter[...]]
            ####
            self.DAG.nodes[i]["teleport_test"]=[0,0]
    def update(self,node:int,map_commpair:tuple[int,int],QPUs:QPUS,t:int,connG):
        FIFO=[]
        G=self.DAG
        G.nodes[node]["count"]-=1
        is_inter=connG.pair_is_inter(commpair=map_commpair)
        G.nodes[node]['start_end_cache_time_sum'][is_inter][0]+=t # Start waiting in the cache
        if(G.nodes[node]["count"]==0 and len(list(G.predecessors(node)))==0):
            FIFO.append(node)
        if(self.is_split(id=node)):
            for id,[commpair,count,start_distill] in enumerate(G.nodes[node]["commpairs"]):
                if(commpair==map_commpair):
                    break
            if(count>1 and start_distill==0 ): # count>1 distill and not start distill, first pair doesn't free cache
                G.nodes[node]["commpairs"][id][1]-=1 # count -1
                G.nodes[node]["commpairs"][id][2]=1  # set flag
            elif(start_distill==1):# start distill, free cache
                QPUs.free_cache(commpair=commpair)
                is_inter=connG.pair_is_inter(commpair=commpair)
                G.nodes[node]['start_end_cache_time_sum'][is_inter][1]+=t # end wait in cache and been used
                if(count==1): # last pair, split_reserve-1
                    QPUs.free_reserve(commpair=commpair)
                G.nodes[node]["commpairs"][id][1]-=1
        update_total_epr_cache_time=[0,0] # cross,inter
        while(len(FIFO)>0):
            node=FIFO.pop(0)
            for commpair,count,_ in G.nodes[node]["commpairs"]:
                QPUs.free_cache(commpair=commpair)
                is_inter=connG.pair_is_inter(commpair=commpair)
                G.nodes[node]['start_end_cache_time_sum'][is_inter][1]+=t # end wait in cache and been used
                assert count<=1
            if(self.is_split(id=node)):# is split node
                for commpair,_,_ in G.nodes[node]["commpairs"]:
                    QPUs.free_reserve(commpair=commpair)
            if(G.nodes[node]["is_teleport"]):# direction: qpu1->qpu2
                QPUs.teleport_update(commpair=G.nodes[node]["info"],
                                     is_split=self.is_split(id=node))
                assert G.nodes[node]["teleport_test"][1]==1
            succ=list(G.successors(node))
            update_total_epr_cache_time[0]+=\
                G.nodes[node]['start_end_cache_time_sum'][0][1]-G.nodes[node]['start_end_cache_time_sum'][0][0]
            update_total_epr_cache_time[1]+=\
                G.nodes[node]['start_end_cache_time_sum'][1][1]-G.nodes[node]['start_end_cache_time_sum'][1][0]
            G.remove_node(node)
            for i in succ:
                if(G.nodes[i]["count"]==0 and len(list(G.predecessors(i)))==0):
                    FIFO.append(i)
        return update_total_epr_cache_time
    def split(self,id,commpairs):
        self.DAG.nodes[id]["commpairs"]=commpairs
        self.DAG.nodes[id]["count"]=0
        for _,count,_ in commpairs:
            self.DAG.nodes[id]["count"]+=count
    def can_split(self,id):
        return len(self.DAG.nodes[id]["commpairs"])==1
    def is_split(self,id):
        return len(self.DAG.nodes[id]["commpairs"])>1
    def test_teleport_sub_flag(self,id,commpair):
        opair=self.DAG.nodes[id]["info"]
        flag=self.DAG.nodes[id]["teleport_sub_flag"]
        if(flag and commpair[1]==opair[1]):
            self.DAG.nodes[id]["teleport_test"][0]+=1
        return flag and commpair[1]==opair[1]
    def clear_teleport_sub_flag(self,id):
        self.DAG.nodes[id]["teleport_sub_flag"]=False
        self.DAG.nodes[id]["teleport_test"][1]+=1
    def get_pair_info(self,id):
        return self.DAG.nodes[id]["info"],self.DAG.nodes[id]["is_teleport"]
    def print_split(self):
        for node in self.DAG.nodes:
            node_data=self.DAG.nodes[node]
            if(len(node_data["commpairs"])>1):
                print("node",node,"count",node_data["count"],"info",node_data["info"],
                          "is_teleport",node_data["is_teleport"],"commpairs",node_data["commpairs"])
    def print(self):
        print("cacheDAG")
        draw_G(self.DAG,["count","info","is_teleport","commpairs","teleport_sub_flag"],[])
class MapDAG:
    def __init__(self,DAG,schedu_depth=3):
        self.DAG=deepcopy(DAG)# node:origin_id, info
        self.schedu_depth=schedu_depth
        self.max_id=0
        for i in self.DAG.nodes:
            self.DAG.nodes[i]["origin_id"]=i
            self.DAG.nodes[i]['depth']=0
            self.max_id=max(i,self.max_id)
    def update(self, del_node=None):
        G=self.DAG
        depth=self.schedu_depth
        if(del_node!=None):# delete node
            succ,pred=list(G.successors(del_node)),list(G.predecessors(del_node))
            G.remove_node(del_node)
            for i in pred:
                for j in succ:
                    G.add_edge(*(i,j))
        FIFO=[]
        #change_num=0
        node_deg={}# Get all nodes with no in edges
        for node in G.nodes:
            G.nodes[node]['depth']=0
            node_deg[node]=len(list(G.predecessors(node)))
            if(node_deg[node]==0):
                FIFO.append(node)
        ret_list=[]
        for _ in range(depth+1): 
            ret_list.append([])
        while(len(FIFO)>0):
            node=FIFO.pop(0)
            #change_num+=1
            node_depth=1
            pred=list(G.predecessors(node))
            for i in pred:# Calculate the current depth
                node_depth=max(node_depth,G.nodes[i]['depth']+1)
            G.nodes[node]['depth']=node_depth
            if(node_depth<depth):
                for i in list(G.successors(node)):# add been affected node
                    node_deg[i]-=1
                    if(node_deg[i]==0):
                        FIFO.append(i)
            if(node_depth<=depth):# add nodes where the depth meets the requirements
                ret_list[node_depth].append(node)
        ret_list.pop(0)
        #print("change_num",change_num)
        return ret_list# ret_list[0] depth=1
    def get_oid_pair(self,map_id):
        commpair=self.DAG.nodes[map_id]["info"]
        origin_id=self.DAG.nodes[map_id]["origin_id"]
        return origin_id,commpair
    def split_node(self,old_id,mqpu,node_mul):
        lnodes,rnodes=[],[]
        origin_id=self.DAG.nodes[old_id]["origin_id"]
        depth=self.DAG.nodes[old_id]["depth"]
        is_teleport=self.DAG.nodes[old_id]["is_teleport"]
        lqpu,rqpu=self.DAG.nodes[old_id]["info"]
        for _ in range(node_mul[0]):
            self.max_id+=1
            self.DAG.add_node(self.max_id,info=(lqpu,mqpu),origin_id=origin_id,depth=depth,is_teleport=is_teleport)
            lnodes.append(self.max_id)
        for _ in range(node_mul[1]):
            self.max_id+=1
            self.DAG.add_node(self.max_id,info=(mqpu,rqpu),origin_id=origin_id,depth=depth,is_teleport=is_teleport)
            rnodes.append(self.max_id)
        succ,pred=list(self.DAG.successors(old_id)),list(self.DAG.predecessors(old_id))
        for i in (lnodes+rnodes):
            for j in pred:
                self.DAG.add_edge(*(j,i))
            for j in succ:
                self.DAG.add_edge(*(i,j))
        self.DAG.remove_node(old_id)
        return lnodes,rnodes
    def print(self):
        print("mapDAG")
        draw_G(self.DAG,["origin_id","info","is_teleport"],[])
class ConnG:
    def __init__(self,connG):
        # connG:edge: [0,0,0] state, node: is_router,[0,0] state 
        self.G=deepcopy(connG)
        self.t=0
        for i in self.G.edges:
            state_len=len(self.G.edges[i]["state"])
            self.G.edges[i]["state"]=[0]*state_len
        for node in self.G.nodes:
            state_len=len(self.G.nodes[node]["state"])
            self.G.nodes[node]["state"]=[0]*state_len
    def dist_func(self,u,v,attr):
        for i in attr["state"]:
            if(i<=self.t):
                return 1
        return float('+inf')
    def pair_is_inter(self,commpair):
        return list(self.G.neighbors(commpair[0]))==list(self.G.neighbors(commpair[1]))
    def rack_router_free(self,rack_router,t):
        for id,state in enumerate(self.G.nodes[rack_router]["state"]):
            if(state<=t):
                return id
        return -1
    def get_flag_path(self,commpair,t): # flag:has_path? path:the path from sqpu to eqpu
        self.t=t
        parent=(list(self.G.neighbors(commpair[0]))[0],list(self.G.neighbors(commpair[1]))[0])
        freeid0=self.rack_router_free(rack_router=parent[0],t=t)
        freeid1=self.rack_router_free(rack_router=parent[1],t=t)
        if(freeid0<0  and freeid1<0 ):
            return False,[]
        length, path = nx.single_source_dijkstra(G=self.G, source=commpair[0],target=commpair[1],weight=self.dist_func)
        ret_list=[]
        if(length==float('+inf')):
            return False,[]
        if(freeid0>=0):
            rack_router_change=(parent[0],freeid0)
        else:
            rack_router_change=(parent[1],freeid1)
        ret_list.append(rack_router_change)
        ret_path=[]
        for i in range(0,len(path)-1):
            id_i=path[i]
            id_i1=path[i+1]
            state_list=self.G.edges[id_i,id_i1]["state"]
            for j in range(0,len(state_list)):
                if(state_list[j]<=t):
                    ret_path.append( ((id_i,id_i1) , j) )
                    break
        ret_list.append(ret_path)
        return True,ret_list
    def update_rack_router(self,rack_router_change,end_t):
        id,stateid=rack_router_change
        assert end_t>=self.G.nodes[id]['state'][stateid]
        self.G.nodes[id]['state'][stateid]=end_t
    def update(self,path,end_t):
        rack_router_change=path[0]
        path_change=path[1]
        self.update_rack_router(rack_router_change=rack_router_change,end_t=end_t)
        for (edge,stateid) in path_change:
            assert end_t>=self.G.edges[edge]["state"][stateid]
            self.G.edges[edge]["state"][stateid]=end_t
    def between_rack_free(self,commpair,t):
        self.t=t
        parent=(list(self.G.neighbors(commpair[0]))[0],list(self.G.neighbors(commpair[1]))[0])
        freeid0=self.rack_router_free(rack_router=parent[0],t=t)
        freeid1=self.rack_router_free(rack_router=parent[1],t=t)
        if(freeid0<0 and freeid1<0 ):
            return False
        length, path = nx.single_source_dijkstra(G=self.G, source=parent[0],target=parent[1],weight=self.dist_func)
        return length!=float('+inf')
    def get_rack_qpu(self,qpu_id):
        parent=list(self.G.neighbors(qpu_id))[0]
        return self.G.neighbors(parent)
    def print(self):
        print("connG")
        draw_G(self.G,["state"],["state"])
class Scheduler_snapshoot:
    def __init__(self,scheduler):
        self.cacheDAG       =deepcopy(scheduler.cacheDAG)
        self.mapDAG         =deepcopy(scheduler.mapDAG)
        self.connG          =deepcopy(scheduler.connG)
        self.QPUs           =deepcopy(scheduler.QPUs)
        self.event_list     =deepcopy(scheduler.event_list)
        self.schedule_result_list  =deepcopy(scheduler.schedule_result_list)
        self.t              =scheduler.t
        self.cross_pair,self.inter_pair,self.distill_pair=scheduler.cross_pair,scheduler.inter_pair,scheduler.distill_pair
        self.inter_EPR_cache_time,self.cross_EPR_cache_time=scheduler.inter_EPR_cache_time,scheduler.cross_EPR_cache_time
    def restore(self,scheduler):
        scheduler.cacheDAG      =self.cacheDAG  
        scheduler.mapDAG        =self.mapDAG    
        scheduler.connG         =self.connG     
        scheduler.QPUs          =self.QPUs      
        scheduler.event_list    =self.event_list
        scheduler.schedule_result_list =self.schedule_result_list
        scheduler.t             =self.t         
        scheduler.cross_pair,scheduler.inter_pair,scheduler.distill_pair=self.cross_pair,self.inter_pair,self.distill_pair
        scheduler.inter_EPR_cache_time,scheduler.cross_EPR_cache_time=self.inter_EPR_cache_time,self.cross_EPR_cache_time
class Event:
    def __init__(self,start_t=0,end_t=0,dag_id=0,map_commpair=(0,0)):
        self.start_t=start_t
        self.end_t=end_t
        self.dag_id=dag_id# id field in cache DAG's node
        self.map_commpair=map_commpair# commpair field in map DAG'node 
    def print(self):
        print("end_t: ",self.end_t," dag_id:",self.dag_id," map_commpair:",self.map_commpair)
class Scheduler:
    def __init__(self,connG,DAG,commqbit_num=2,cache_size=10,reserve_size=2,schedu_depth=3,
                 inter_time=1,switch_time=10,exter_time=100,split_mul=2,
                 shoot_num=20,shoot_gap=100,retry_length=40,retry_length_mul=2,
                 check_CAT_sTP=True,check_dTP=False,check_split_num=True):
        # connG:edge field: [0,0,0,...] state, node field: is_router. DAG node field: info(communication qpu pairs), is_teleport
        # reserve_size:number of qubits needed for execution at a layer less than reserve_size, 
        # need DAG contain layer  information to determine which layer the current node belongs to
        self.cacheDAG=CacheDAG(DAG=DAG)# upate will change QPU status
        self.mapDAG=MapDAG(DAG=DAG,schedu_depth=schedu_depth)
        self.connG=ConnG(connG=connG)
        # self.QPUs=None
        self.event_list=[[]]
        self.inter_time=inter_time
        self.switch_time=switch_time
        self.exter_time=exter_time
        self.t=1
        self.split_mul=split_mul
        self.is_normal_state=True
        self.snapshoots=[]
        self.shoot_num=shoot_num
        self.shoot_gap=shoot_gap
        self.retry_length=retry_length
        self.min_retry_length=retry_length
        self.retry_length_mul=retry_length_mul
        self.retry_base_step_count=0
        self.max_t=self.t
        self.cross_pair,self.inter_pair,self.distill_pair=0,0,0
        self.inter_EPR_cache_time,self.cross_EPR_cache_time=0,0
        self.retry_num=0
        self.total_step=self.t
        self.schedule_result_list=[]
        qpu_list=[]
        for i in connG.nodes:
            if(not connG.nodes[i]["is_router"]):
                qpu_list.append(i)
        self.QPUs=QPUS(qpu_list=qpu_list,commqbit_num=commqbit_num,cache_size=cache_size,reserve_size=reserve_size,
                            check_CAT_sTP=check_CAT_sTP,check_dTP=check_dTP,check_split_num=check_split_num)
        self.snapshoots.append(Scheduler_snapshoot(scheduler=self))
        # print("finish init!")
    def push_event(self,event):
        gap=event.end_t-self.t
        while(len(self.event_list)<gap+1):
            self.event_list.append([])
        self.event_list[gap].append(event)
    def save_schedule(self,event:Event):
        opair,is_teleport=self.cacheDAG.get_pair_info(id=event.dag_id)
        pair_type=''
        if(is_teleport):
            pair_type+='T'
        else:
            pair_type+='C'
        map_p=event.map_commpair
        if((opair[0]==map_p[0] and opair[1]==map_p[1]) or (opair[0]==map_p[1] and opair[1]==map_p[0])):
            pair_type+='O'
        else:
            pair_type+='S'
        self.schedule_result_list.append([pair_type,opair,map_p,event.start_t,event.end_t])
    def handle_event(self):
        events=self.event_list[0]
        have_event=len(events)>0
        while(len(events)>0):
            event=events.pop(0)
            self.save_schedule(event=event)
            dag_id=event.dag_id
            map_commpair=event.map_commpair
            cross_cache,inter_cache=\
                self.cacheDAG.update(node=dag_id,map_commpair=map_commpair,QPUs=self.QPUs,t=self.t,connG=self.connG)
            self.inter_EPR_cache_time+=inter_cache
            self.cross_EPR_cache_time+=cross_cache
        return have_event
    def map_mapdag_node(self,map_id,is_front,join_map):
        origin_id,commpair=self.mapDAG.get_oid_pair(map_id=map_id)
        is_teleport_sub=self.cacheDAG.test_teleport_sub_flag(id=origin_id,commpair=commpair)
        is_split=self.cacheDAG.is_split(id=origin_id)
        is_inter=self.connG.pair_is_inter(commpair=commpair)
        if(is_inter):
            end_t=self.t+self.switch_time+self.inter_time
        else:
            end_t=self.t+self.switch_time+self.exter_time
        pair_cache_enough=self.QPUs.cache_enough(commpair=commpair,is_front=is_front,is_split=is_split,is_teleport_sub=is_teleport_sub)
        if(not pair_cache_enough):
            #print("f1")
            #print(commpair,origin_id)
            return False
        if(is_inter and join_map):# try join map
            flag,commqbits_id=self.QPUs.join_map_flag_id(commpair=commpair,t=self.t)
            if(flag):
                end_t,path=self.QPUs.get_comm_endt_path(commpair=commpair,commqbits_id=commqbits_id)
                end_t+=self.inter_time
                if(is_teleport_sub):
                    self.cacheDAG.clear_teleport_sub_flag(id=origin_id)
                self.QPUs.map(end_t=end_t,commpair=commpair,commqbits_id=commqbits_id,is_teleport_sub=is_teleport_sub
                                               ,is_split=is_split,path=path)
                self.connG.update(path=path,end_t=end_t)
                self.push_event(Event(start_t=self.t,end_t=end_t,dag_id=origin_id,map_commpair=commpair))
                if(not is_split and is_inter):
                    self.inter_pair+=1
                if(origin_id%1000==0):
                    print("join map origin_id: ",origin_id,"map_id: ",map_id)
                return True
        path_flag,path=self.connG.get_flag_path(commpair=commpair,t=self.t)
        # try normal map
        if(not path_flag):
            #print("f2")
            #print(commpair,origin_id)
            return False
        flag,commqbits_id=self.QPUs.normal_map_flag_id(commpair=commpair,t=self.t)
        if(not flag):
            #print("f3")
            #print(commpair,origin_id)
            return False
        if(is_teleport_sub):
            self.cacheDAG.clear_teleport_sub_flag(id=origin_id)
        # add path update
        self.QPUs.map(end_t=end_t,commpair=commpair,commqbits_id=commqbits_id,is_teleport_sub=is_teleport_sub
                                               ,is_split=is_split,path=path)
        self.push_event(Event(start_t=self.t,end_t=end_t,dag_id=origin_id,map_commpair=commpair))
        self.connG.update(path=path,end_t=end_t)
        if(not is_split and is_inter):
            self.inter_pair+=1
        if(not is_inter):
            self.cross_pair+=1
        if(origin_id%1000==0):
            print("normal map origin_id: ",origin_id,"map_id: ",map_id)
        return True
    
    def split(self,map_id,is_front):# return exterpair, after return cross-rack communication should start immediately
        origin_id,commpair=self.mapDAG.get_oid_pair(map_id=map_id)
        is_inter=self.connG.pair_is_inter(commpair=commpair)
        between_free=self.connG.between_rack_free(commpair=commpair,t=self.t)
        cache_can_split=self.cacheDAG.can_split(id=origin_id)
        #is_teleport_sub=self.cacheDAG.test_teleport_sub_flag(id=origin_id,commpair=commpair) # for debug, no real use
        if(is_inter or not between_free or not cache_can_split):
            return False,None
        rack0=self.connG.get_rack_qpu(qpu_id=commpair[0])
        rack1=self.connG.get_rack_qpu(qpu_id=commpair[1])
        fqpu0=self.QPUs.rack_free_qpu_id(rack_qpu=rack0,t=self.t,is_front=is_front)
        fqpu1=self.QPUs.rack_free_qpu_id(rack_qpu=rack1,t=self.t,is_front=is_front)
        comm_qpu0_free,comm_qpu1_free=self.QPUs.free(commpair=commpair,t=self.t,is_front=is_front)
        # it is possible for both QPUs to be free. This is caused by the previous split, 
        # which resulted in max_cache_size and split_reserve not meeting size requirements
        
        if((not comm_qpu0_free and fqpu0<0) or  (not comm_qpu1_free and fqpu1<0) or (comm_qpu0_free and comm_qpu1_free)):
            return False,None
        commpairs=[[commpair,1,0]]#-1 position is cross-rack communication
        if(not comm_qpu0_free):
            tempair0,tempcount0,_=commpairs.pop(-1)
            commpairs.append([(tempair0[0],fqpu0),self.split_mul*tempcount0,0])
            commpairs.append([(fqpu0,tempair0[1]),tempcount0,0])
            assert tempcount0==1
        if(not comm_qpu1_free):
            tempair1,tempcount1,_=commpairs.pop(-1)
            commpairs.append([(fqpu1,tempair1[1]),self.split_mul*tempcount1,0])
            commpairs.append([(tempair1[0],fqpu1),tempcount1,0])
            assert tempcount1==1
        def get_split_QPU_count(commpairs):
            QPU_count={}
            for (qpu1,qpu2),count,_ in commpairs:
                if(qpu1 not in QPU_count):
                    QPU_count[qpu1]=0
                if(qpu2 not in QPU_count):
                    QPU_count[qpu2]=0
                QPU_count[qpu1]+=min(2,count) # >=2:distill,2 ==1 no distill,1
                QPU_count[qpu2]+=min(2,count)
            return QPU_count
        QPU_count=get_split_QPU_count(commpairs=commpairs)
        if(not self.QPUs.reserve_QPU_enough(QPU_count=QPU_count,is_front=is_front)):
            return False,None
        exter_id=map_id
        if(not comm_qpu0_free):
            exter_id=self.mapDAG.split_node(old_id=exter_id,mqpu=fqpu0,node_mul=(self.split_mul*tempcount0,tempcount0))
            exter_id=exter_id[1][0]
            self.distill_pair+=1
        if(not comm_qpu1_free):
            exter_id=self.mapDAG.split_node(old_id=exter_id,mqpu=fqpu1,node_mul=(tempcount1,self.split_mul*tempcount1))
            exter_id=exter_id[0][0]
            self.distill_pair+=1
        self.QPUs.reserve_QPU(QPU_count=QPU_count)
        self.cacheDAG.split(id=origin_id,commpairs=commpairs)
        # print("split",origin_id,commpairs)
        return True,exter_id
    def step(self):
        while(len(self.event_list)>0 and len(self.event_list[0])==0):
            self.t+=1
            self.total_step+=1
            self.event_list.pop(0)
            if(self.t%self.shoot_gap==0 and self.is_normal_state):
                self.snapshoots.append(Scheduler_snapshoot(scheduler=self))
                while(len(self.snapshoots)>self.shoot_num):
                    self.snapshoots.pop(1)
        if(not self.is_normal_state):
            self.retry_base_step_count+=1
            #print(self.retry_base_step_count,self.retry_length)
            if(self.retry_base_step_count>=self.retry_length):
                print("normal try!")
                self.is_normal_state=True
                self.retry_base_step_count=0
    def restore(self):
        if(len(self.snapshoots)>1):
            snapshoot=self.snapshoots.pop(-1)
        else:
            snapshoot=deepcopy(self.snapshoots[0])
        snapshoot.restore(scheduler=self)
    def run(self,look_ahead=False,join_map=False,split=False,ahead_split=False):
        #self.print_QPU()
        #print("start running!")
        mapDAGnode=None
        map_list=[[-1]]#dummy
        while(len(map_list[0])>0):
            #print("start order!")
            map_list=self.mapDAG.update(del_node=None)
            #print("order Ok!")
            print(self.t,map_list)
            while(len(self.event_list)>0):
                t_can_map=True
                while(t_can_map):
                    t_can_map=False
                    for i in range(0,len(map_list)):
                        is_front= i==0
                        break_flag=False
                        if((not look_ahead or not self.is_normal_state) and i>0):
                            break
                        for mapDAGnode in map_list[i]:
                            map_state=self.map_mapdag_node(map_id=mapDAGnode,is_front=is_front,join_map=join_map and self.is_normal_state)
                            if(map_state):
                                map_list=self.mapDAG.update(del_node=mapDAGnode)
                                t_can_map=True
                                mapDAGnode=None
                                break_flag=True
                                break
                        if(break_flag):
                            break
                can_step=True
                if(split and self.is_normal_state):
                    for i in range(0,len(map_list)):
                        is_front= i==0
                        break_flag=False
                        if( ((not look_ahead or not ahead_split) or not self.is_normal_state) and i>0):
                            break
                        for mapDAGnode in map_list[i]:
                            split_state,exterid=self.split(map_id=mapDAGnode,is_front=is_front)
                            if(split_state):
                                can_step=False
                                map_state=self.map_mapdag_node(map_id=exterid,is_front=is_front,join_map=join_map and self.is_normal_state)
                                assert map_state==True
                                map_list=self.mapDAG.update(del_node=exterid)
                                mapDAGnode=None
                                break_flag=True
                                break
                        if(break_flag):
                            break
                can_step=not self.handle_event() and can_step
                if(can_step):
                    #print(self.t,map_list)
                    #self.print_events()
                    #self.print_QPU()
                    #self.cacheDAG.print()
                    #self.connG.print()
                    self.step()
            if(len(map_list[0])>0):# retry
                self.retry_num+=1
                self.is_normal_state=False
                self.retry_base_step_count=0
                if(self.t>self.max_t):
                    self.max_t=self.t
                    self.retry_length=self.min_retry_length
                else:
                    self.retry_length=int(self.retry_length*self.retry_length_mul)
                print("retry!")
                self.restore()
                #self.cacheDAG.print_split()
                #self.print_QPU()
        print(self.t,map_list)
        #self.print_events()
        #self.cacheDAG.print()
        #self.mapDAG.print()
        #self.connG.print()
        #self.cacheDAG.print_split()
        #self.print_pair_num()
        #print("cross_EPR_cache_time",self.cross_EPR_cache_time,"inter_EPR_cache_time",self.inter_EPR_cache_time)
        #self.QPUs.print_QPU()
        return self.t,self.cross_pair,self.inter_pair,self.distill_pair,\
            self.cross_EPR_cache_time,self.inter_EPR_cache_time,self.retry_num,self.total_step,self.schedule_result_list
    def print_events(self):
        print("###############")
        for i in self.event_list:
            print("#")
            for j in i:
                j.print()
    def print_pair_num(self):
        print("cross_pair",self.cross_pair,"inter_pair",self.inter_pair,"distill_pair",self.distill_pair)
class Scheduler_baseline:
    def __init__(self,connG,DAG,commqbit_num=2,cache_size=10,reserve_size=2,
                 inter_time=1,switch_time=10,exter_time=100,
                 check_CAT_sTP=True,check_dTP=True,check_split_num=True):
        # connG:edge field: [0,0,0,...] state, node field: is_router. DAG node field: info(communication qpu pairs), is_teleport
        # reserve_size:number of qubits needed for execution at a layer less than reserve_size, 
        # need DAG contain layer  information to determine which layer the current node belongs to
        self.cacheDAG=CacheDAG(DAG=DAG)# upate will change QPU status
        self.mapDAG=MapDAG(DAG=DAG,schedu_depth=1)
        self.connG=ConnG(connG=connG)
        #self.QPUs={}
        self.QPU_free={}
        self.event_list=[[]]
        self.inter_time=inter_time
        self.switch_time=switch_time
        self.exter_time=exter_time
        self.t=1
        self.cross_pair,self.inter_pair,self.distill_pair=0,0,0
        self.inter_EPR_cache_time,self.cross_EPR_cache_time=0,0
        self.retry_num=0
        self.total_step=self.t
        self.schedule_result_list=[]
        qpu_list=[]
        for i in connG.nodes:
            if(not connG.nodes[i]["is_router"]):
                qpu_list.append(i)
                self.QPU_free[i]=True
        self.QPUs=QPUS(qpu_list=qpu_list,commqbit_num=commqbit_num,cache_size=cache_size,reserve_size=reserve_size,
                        check_CAT_sTP=check_CAT_sTP,check_dTP=check_dTP,check_split_num=check_split_num)
    def push_event(self,event):
        gap=event.end_t-self.t
        while(len(self.event_list)<gap+1):
            self.event_list.append([])
        self.event_list[gap].append(event)
    def save_schedule(self,event:Event):
        opair,is_teleport=self.cacheDAG.get_pair_info(id=event.dag_id)
        pair_type=''
        if(is_teleport):
            pair_type+='T'
        else:
            pair_type+='C'
        map_p=event.map_commpair
        if((opair[0]==map_p[0] and opair[1]==map_p[1]) or (opair[0]==map_p[1] and opair[1]==map_p[0])):
            pair_type+='O'
        else:
            pair_type+='S'
        self.schedule_result_list.append([pair_type,opair,map_p,event.start_t,event.end_t])
    def handle_event(self):
        events=self.event_list[0]
        have_event=len(events)>0
        while(len(events)>0):
            event=events.pop(0)
            dag_id=event.dag_id
            if(dag_id<0):
                continue
            self.save_schedule(event=event)
            map_commpair=event.map_commpair
            cross_cache,inter_cache=\
                self.cacheDAG.update(node=dag_id,map_commpair=map_commpair,QPUs=self.QPUs,t=self.t,connG=self.connG)
            self.inter_EPR_cache_time+=inter_cache
            self.cross_EPR_cache_time+=cross_cache
        return have_event
    def map_mapdag_node(self,map_id):
        origin_id,commpair=self.mapDAG.get_oid_pair(map_id=map_id)
        qpu0,qpu1=commpair
        if(not self.QPU_free[qpu0] or not self.QPU_free[qpu1]):
            return False
        self.QPU_free[qpu0]=False
        self.QPU_free[qpu1]=False
        is_teleport_sub=self.cacheDAG.test_teleport_sub_flag(id=origin_id,commpair=commpair)
        is_inter=self.connG.pair_is_inter(commpair=commpair)
        if(is_inter):
            end_t=self.t+self.switch_time+self.inter_time
        else:
            end_t=self.t+self.switch_time+self.exter_time
        pair_cache_enough=self.QPUs.cache_enough(commpair=commpair,is_front=True,is_split=False,is_teleport_sub=is_teleport_sub)
        if(not pair_cache_enough):
            #print("f1")
            #print(commpair,origin_id)
            return False
        path_flag,path=self.connG.get_flag_path(commpair=commpair,t=self.t)
        # try normal map
        if(not path_flag):
            #print("f2")
            #print(commpair,origin_id)
            return False
        flag,commqbits_id=self.QPUs.normal_map_flag_id(commpair=commpair,t=self.t)
        if(not flag):
            #print("f3")
            #print(commpair,origin_id)
            return False
        if(is_teleport_sub):
            self.cacheDAG.clear_teleport_sub_flag(id=origin_id)
        # add path update
        end_t=self.QPUs.map_with_aheadpairs(end_t=end_t,commpair=commpair,commqbits_id=commqbits_id,is_teleport_sub=is_teleport_sub
                                               ,is_split=False,path=path)
        epr_time_gap=0
        if(end_t<=self.t):
            epr_time_gap=self.t-end_t
            end_t=self.t
        else:
            self.connG.update(path=path,end_t=end_t)
        self.push_event(Event(start_t=self.t,end_t=end_t,dag_id=origin_id,map_commpair=commpair))
        if(is_inter):
            self.inter_pair+=1
            self.inter_EPR_cache_time+=epr_time_gap
        else:
            self.cross_pair+=1
            self.cross_EPR_cache_time+=epr_time_gap
        if(origin_id%1000==0):
            print("normal map origin_id: ",origin_id,"map_id: ",map_id)
        return True
    def gen_aheadpairs(self):
        free_qpu_list=self.QPUs.get_free_gen_aheadpairs_qpu_list(t=self.t)
        if(len(free_qpu_list)==0):
            return None
        #random.shuffle(free_qpu_list)
        #print(free_qpu_list)
        for qpu_idx0 in range(0,len(free_qpu_list)-1):
            qpu0=free_qpu_list[qpu_idx0]
            path_flag=False
            for qpu1 in free_qpu_list[qpu_idx0+1:]:
                commpair=(qpu0,qpu1)
                path_flag,path=self.connG.get_flag_path(commpair=commpair,t=self.t)
                comm_flag,commqbits_id=self.QPUs.normal_map_flag_id(commpair=commpair,t=self.t)
                if(path_flag and comm_flag):
                    break
            if(path_flag and comm_flag):
                is_inter=self.connG.pair_is_inter(commpair=commpair)
                if(is_inter):
                    end_t=self.t+self.switch_time+self.inter_time
                else:
                    end_t=self.t+self.switch_time+self.exter_time
                self.QPUs.map_aheadpair_to_qpu(end_t=end_t,commpair=commpair,commqbits_id=commqbits_id,path=path)
                self.push_event(Event(start_t=self.t,end_t=end_t,dag_id=-1,map_commpair=commpair))
    def step(self):
        for i in self.QPU_free:
            self.QPU_free[i]=True
        while(len(self.event_list)>0 and len(self.event_list[0])==0):
            self.t+=1
            self.total_step+=1
            self.event_list.pop(0)
    def run(self,ahead_epr=False):
        #self.print_QPU()
        #print("start running!")
        mapDAGnode=None
        map_list=self.mapDAG.update(del_node=None)[0]
        map_list.sort()
        print(self.t,map_list)
        while(len(map_list)>0 or len(self.event_list)>0):
            t_can_map=True
            while(t_can_map):
                t_can_map=False
                for mapDAGnode in map_list:
                    map_state=self.map_mapdag_node(map_id=mapDAGnode)
                    if(map_state):
                        map_list=self.mapDAG.update(del_node=mapDAGnode)[0]
                        map_list.sort()
                        t_can_map=True
                        mapDAGnode=None
                        break
            can_step=not self.handle_event()
            if(can_step):
                #print(self.t,map_list)
                # print(self.event_list)
                # self.print_events()
                # self.print_QPU()
                #self.cacheDAG.print()
                #self.connG.print()
                if(ahead_epr):
                    self.gen_aheadpairs()
                self.step()
        print(self.t,map_list)
        #self.print_events()
        #self.cacheDAG.print()
        #self.mapDAG.print()
        #self.connG.print()
        #self.cacheDAG.print_split()
        #print("cross_EPR_cache_time",self.cross_EPR_cache_time,"inter_EPR_cache_time",self.inter_EPR_cache_time)
        #self.QPUs.print_QPU()
        #print(len(list(self.cacheDAG.DAG.nodes)))
        #self.print_pair_num()
        return self.t,self.cross_pair,self.inter_pair,self.distill_pair,\
            self.cross_EPR_cache_time,self.inter_EPR_cache_time,self.retry_num,self.total_step,self.schedule_result_list
    def print_events(self):
        print("###############")
        for i in self.event_list:
            print("#")
            for j in i:
                j.print()
    def print_pair_num(self):
        print("cross_pair",self.cross_pair,"inter_pair",self.inter_pair,"distill_pair",self.distill_pair)
class Validater:
    def __init__(self,QPUs,DAG):
        self.QPUs=deepcopy(QPUs.QPUs)
        for node in nx.topological_sort(DAG):
            if(DAG.nodes[node]['is_teleport']):
                qpu0,qpu1=DAG.nodes[node]['info']
                self.QPUs[qpu0].max_cache_size+=1
                self.QPUs[qpu1].max_cache_size-=1
                self.QPUs[qpu0].cache_size+=1
                self.QPUs[qpu1].cache_size-=1
    def run(self,final_QPUs):
        final_QPUs=final_QPUs.QPUs
        for id in final_QPUs:
            assert final_QPUs[id].max_cache_size == self.QPUs[id].max_cache_size
            assert final_QPUs[id].cache_size == self.QPUs[id].cache_size
            assert final_QPUs[id].split_reserve==0
        print("pass!")
    def print_QPU(self):
        for i in self.QPUs:
            self.QPUs[i].print()