#!/usr/bin/env python

#Content based recommender system - item 2 item

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import argparse

def get_recommendation(fic):
    if fic in mapping_reduced:
        fic_index = mapping_reduced[fic]
    else:
        exit("This fic does not appear in the database")
    sc = similarity_matrix[fic_index].toarray().reshape(-1)
    identical = np.where(sc==1.0)
    similarity_score = list(enumerate(similarity_matrix[fic_index].toarray().reshape(-1)))
    similarity_score = sorted(similarity_score, key=lambda x: x[1], reverse=True)
    similarity_score = similarity_score[1:args.numR]
    fic_indices = [i[0] for i in similarity_score]
    return (df_reduced[["idName","title","metadata"]].iloc[fic_indices],similarity_score)

def find_optimal_clusters(data, max_k):
    iters = range(6, max_k+1, 2)
    for a in range(100):
        sse = []
        for k in iters:
            sse.append(MiniBatchKMeans(n_clusters=k, init_size=1024, batch_size=2048, random_state=a).fit(data).inertia_)
            print('Fit {} clusters'.format(k))
        print(a)
        f, ax = plt.subplots(1, 1)
        ax.plot(iters, sse, marker='o')
        ax.set_xlabel('Cluster Centers')
        ax.set_xticks(iters)
        ax.set_xticklabels(iters)
        ax.set_ylabel('SSE')
        ax.set_title('SSE by Cluster Center Plot - random_seed = '+str(a))
        plt.show()

parser = argparse.ArgumentParser(description="Content based recommender")
parser.add_argument("-i",dest="metadataFile",action="store",required=True,help="File containing the fics metadata")
parser.add_argument("-m",dest="filtering_mode",action="store",choices=["clustering","number_words"],default="number_words",help="How data will be filtered before prediction")
parser.add_argument("-f",dest="ficInterest",action="store",type=int,required=True,help="Id of the fic you want to search similarities to")
parser.add_argument("--number_clusters",dest="numCl",action="store",type=int,default=12,help="Number of clusters used in kmeans when clustering filter is selected")
parser.add_argument("--random_seed",dest="randS",action="store",type=int,default=33,help="Random seed to run kmeans")
parser.add_argument("--number_words",dest="numW",action="store",type=int,default=10000,help="Number of words in Tfid analysis")
parser.add_argument("--number_recommendations",dest="numR",action="store",type=int,default=15,help="Number of recommendations")
parser.add_argument("--add_characters",dest="addC",action="store_true",help="Adds character information to the metadata")
parser.add_argument("--add_relationships",dest="addR",action="store_true",help="Adds relationship information to the metadata")
parser.add_argument("--find_optimal_clusters",dest="optimize_clusters",action="store_true",help="Provides graphs to explore the optimal number of clusters, iterated over number of cl and random_state")
args = parser.parse_args()
    
df = pd.read_csv(args.metadataFile,sep="\t",na_values="-")
df["additional_tags"] = df["additional_tags"].fillna("")
df["characters"] = df["characters"].fillna("")
df["relationships"] = df["relationships"].fillna("")
df["metadata"] = df["additional_tags"]
if args.addC:
    df["metadata"] = df["metadata"] + df["characters"]
if args.addR:
    df["metadata"] = df["metadata"] + df["relationships"]
    
tfidf = TfidfVectorizer(stop_words="english",max_features=args.numW) 
word_matrix = tfidf.fit_transform(df["metadata"])
ficName = args.ficInterest

if args.filtering_mode == "clustering":
    if args.optimize_clusters:
        find_optimal_clusters(word_matrix, 20)
    clusters = MiniBatchKMeans(n_clusters=args.numCl, init_size=1024, batch_size=2048, random_state=33).fit_predict(word_matrix)
    df["cluster"] = clusters
    mapping = pd.Series(df.index,index = df["idName"])
    fic_index = mapping[ficName]
    cl = df.iloc[fic_index]["cluster"]
    cluster_idx = df[df["cluster"] == cl].index
    df_reduced = df[df["cluster"] == cl]
    df_reduced.reset_index(drop=True,inplace=True)
    word_matrix_reduced = word_matrix[cluster_idx]

elif args.filtering_mode == "number_words":
    df_reduced = df.sort_values(by=["numWords"],ascending=False)[:50000]
    numWords_idx = df_reduced.index
    df_reduced.reset_index(drop=True,inplace=True)
    word_matrix_reduced = word_matrix[numWords_idx]

mapping_reduced = pd.Series(df_reduced.index,index = df_reduced["idName"])
fic_index = mapping_reduced[ficName]
similarity_matrix = linear_kernel(word_matrix_reduced,word_matrix_reduced,dense_output=False)

recom,similarity_score = get_recommendation(ficName)

print(df_reduced[df_reduced["idName"] == ficName][["idName","title","metadata"]])
print(recom)
print(similarity_score)
