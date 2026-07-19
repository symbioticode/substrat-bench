"""
pipelines/common/agregation.py — Agrégation assertions multi-instances
Clustering par similarité sémantique + Dawid-Skene (Crowd-Kit) pour P3/P4.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Crowd-Kit pour Dawid-Skene (installé via requirements.txt)
try:
    from crowdkit.aggregation import DawidSkene
    CROWDKIT_AVAILABLE = True
except ImportError:
    CROWDKIT_AVAILABLE = False
    DawidSkene = None


@dataclass
class Assertion:
    """Assertion extraite par une instance, avec source_ref obligatoire (§1bis)."""
    instance_id: str
    text: str
    source_ref: Dict[str, Any]  # {"session_id": "...", "tour_n": int}
    confidence: Optional[str] = None  # FORT/FAIBLE/PROBABLE (P3/P4 seulement)
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "text": self.text,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


@dataclass
class ClusteredAssertion:
    """Groupe d'assertions fusionnées (même source_ref + similarité > seuil)."""
    assertions: List[Assertion]
    representative_text: str
    source_ref: Dict[str, Any]
    instance_count: int
    avg_confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "representative_text": self.representative_text,
            "source_ref": self.source_ref,
            "instance_count": self.instance_count,
            "avg_confidence": self.avg_confidence,
            "assertions": [a.to_dict() for a in self.assertions]
        }


class SemanticClusterer:
    """Clusterise assertions par source_ref exact + similarité cosinus texte."""
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        similarity_threshold: float = 0.50,  # D4 — à valider Sprint 1
        batch_size: int = 32
    ):
        self.threshold = similarity_threshold
        self.model = SentenceTransformer(embedding_model)
        self.batch_size = batch_size
    
    def cluster(
        self,
        assertions: List[Assertion],
        min_instances_for_cluster: int = 1
    ) -> List[ClusteredAssertion]:
        """
        Agrège assertions en clusters.
        
        Algorithme :
        1. Grouper par source_ref exact (session_id, tour_n)
        2. Dans chaque groupe, clusteriser par similarité cosinus > seuil
        3. Pour chaque cluster, calculer texte représentatif (médiane embeddings)
        """
        # Étape 1 : Grouper par source_ref exact
        by_source = defaultdict(list)
        for a in assertions:
            key = (a.source_ref.get("session_id"), a.source_ref.get("tour_n"))
            by_source[key].append(a)
        
        clusters = []
        
        for (session_id, tour_n), group in by_source.items():
            if len(group) == 1:
                # Cluster singleton
                clusters.append(ClusteredAssertion(
                    assertions=group,
                    representative_text=group[0].text,
                    source_ref={"session_id": session_id, "tour_n": tour_n},
                    instance_count=1,
                    avg_confidence=None
                ))
                continue
            
            # Étape 2 : Similarité cosinus dans le groupe
            texts = [a.text for a in group]
            embeddings = self.model.encode(texts, batch_size=self.batch_size, show_progress_bar=False)
            sim_matrix = cosine_similarity(embeddings)
            
            # Clustering agglomératif simple (seuil)
            visited = [False] * len(group)
            for i in range(len(group)):
                if visited[i]:
                    continue
                
                cluster_indices = [i]
                visited[i] = True
                
                for j in range(i + 1, len(group)):
                    if not visited[j] and sim_matrix[i, j] >= self.threshold:
                        cluster_indices.append(j)
                        visited[j] = True
                
                cluster_assertions = [group[idx] for idx in cluster_indices]
                
                # Texte représentatif = celui le plus central (moyenne sim max)
                if len(cluster_indices) > 1:
                    central_idx = cluster_indices[np.argmax([
                        np.mean(sim_matrix[idx, cluster_indices]) for idx in cluster_indices
                    ])]
                    rep_text = group[central_idx].text
                else:
                    rep_text = cluster_assertions[0].text
                
                # Confiance moyenne si disponible (P3/P4)
                confidences = [a.confidence for a in cluster_assertions if a.confidence]
                avg_conf = None
                if confidences:
                    conf_map = {"FAIBLE": 0.33, "PROBABLE": 0.66, "FORT": 1.0}
                    avg_conf = np.mean([conf_map.get(c, 0.5) for c in confidences])
                
                clusters.append(ClusteredAssertion(
                    assertions=cluster_assertions,
                    representative_text=rep_text,
                    source_ref={"session_id": session_id, "tour_n": tour_n},
                    instance_count=len(cluster_indices),
                    avg_confidence=avg_conf
                ))
        
        return clusters


