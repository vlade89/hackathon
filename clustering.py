import os
import random
import re

import compress_fasttext
import numpy as np
import pandas as pd
from sklearn import cluster

from lib.preprocessing import Preprocessing
from lib.read_data import parse_resume, read_resume

INPUT_DATA_PATH = './data'
OUTPUT_DATA_PATH = './data/resumes.csv'
MODEL_PATH = 'nlp_model/small_model'
VECTORIZER = compress_fasttext.models.CompressedFastTextKeyedVectors.load(MODEL_PATH)
NUM_CLUSTERS = 31
SEED = 2023
random.seed(SEED)

resumes = []
for file in os.listdir(INPUT_DATA_PATH):
    my_soup = read_resume(file)
    resumes.append(parse_resume(my_soup))

data = pd.DataFrame.from_records(resumes).assign(
    one_name=lambda df: df['name'].apply(lambda txt: re.split('[,/.]', txt)[0].strip())
)
proc = Preprocessing()
data['tokens_for_clustering'] = proc.process_texts(data, 'one_name')
clustered_data = (
    data
    .loc[data['tokens_for_clustering'].apply(lambda x: len(x) != 0)]
    .assign(
        ft_vectors=lambda df: df['tokens_for_clustering'].apply(
            lambda txt: np.array([VECTORIZER[token] for token in txt]).mean(axis=0)
        )
    )
)[['one_name', 'ft_vectors']]

ft_vectors = np.concatenate(
    clustered_data['ft_vectors'].values
).reshape(clustered_data.shape[0], -1)
clustered_data['agglomerative_labels'] = cluster.AgglomerativeClustering(
    n_clusters=NUM_CLUSTERS
).fit_predict(ft_vectors)
clustered_data['clusters_cnt'] = (
    clustered_data
    .groupby('agglomerative_labels', as_index=False)['one_name']
    .transform('count')
)
clustered_data['cluster_center'] = 'dummy'
data.to_csv(OUTPUT_DATA_PATH, index=False)
clustered_data.to_csv('clustered_data.csv')