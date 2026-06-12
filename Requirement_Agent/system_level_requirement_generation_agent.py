from typing import Dict, Iterable, List, Optional

from .artifacts import save_json, save_requirement_dict_as_text_files
from .openai_client import chat_completion


SYSTEM_LEVEL_REQUIREMENT_GENERATION_PROMPT = """
You will receive a cluster of code-level requirement descriptions generated from
multiple UI-layer files. Each file is in the following format:
{relative_path}:
{code_level_requirement_description}

Your task is to synthesize system-level functional requirements from the provided
descriptions. Focus on summarizing the key functionalities represented by this
cluster in concise, clear, and structured language. Maintain the core themes and
commonalities within the cluster while ensuring the summary is actionable and
focused on system-level functional requirements.

Only return the summary content; there is no need for the code paths or other
explanations.
""".strip()


def code_level_requirements_to_dict(
    filtered_code_level_requirements: Iterable[Dict[str, str]],
) -> Dict[str, str]:
    requirements_by_path: Dict[str, str] = {}
    for item in filtered_code_level_requirements:
        requirements_by_path.update(item)
    return requirements_by_path


def summarize_requirement_clusters(
    clusters: Dict[int, List[str]],
    requirements_by_path: Dict[str, str],
    generation_model: Optional[str] = None,
) -> Dict[int, str]:
    system_level_requirements: Dict[int, str] = {}
    for cluster_id, file_paths in sorted(clusters.items(), key=lambda item: int(item[0])):
        cluster_content = "\n\n".join(
            f"{path}:\n{requirements_by_path.get(path, '')}" for path in file_paths
        ).strip()
        if not cluster_content:
            continue
        system_level_requirements[int(cluster_id)] = chat_completion(
            system_prompt=SYSTEM_LEVEL_REQUIREMENT_GENERATION_PROMPT,
            user_prompt=cluster_content,
            model=generation_model,
        )
    return system_level_requirements


def generate_system_level_requirements_node(state: Dict) -> Dict:
    requirements_by_path = code_level_requirements_to_dict(
        state.get("filtered_code_level_requirements", [])
    )
    kmeans_system_level_requirements = summarize_requirement_clusters(
        state.get("kmeans_clusters", {}),
        requirements_by_path,
        generation_model=state.get("generation_model"),
    )
    hca_system_level_requirements = summarize_requirement_clusters(
        state.get("hca_clusters", {}),
        requirements_by_path,
        generation_model=state.get("generation_model"),
    )
    save_json(
        state,
        "06_system_level_requirement_generation/kmeans_system_level_requirements.json",
        kmeans_system_level_requirements,
    )
    save_requirement_dict_as_text_files(
        state,
        "06_system_level_requirement_generation/kmeans_system_level_requirements",
        kmeans_system_level_requirements,
    )
    save_json(
        state,
        "06_system_level_requirement_generation/hca_system_level_requirements.json",
        hca_system_level_requirements,
    )
    save_requirement_dict_as_text_files(
        state,
        "06_system_level_requirement_generation/hca_system_level_requirements",
        hca_system_level_requirements,
    )
    return {
        "kmeans_system_level_requirements": kmeans_system_level_requirements,
        "hca_system_level_requirements": hca_system_level_requirements,
    }
