from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from .artifacts import save_json
from .kmeans_clustering import embeddings_to_matrix


def build_hca_model(cluster_count: int):
    try:
        return AgglomerativeClustering(
            n_clusters=cluster_count,
            metric="cosine",
            linkage="average",
        )
    except TypeError:
        return AgglomerativeClustering(
            n_clusters=cluster_count,
            affinity="cosine",
            linkage="average",
        )


def select_optimal_hca_labels(matrix: np.ndarray) -> np.ndarray:
    sample_count = len(matrix)
    if sample_count < 3:
        return np.zeros(sample_count, dtype=int)

    best_score = -1.0
    best_labels: Optional[np.ndarray] = None
    max_clusters = min(30, sample_count - 1)
    for cluster_count in range(2, max_clusters + 1):
        model = build_hca_model(cluster_count)
        labels = model.fit_predict(matrix)
        try:
            score = silhouette_score(matrix, labels, metric="cosine")
        except ValueError:
            continue
        if score > best_score:
            best_score = score
            best_labels = labels

    if best_labels is None:
        return np.zeros(sample_count, dtype=int)
    return best_labels


def cluster_requirements_with_hca_node(state: Dict) -> Dict:
    paths, matrix = embeddings_to_matrix(state.get("requirement_embeddings", []))
    if not paths:
        save_json(state, "05_hca_clustering/hca_clusters.json", {})
        return {"hca_clusters": {}}
    if len(paths) < 3:
        clusters = {0: paths}
        save_json(state, "05_hca_clustering/hca_clusters.json", clusters)
        return {"hca_clusters": clusters}

    labels = select_optimal_hca_labels(matrix)
    clusters: Dict[int, List[str]] = defaultdict(list)
    for path, label in zip(paths, labels):
        clusters[int(label)].append(path)

    result = dict(clusters)
    save_json(state, "05_hca_clustering/hca_clusters.json", result)
    return {"hca_clusters": result}
