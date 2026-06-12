import json
from typing import Dict

from .artifacts import save_json, save_text
from .openai_client import chat_completion


REQUIREMENT_EVALUATION_PROMPT = """
Assume you are a software requirements analyst. Two clustering methods
(K-MEANS, HIERARCHY) have been applied to cluster the same set of
requirement texts, and a summary of the requirements for each cluster
has been provided. Next, you will be given two sets of summaries based on the
clustering results of the requirement texts.

Please perform a horizontal comparison of the two clustering methods based on
the following three aspects to evaluate which clustering method is the best:
1. The number of clusters is appropriate (e.g., whether it is too few or too many).
   Considering that extracting requirements from the project requires more detailed
   classification and listing, please appropriately break down and enumerate the
   more specific situations.
2. Whether there is a clear thematic distinction between the clusters
   (avoiding repetition or ambiguity).
3. Whether the summary for each cluster is readable and clear in meaning.

Please indicate which clustering method you think performs the best and briefly explain why.
""".strip()


def evaluate_system_level_requirements_node(state: Dict) -> Dict:
    kmeans_summary = {
        str(cluster_id): summary
        for cluster_id, summary in state.get(
            "kmeans_system_level_requirements",
            {},
        ).items()
    }
    hca_summary = {
        str(cluster_id): summary
        for cluster_id, summary in state.get(
            "hca_system_level_requirements",
            {},
        ).items()
    }

    user_prompt = (
        "K-MEANS system-level outputs:\n"
        f"{json.dumps(kmeans_summary, indent=2, ensure_ascii=False)}\n\n"
        "Hierarchical clustering system-level outputs:\n"
        f"{json.dumps(hca_summary, indent=2, ensure_ascii=False)}"
    )
    evaluation_result = chat_completion(
        system_prompt=REQUIREMENT_EVALUATION_PROMPT,
        user_prompt=user_prompt,
        model=state.get("generation_model"),
    )
    save_text(
        state,
        "07_requirement_evaluation/requirement_evaluation_result.txt",
        evaluation_result,
    )
    save_json(
        state,
        "07_requirement_evaluation/requirement_evaluation_input.json",
        {
            "kmeans_system_level_requirements": kmeans_summary,
            "hca_system_level_requirements": hca_summary,
        },
    )
    return {"requirement_evaluation_result": evaluation_result}