class DawidSkeneAggregator:
    """
    Wrapper Dawid-Skene (Crowd-Kit) pour agrégation labels bruités P3/P4.
    
    Mappe : instances = "annotateurs", clusters = "tâches", 
    vote instance sur cluster = "label" (FORT/FAIBLE/PROBABLE → 0/1/2)
    """
    
    def __init__(self, n_iter: int = 100, tol: float = 1e-6):
        if not CROWDKIT_AVAILABLE:
            raise ImportError("crowdkit requis: pip install crowdkit")
        self.model = DawidSkene(n_iter=n_iter, tol=tol)
        self.label_map = {"FAIBLE": 0, "PROBABLE": 1, "FORT": 2}
        self.reverse_map = {v: k for k, v in self.label_map.items()}
    
    def prepare_dataframe(self, clusters: List[ClusteredAssertion]) -> "pd.DataFrame":
        """Convertit clusters en DataFrame Crowd-Kit: task, worker, label."""
        import pandas as pd
        
        rows = []
        for task_id, cluster in enumerate(clusters):
            for assertion in cluster.assertions:
                if assertion.confidence in self.label_map:
                    rows.append({
                        "task": task_id,
                        "worker": assertion.instance_id,
                        "label": self.label_map[assertion.confidence]
                    })
        
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["task", "worker", "label"])
    
    def aggregate(self, clusters: List[ClusteredAssertion]) -> List[ClusteredAssertion]:
        """
        Applique Dawid-Skene et met à jour clusters avec label agrégé.
        
        Returns clusters avec champ 'ds_label' (label Dawid-Skene) et 'ds_proba' (probabilité).
        """
        import pandas as pd
        
        df = self.prepare_dataframe(clusters)
        if df.empty:
            return clusters
        
        # Fit Dawid-Skene
        result = self.model.fit_predict(df)
        
        # result est une Series indexée par task_id avec label prédit
        # Probabilités disponibles via model.prob_
        
        for task_id, cluster in enumerate(clusters):
            if task_id in result.index:
                ds_label = result[task_id]
                cluster.ds_label = self.reverse_map.get(ds_label, "FAIBLE")
                
                # Probabilité du label prédit
                if hasattr(self.model, 'prob_') and task_id < len(self.model.prob_):
                    probs = self.model.prob_[task_id]
                    cluster.ds_proba = float(np.max(probs))
                else:
                    cluster.ds_proba = 1.0
            else:
                cluster.ds_label = "FAIBLE"
                cluster.ds_proba = 0.0
        
        return clusters


def majority_vote_aggregation(
    clusters: List[ClusteredAssertion],
    vote_threshold: float = 2/3  # ≥2/3 instances
) -> List[ClusteredAssertion]:
    """
    Agrégation P1/P2 : vote majoritaire simple sur clusters.
    
    Règle : cluster retenu si instance_count / N_instances >= vote_threshold.
    Pour N=3, seuil 2/3 = au moins 2 instances.
    """
    N_INSTANCES = 3  # Fixé §2 protocole
    
    for cluster in clusters:
        cluster.retained = (cluster.instance_count / N_INSTANCES) >= vote_threshold
        cluster.vote_ratio = cluster.instance_count / N_INSTANCES
    
    return clusters


def load_assertions_from_pipeline_output(
    output_path: str,
    instance_id: str
) -> List[Assertion]:
    """Charge assertions depuis sortie JSONL d'un pipeline (1 ligne = 1 assertion)."""
    assertions = []
    with open(output_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            assertions.append(Assertion(
                instance_id=instance_id,
                text=data.get("text", ""),
                source_ref=data.get("source_ref", {}),
                confidence=data.get("confidence"),
                reasoning=data.get("reasoning")
            ))
    return assertions


def save_clusters_to_jsonl(clusters: List[ClusteredAssertion], output_path: str) -> None:
    """Sauvegarde clusters agrégés en JSONL pour métriques."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for cluster in clusters:
            f.write(json.dumps(cluster.to_dict(), ensure_ascii=False) + "\n")


# === Test unitaire Sprint 1 ===
def test_semantic_clustering():
    """Test clustering basique."""
    clusterer = SemanticClusterer(similarity_threshold=0.5)
    
    assertions = [
        Assertion("inst_1", "Le projet coûte 10M€", {"session_id": "s1", "tour_n": 5}),
        Assertion("inst_2", "Le budget est de 10 millions d'euros", {"session_id": "s1", "tour_n": 5}),
        Assertion("inst_3", "La deadline est mars 2025", {"session_id": "s1", "tour_n": 8}),
    ]
    
    clusters = clusterer.cluster(assertions)
    
    # Doit former 2 clusters : s1t5 (2 assertions similaires) + s1t8 (1 assertion)
    assert len(clusters) == 2
    cluster_s1t5 = next(c for c in clusters if c.source_ref["tour_n"] == 5)
    assert cluster_s1t5.instance_count == 2
    
    print("[OK] test_semantic_clustering passed")


def test_majority_vote():
    """Test vote majoritaire P1/P2."""
    clusters = [
        ClusteredAssertion([], "A", {"session_id": "s1", "tour_n": 1}, 3),  # 3/3 = retained
        ClusteredAssertion([], "B", {"session_id": "s1", "tour_n": 2}, 2),  # 2/3 = retained
        ClusteredAssertion([], "C", {"session_id": "s1", "tour_n": 3}, 1),  # 1/3 = rejected
    ]
    
    result = majority_vote_aggregation(clusters)
    
    assert result[0].retained == True
    assert result[1].retained == True
    assert result[2].retained == False
    
    print("[OK] test_majority_vote passed")


if __name__ == "__main__":
    test_semantic_clustering()
    test_majority_vote()
    print("\n✅ Tests agrégation passent")