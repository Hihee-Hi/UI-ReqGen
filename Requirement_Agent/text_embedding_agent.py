from typing import Dict, List

from .artifacts import compact_embedding_metadata, save_json
from .openai_client import create_embedding


def embed_code_level_requirements_node(state: Dict) -> Dict:
    filtered_code_level_requirements = state.get("filtered_code_level_requirements", [])
    embedding_model = state.get("embedding_model")

    requirement_embeddings: List[Dict[str, List[float]]] = []
    for item in filtered_code_level_requirements:
        for relative_path, requirement_text in item.items():
            embedding = create_embedding(
                text=requirement_text,
                model=embedding_model,
            )
            requirement_embeddings.append({relative_path: embedding})

    save_json(
        state,
        "03_text_embedding/requirement_embeddings.json",
        requirement_embeddings,
    )
    save_json(
        state,
        "03_text_embedding/requirement_embedding_metadata.json",
        compact_embedding_metadata(requirement_embeddings),
    )
    return {"requirement_embeddings": requirement_embeddings}
