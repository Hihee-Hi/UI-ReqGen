import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_ARTIFACT_OUTPUT_DIR = "ui_reqgen_artifacts"


def get_artifact_output_dir(state: Dict) -> Path:
    output_dir = state.get("artifact_output_dir") or DEFAULT_ARTIFACT_OUTPUT_DIR
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(state: Dict, relative_path: str, data: Any) -> Path:
    output_path = get_artifact_output_dir(state) / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def save_text(state: Dict, relative_path: str, text: str) -> Path:
    output_path = get_artifact_output_dir(state) / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def save_requirement_dict_as_text_files(
    state: Dict,
    directory: str,
    requirements: Dict[int, str],
) -> None:
    for requirement_id, text in sorted(requirements.items(), key=lambda item: int(item[0])):
        save_text(state, f"{directory}/cluster_{int(requirement_id)}.txt", text)


def save_requirement_list_as_json(
    state: Dict,
    relative_path: str,
    requirements: Iterable[Dict[str, str]],
) -> Path:
    return save_json(state, relative_path, list(requirements))


def compact_embedding_metadata(
    requirement_embeddings: List[Dict[str, List[float]]],
) -> List[Dict[str, Any]]:
    metadata: List[Dict[str, Any]] = []
    for item in requirement_embeddings:
        for path, embedding in item.items():
            metadata.append(
                {
                    "path": path,
                    "dimensions": len(embedding),
                }
            )
    return metadata
