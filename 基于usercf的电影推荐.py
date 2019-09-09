#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 13:40:43 2019

@author: liujun
"""

import random
import os
import json 
import math



class UserCFRec:
    def __init__(self,datafile):
        self.datafile=datafile
        self.data=self.load_data()
        self.train,self.test=self.split_data(3,47)
        self.usersim=self.user_similarity()
        
    def load_data(self):
        print('加载数据')
        data=[]
        for line in open(self.datafile):
            userid,itemid,record,_=line.split('::')
            data.append((userid,itemid,int(record)))
        return data
    
    def split_data(self,k,seed,M=8):
        print('拆分数据为训练集和测试集')
        train,test={},{}
        random.seed(seed)
        for userid,itemid,record in self.data:
            if random.randint(0,M)==k:
                test.setdefault(userid,{})
                test[userid][itemid]=record
            else:
                train.setdefault(userid,{})
                train[userid][itemid]=record
        return train,test


#根据john s. breese的论文 计算用户的兴趣相似度公式为w_uv=sum(1/log(1+len(N_i)))/(len(N_u)*len(N_v))^(1/2)
#N_i为对物品i评价过的用户的集合 对uv共同评价过的所有产品进行该操作   为了惩罚热门
#N_u为用户u一共评价过的物品数  N_v为用户v一共评价过的物品数
    def user_similarity(self):
        print('开始计算用户相识度')
        if os.path.exists('user_sim.json'):
            print('开始加载文件')
            usersim=json.load(open('user_sim.json','r'))
        else:
            users=dict() #itemid:userid1,userid2,.......
            for userid, items in self.train.items(): #userid:{itemid:rate}
                for itemid in items.keys():
                    users.setdefault(itemid,set())
                    if self.train[userid][itemid]>0:
                        users[itemid].add(userid) 
            count=dict()
            user_count=dict()
            for itemid,userids in users.items():
                for u in userids:
                    user_count.setdefault(u,0) #userid:0
                    user_count[u]=user_count[u]+1 #userid:评价的商品数
                    count.setdefault(u,{})  #userid_u:(userid_v:1/math.log(1+len(users))
                    for v in userids:
                        count[u].setdefault(v,0)
                        if u==v:
                            continue
                        count[u][v]=count[u][v]+1/math.log(1+len(userids))
            usersim=dict()
            for u, related_user in count.items():
                usersim.setdefault(u,{})
                for v,cuv in related_user.items():
                    if u==v:
                        continue
                    usersim[u].setdefault(v,0)  #userid_u:(user_v:1/math.log(1+len(users)/math.sqrt(user_count[u]*user_count[v]) )
                    usersim[u][v]=cuv/math.sqrt(user_count[u]*user_count[v]) 
            json.dump(usersim,open('user_sim.json','w'))
        return usersim
    


     
    #选择K近邻为用户提供推荐
    def recommend(self,user,k=8,nitems=40):
        result=dict()
        have_scored_items=self.train.get(user,{})
        for v,wuv in sorted(self.usersim[user].items(),key=lambda x:x[1],reverse=True)[:k]:
            for i, rvi in self.train[v].items():
                if i not in have_scored_items:
                    result.setdefault(i,0)
                    result[i]=result[i]+wuv*rvi
        return dict(sorted(result.items(),key=lambda x:x[1],reverse=True)[:nitems])
    
    #评估效果
    def precision(self,k=8,nitems=10):
        print('开始计算准确率')
        hit=0
        precision=0
        for user in self.train.keys():
            tu=self.test.get(user,{})
            rank=self.recommend(user,k=k,nitems=nitems)
            for item,rate in rank.items():
                if item in tu:
                    hit=hit+1
            precision=precision+nitems
        return hit/precision
        
if __name__=='__main__':
    rec=UserCFRec('ratings.dat')
    result=rec.recommend('1')
    print('为用户1推荐的items为{}'.format(result))
    precision=rec.precision()
    print('正确率为{}'.format(precision))
    
             