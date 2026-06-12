import os
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .artifacts import save_json


os.environ.setdefault("OMP_NUM_THREADS", "1")


def embeddings_to_matrix(
    requirement_embeddings: List[Dict[str, List[float]]],
) -> Tuple[List[str], np.ndarray]:
    paths: List[str] = []
    embeddings: List[List[float]] = []
    for item in requirement_embeddings:
        for path, embedding in item.items():
            paths.append(path)
            embeddings.append(embedding)
    if not embeddings:
        return paths, np.empty((0, 0))
    return paths, np.asarray(embeddings, dtype=float)


def select_optimal_kmeans_cluster_count(matrix: np.ndarray) -> int:
    sample_count = len(matrix)
    if sample_count < 3:
        return 1

    best_k = 2
    best_score = -1.0
    max_clusters = min(30, sample_count - 1)
    for cluster_count in range(2, max_clusters + 1):
        model = KMeans(
            n_clusters=cluster_count,
            init="k-means++",
            n_init=10,
            random_state=42,
        )
        labels = model.fit_predict(matrix)
        score = silhouette_score(matrix, labels)
        if score > best_score:
            best_score = score
            best_k = cluster_count
    return best_k


def cluster_requirements_with_kmeans_node(state: Dict) -> Dict:
    paths, matrix = embeddings_to_matrix(state.get("requirement_embeddings", []))
    if not paths:
        save_json(state, "04_kmeans_clustering/kmeans_clusters.json", {})
        return {"kmeans_clusters": {}}
    if len(paths) < 3:
        clusters = {0: paths}
        save_json(state, "04_kmeans_clustering/kmeans_clusters.json", clusters)
        return {"kmeans_clusters": clusters}

    cluster_count = select_optimal_kmeans_cluster_count(matrix)
    model = KMeans(
        n_clusters=cluster_count,
        init="k-means++",
        n_init=10,
        random_state=42,
    )
    labels = model.fit_predict(matrix)

    clusters: Dict[int, List[str]] = defaultdict(list)
    for path, label in zip(paths, labels):
        clusters[int(label)].append(path)

    result = dict(clusters)
    save_json(state, "04_kmeans_clustering/kmeans_clusters.json", result)
    return {"kmeans_clusters": result}
