# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 16:37:37 2017

@author: lu
"""

import pandas as pd
import numpy as np
import networkx as nx
import time
import os
from os.path import join
import matplotlib.pyplot as plt
import gevent
import gevent.pool
import multiprocessing
from multiprocessing import Pool
import os, time, random
import matplotlib.pyplot as plt
import seaborn as sns
import sys
from scipy import stats
from compiler.ast import flatten

# python project2.py -i result_c5_s10_20171220weight.txt -d IDMapping_consolidated_allPhi2_cleaned_lfc_avg.txt -f IDMapping_consolidated_allQESV_cleaned_LFC_avg.txt -g IDMapping_consolidated_allQI_new_RAW3_adj_LFC_avg.txt -w 0.9 -s 5 -p 0.5 -m 0.005 -n -0.18 -b 0.08 -v -0.22 -c -100 -z 0.34
phe1 = pd.read_table('G:\project2\\NPM201507\\data\\IDMapping_consolidated_allPhi2_cleaned_lfc_avg.txt', index_col=0)
phe2 = pd.read_table('G:\project2\\NPM201507\\data\\IDMapping_consolidated_allQESV_cleaned_LFC_avg.txt', index_col=0)
phe3 = pd.read_table('G:\project2\\NPM201507\\data\\IDMapping_consolidated_allQI_new_RAW3_adj_LFC_avg.txt', index_col=0)

phe1.columns = [i for i in range(0, 113)]
phe2.columns = [i for i in range(0, 113)]
phe3.columns = [i for i in range(0, 113)]


def tree_statis(weight_value, window):
    # output 50 trees
    filename2 = 'edge/edgeInfo' + str(window) + '.txt'
    f_path2 = curr_path + os.path.normpath(filename2)
    f_window = open(f_path2, 'w')
    df = data[data[data.columns[window]] >= (weight_value + 0.00001)]
    print df.shape
    for edge in range(0, df.shape[0]):
        node_1, node_2 = df.index[edge].split('_')
        f_window.write(node_1 + '\t' + node_2 + '\n')


def tree0(weight_value, startwindow, term):
    # 2017.8.21
    print 'start window:', startwindow
    # windowGraph = {}
    cliqueGraph = nx.DiGraph()
    dic_term = {}
    dic_last_time = {}
    dic_temp = {}
    dic_term_num = {}
    dic_intersect_level = {}
    # term = 183
    root = 0
    cliqueGraph.add_node(root, annotation='root', windowsize='root', weight_value='root')
    w = data.shape[1]
    i = 0
    q = 0
    for window in range(startwindow, w):
        dic_intersect_level.clear()
        if window == startwindow:

            for clique in nx.find_cliques(windowGraph[window]):
                if len(clique) > 5:

                    cliqueGraph.add_node(term, annotation=list(clique), windowsize=[window],
                                         weight=weight_value)  # generate a term
                    cliqueGraph.add_edge(root, term)
                    dic_term[frozenset(clique)] = [window]  # dic_term 记录 window和clique
                    dic_term_num[frozenset(clique)] = term  # dic_term_num 记录 term 序号和clique
                    dic_last_time[frozenset(clique)] = [window]  # dic_last_time   记录上一时刻生成的交集 用于下一时刻的比较
                    term = term + 1
                else:
                    continue
                    # print len(dic_last_time), len(dic_term), cliqueGraph.number_of_nodes()
        else:

            for clique in nx.find_cliques(windowGraph[window]):
                if len(clique) > 5:

                    for key, value in dic_last_time.items():  # key 是clique ,value是 [window]
                        intersect = sorted(set(key).intersection(set(clique)))
                        q = 0
                        if len(intersect) >= 5:
                            # 同一层判断交集之间是否有重复的父子关系。 每生成一个交集， 判断当前层的其他term和交集的关系。
                            for ik, iv in dic_intersect_level.items():
                                if set(intersect) == (set(ik)):  # 生成一模一样的交集
                                    # 判断两个的编号是否一样？
                                    if dic_term_num[frozenset(key)] != dic_term_num[frozenset(ik)]:
                                        cliqueGraph.add_edge(dic_term_num[frozenset(key)], dic_term_num[frozenset(ik)])
                                    q = 1
                                    break
                                elif set(intersect).issuperset(set(ik)):  # 生成了超集
                                    cliqueGraph.remove_node(dic_term_num[frozenset(ik)])
                                    dic_term.pop(frozenset(ik))  # 从四个字典中都删除该节点的信息
                                    dic_term_num.pop(frozenset(ik))
                                    dic_intersect_level.pop(frozenset(ik))
                                    dic_temp.pop(frozenset(ik))
                                elif set(intersect).issubset(set(ik)):  # 生成了子集
                                    q = 1
                                    break
                            if q == 1:
                                continue
                            dic_intersect_level[frozenset(intersect)] = 1

                            if dic_term.has_key(frozenset(intersect)):
                                # 交集已经出现过
                                parent = cliqueGraph.predecessors(dic_term_num[frozenset(intersect)])
                                children = cliqueGraph.successors(dic_term_num[frozenset(intersect)])
                                if len(parent) > 0:
                                    # 是交集生成的term，则重定向
                                    cliqueGraph.add_node(term, annotation=list(intersect),
                                                         windowsize=value + [window],
                                                         weight=weight_value)
                                    for p in parent:
                                        cliqueGraph.add_edge(p, term)  # 连边

                                    for c in children:
                                        cliqueGraph.add_edge(term, c)  # 连边
                                    cliqueGraph.remove_node(dic_term_num[frozenset(intersect)])  # 从图中删除冗余结点

                                    # print 'deleted intersect nodes:',dic_term_num[frozenset(intersect)]
                                    i = i + 1
                                    dic_term.pop(frozenset(intersect))  # 字典中删除
                                    dic_term_num.pop(frozenset(intersect))

                                    dic_term[frozenset(intersect)] = value + [window]  # 新节点插入字典
                                    dic_term_num[frozenset(intersect)] = term
                                    dic_temp[frozenset(intersect)] = value + [window]  # 记录到dic_temp里
                                    term = term + 1
                                    continue
                                else:
                                    # 是window生成的term
                                    continue
                            else:
                                # 交集没有出现过， 则生成新的term
                                # print 'new term intersect never appear:', term
                                cliqueGraph.add_node(term, annotation=list(intersect), windowsize=value + [window],
                                                     weight=weight_value)  # generate a term

                                cliqueGraph.add_edge(dic_term_num[frozenset(key)], term)  # 连边，变化：只连接交集作为父亲。
                                dic_term[frozenset(intersect)] = value + [window]  # 新节点插入字典
                                dic_term_num[frozenset(intersect)] = term
                                dic_temp[frozenset(intersect)] = value + [window]  # 记录到dic_temp里
                                term = term + 1
                        else:
                            continue
                else:
                    continue
            dic_last_time.clear()
            for key, value in dic_temp.items():
                dic_last_time[key] = value
            dic_temp.clear()
    print 'window', startwindow, 'size is', cliqueGraph.number_of_nodes(), cliqueGraph.number_of_edges()
    # print 'deleted nodes:', i
    # fw = open('0904edges_remove.txt', 'w')
    # fw2 = open('0904terms_remove.txt', 'w')
    # fw.write('parent' + '\t' + 'child' + '\n')
    # for edge in cliqueGraph.edges():
    #     fw.write(str(edge[0]) + '\t' + str(edge[1]) + '\n')
    # fw.close()
    # fw2.write('term_id' + '\t' + 'anno_genes' + '\t' + 'window' + '\t' + 'gene_size' + '\t' + 'window_size' + '\n')
    # for key, value in dic_term.items():
    #     fw2.write(str(dic_term_num[key]) + '\t' + str(key) + '\t' + str(value) + '\t' + str(len(key)) + '\t' + str(len(value)) + '\n')
    # fw2.close()
    # for nodes in cliqueGraph.nodes():
    #     if cliqueGraph.degree(nodes) == 0:
    #         print nodes
    # 20170905
    return cliqueGraph, dic_term, dic_term_num, term


def sign_value(node, gene_set, window):
    t_min = min(window) + 49
    t_max = max(window) + 49 + 10
    window_set = [i for i in range(t_min, t_max)]  # 回到最原始的数据上
    p1 = phe1.loc[gene_set, window_set]
    p2 = phe2.loc[gene_set, window_set]
    p3 = phe3.loc[gene_set, window_set]

    p1_list = flatten(p1.values.tolist())
    p2_list = flatten(p2.values.tolist())
    p3_list = flatten(p3.values.tolist())
    sign_p1 = [x for x in p1_list if x < -0.18 or x > 0.08]
    sign_p2 = [x for x in p2_list if x < -0.22 or x > 0.27]
    sign_p3 = [x for x in p3_list if x > 0.34]
    sign = len(sign_p1) + len(sign_p2) + len(sign_p3)
    all = len(p1_list) + len(p2_list) + len(p3_list)
    if p1[t_min].mean() - p1[t_max - 1].mean() < 0:
        trend1 = 1
    else:
        trend1 = 0
    if p2[t_min].mean() - p2[t_max - 1].mean() < 0:
        trend2 = 1
    else:
        trend2 = 0
    if p3[t_min].mean() - p3[t_max - 1].mean() < 0:
        trend3 = 1
    else:
        trend3 = 0
    return sign, float(sign) / all, trend1, trend2, trend3

if __name__ == '__main__':

    start = time.clock()

    # for i in range(0, 50):
    #     tree_statis(0.9, i)
    s = 0
    # 先产生第一个window的 tree
    term = 183
    # filename = 'result_c5_s10_v2_weight.txt'
    # 20171217
    # filename = 'result_c5_s10_20171219weight.txt'
    filename = 'result_c5_s10_20171220weight.txt'
    data = pd.read_csv(filename, index_col=0, sep='\t')
    # print data.head(5), type(data.loc['AT4G33520_AT1G67840']['49'])
    curr_path = os.getcwd() + '/'
    weight_value = 0.9
    windowGraph = {}

    for window in range(0, 54):
        windowGraph[window] = nx.Graph()
        df = data[data[data.columns[window]] >= (weight_value + 0.00001)]
        # print window, weight_value, df.shape
        for edge in range(0, df.shape[0]):
            node_1, node_2 = df.index[edge].split('_')
            windowGraph[window].add_edge(node_1, node_2)

    cliqueGraph0, dic_term0, dic_term_num0, term = tree0(weight_value, 0, 183)
    dic_all = {}
    dic_all = dic_term0.copy()
    copy_clique = cliqueGraph0
    for i in range(1, 50):
        print 'begin term num:', term
        cliqueGraph1, dic_term1, dic_term_num1, term = tree0(weight_value, i, term)

        for key in dic_term1.keys():
            if dic_all.has_key(key):
                if set(dic_all[key]).issuperset(set(dic_term1[key])):
                    dic_term1.pop(key)
                    num = dic_term_num1[key]
                    cliqueGraph1.remove_node(num)
                    s = s + 1
                else:
                    dic_all[key] = dic_all[key] + dic_term1[key]
                    dic_term1.pop(key)
                    # num = dic_term_num1[key]
                    # cliqueGraph1.remove_node(num)
                    # else:
                    #     dic_all[key] = dic_term1[key]

        dic_all.update(dic_term1)
        cliqueGraph0 = nx.compose(cliqueGraph0, cliqueGraph1)
        print 'before purity window', i, cliqueGraph0.number_of_nodes(), cliqueGraph0.number_of_edges()
    dic_term_score = {}
    dic_term_distance = {}
    dic_vector = {}
    dic_pearson = {}
    dic = {}
    fr = open('G:\project2\\NPM201507\\code\\term_name_id\\termN_Id.txt', 'r')
    for line in fr:
        term, idd = line.strip().split('\t')
        dic[term] = idd
    for node in cliqueGraph0.nodes():
        if node == 0:
            continue
        else:
            gene_set = cliqueGraph0.node[node]['annotation']
            window_set = cliqueGraph0.node[node]['windowsize']
            # 判断phenotype是否有意义
            sign, score, trend1, trend2, trend3 = sign_value(node, gene_set, window_set)
            dis = class_distance(node, gene_set, window_set)
            pearson_coff = pearson(node, gene_set, window_set)
            if score < 0.005:
                # 无意义，delete，重定向
                parent = cliqueGraph0.predecessors(node)
                child = cliqueGraph0.successors(node)
                for p in parent:
                    for c in child:
                        cliqueGraph0.add_edge(p, c)
                cliqueGraph0.remove_node(node)
            else:
                dic_term_score[node] = score
                dic_term_distance[node] = dis
                dic_pearson[node] = pearson_coff
                dic_vector[node] = []
                dic_vector[node].append(len(cliqueGraph0.node[node]['annotation']))
                dic_vector[node].append(len(cliqueGraph0.node[node]['windowsize']) + 9)
                if len(cliqueGraph0.successors(node)) == 0:
                    dic_vector[node].append(1)
                else:
                    dic_vector[node].append(0)
                dic_vector[node].append(trend1)
                dic_vector[node].append(trend2)
                dic_vector[node].append(trend3)
                continue
    print 'after purity window', i, cliqueGraph0.number_of_nodes(), cliqueGraph0.number_of_edges()
    # name--id
    # dic = {}
    # fr = open('G:\project2\\NPM201507\\code\\term_name_id\\termN_Id.txt', 'r')
    # for line in fr:
    #     term, idd = line.strip().split('\t')
    #     dic[term] = idd
    # leaf nodes:
    # fwc = open('my_method_leaf_nodes.txt', 'w')
    # for node in cliqueGraph0.nodes():
    #     if len(cliqueGraph0.successors(node))==0:
    #         fwc.write(str(node) + '\n')


    fw1 = open('0325edges_sign_id.txt', 'w')
    fw2 = open('0325terms_sign_id.txt', 'w')
    fw3 = open('0325sign_distance_id.txt', 'w')
    fw4 = open('0325term_vector_id.txt', 'w')
    fw5 = open('0325term_pearson_id.txt', 'w')
    fw6 = open('0325terms_sign_list_id.txt', 'w')
    fw1.write('parent' + '\t' + 'child' + '\n')
    for edge in cliqueGraph0.edges():
        fw1.write(str(edge[0]) + '\t' + str(edge[1]) + '\n')
    fw2.write(
        'term_id' + '\t' + 'sign_score' + '\t' + 'annotation_gene' + '\t' + 'start_time' + '\t' + 'end_time' + '\t' + 'geneSize' + '\t' + 'time_size' + '\n')
    fw3.write('Term_Id' + '\t' + 'distance' + '\n')
    fw4.write(
        'Term_id' + '\t' + 'Sign_score' + '\t' + 'Gene_number' + '\t' + 'Time_point_length' + '\t' + 'leaf' + '\t' + 'Trend1' + '\t' + 'Trend2' + '\t' + 'Trend3' + '\n')
    fw5.write('Term_id' + '\t' + 'pearson' + '\n')
    fw6.write(
        'term_id' + '\t' + 'sign_score' + '\t' + 'level' + '\t' + 'annotation_gene' + '\t' + 'start_time' + '\t' + 'end_time' + '\t' + 'geneSize' + '\t' + 'time_size' + '\n')

    for node, value in sorted(dic_term_score.items(), key=lambda d: d[1], reverse=True):
        fw2.write(
            str(node) + '\t' + str(round(value, 4)) + '\t' + str(cliqueGraph0.node[node]['annotation']) + '\t' + str(
                min(cliqueGraph0.node[node]['windowsize']) + 49) + '\t' + str(
                max(cliqueGraph0.node[node]['windowsize']) + 58) + '\t' +
            str(len(cliqueGraph0.node[node]['annotation'])) + '\t' + str(
                len(cliqueGraph0.node[node]['windowsize']) + 9) + '\n')
        fw3.write(str(node) + '\t' + str(dic_term_distance[node]) + '\n')
        fw4.write(str(node) + '\t' + str(round(value, 4)) + '\t' + '\t'.join(str(i) for i in dic_vector[node]) + '\n')
        fw5.write(str(node) + '\t' + str(dic_pearson[node]) + '\n')
        fw6.write(
            str(node) + '\t' + str(round(value, 4)) + '\t' + str(
                nx.shortest_path_length(cliqueGraph0, 0, node)) + '\t' + ','.join(
                [dic[t] for t in cliqueGraph0.node[node]['annotation']]) + '\t' + str(
                min(cliqueGraph0.node[node]['windowsize']) + 49) + '\t' + str(
                max(cliqueGraph0.node[node]['windowsize']) + 58) + '\t' +
            str(len(cliqueGraph0.node[node]['annotation'])) + '\t' + str(
                len(cliqueGraph0.node[node]['windowsize']) + 9) + '\n')

    fw1.close()
    fw2.close()
    fw3.close()
    fw4.close()
    fw5.close()
    fw6.close()




    end = time.clock()
    print 'The function run time is : %.03f seconds' % (end - start)
