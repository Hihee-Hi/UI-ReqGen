import argparse
import json
import os
from typing import Annotated, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from Requirement_Agent.code_level_requirement_generation_agent import (
    generate_code_level_requirements_node,
)
from Requirement_Agent.hca_clustering import cluster_requirements_with_hca_node
from Requirement_Agent.kmeans_clustering import cluster_requirements_with_kmeans_node
from Requirement_Agent.non_functional_requirement_filtering_agent import (
    filter_non_functional_requirements_node,
)
from Requirement_Agent.requirement_evaluation_agent import (
    evaluate_system_level_requirements_node,
)
from Requirement_Agent.system_level_requirement_generation_agent import (
    generate_system_level_requirements_node,
)
from Requirement_Agent.text_embedding_agent import embed_code_level_requirements_node


class UIReqGenState(TypedDict, total=False):
    ui_layer_code_dir: Annotated[str, "Input"]
    code_level_requirement_output_dir: Annotated[str, "Input"]
    artifact_output_dir: Annotated[str, "Output"]
    ui_layer_file_extensions: List[str]
    generation_model: str
    embedding_model: str
    code_level_requirements: List[Dict[str, str]]
    filtered_code_level_requirements: List[Dict[str, str]]
    nfr_filtered_paths: List[str]
    requirement_embeddings: List[Dict[str, List[float]]]
    kmeans_clusters: Dict[int, List[str]]
    hca_clusters: Dict[int, List[str]]
    kmeans_system_level_requirements: Dict[int, str]
    hca_system_level_requirements: Dict[int, str]
    requirement_evaluation_result: str


def build_ui_reqgen_graph():
    builder = StateGraph(state_schema=UIReqGenState)
    builder.add_node(
        "code_level_requirement_generation",
        generate_code_level_requirements_node,
    )
    builder.add_node(
        "non_functional_requirement_filtering",
        filter_non_functional_requirements_node,
    )
    builder.add_node("text_embedding", embed_code_level_requirements_node)
    builder.add_node("kmeans_clustering", cluster_requirements_with_kmeans_node)
    builder.add_node("hca_clustering", cluster_requirements_with_hca_node)
    builder.add_node(
        "system_level_requirement_generation",
        generate_system_level_requirements_node,
    )
    builder.add_node("requirement_evaluation", evaluate_system_level_requirements_node)

    builder.set_entry_point("code_level_requirement_generation")
    builder.add_edge(
        "code_level_requirement_generation",
        "non_functional_requirement_filtering",
    )
    builder.add_edge("non_functional_requirement_filtering", "text_embedding")
    builder.add_edge("text_embedding", "kmeans_clustering")
    builder.add_edge("kmeans_clustering", "hca_clustering")
    builder.add_edge("hca_clustering", "system_level_requirement_generation")
    builder.add_edge("system_level_requirement_generation", "requirement_evaluation")
    builder.add_edge("requirement_evaluation", END)
    return builder.compile()


def run_ui_reqgen_pipeline(
    ui_layer_code_dir: str,
    code_level_requirement_output_dir: str,
    artifact_output_dir: str,
    generation_model: Optional[str] = None,
    embedding_model: Optional[str] = None,
    ui_layer_file_extensions: Optional[List[str]] = None,
) -> UIReqGenState:
    graph = build_ui_reqgen_graph()
    inputs: UIReqGenState = {
        "ui_layer_code_dir": ui_layer_code_dir,
        "code_level_requirement_output_dir": code_level_requirement_output_dir,
        "artifact_output_dir": artifact_output_dir,
    }
    if generation_model:
        inputs["generation_model"] = generation_model
    if embedding_model:
        inputs["embedding_model"] = embedding_model
    if ui_layer_file_extensions:
        inputs["ui_layer_file_extensions"] = ui_layer_file_extensions
    return graph.invoke(inputs)


def print_ui_reqgen_result(result: UIReqGenState) -> None:
    print("\n[UI-ReqGen] Artifact output directory:")
    print(result.get("artifact_output_dir", "ui_reqgen_artifacts"))

    print("\n[UI-ReqGen] Code-level requirements:")
    print(len(result.get("code_level_requirements", [])))

    print("\n[UI-ReqGen] Filtered code-level requirements:")
    print(len(result.get("filtered_code_level_requirements", [])))
    filtered_paths = result.get("nfr_filtered_paths", [])
    if filtered_paths:
        print("Removed by NFR filtering:")
        print(json.dumps(filtered_paths, ensure_ascii=False, indent=2))

    print("\n[UI-ReqGen] K-Means clusters:")
    print(json.dumps(result.get("kmeans_clusters", {}), ensure_ascii=False, indent=2))

    print("\n[UI-ReqGen] HCA clusters:")
    print(json.dumps(result.get("hca_clusters", {}), ensure_ascii=False, indent=2))

    print("\n[UI-ReqGen] K-Means system-level requirements:")
    print(
        json.dumps(
            result.get("kmeans_system_level_requirements", {}),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n[UI-ReqGen] HCA system-level requirements:")
    print(
        json.dumps(
            result.get("hca_system_level_requirements", {}),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n[UI-ReqGen] Requirement evaluation result:")
    print(result.get("requirement_evaluation_result", ""))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the paper-aligned UI-ReqGen multi-agent framework."
    )
    parser.add_argument(
        "--ui-layer-code-dir",
        required=True,
        help="Directory containing UI-layer source files.",
    )
    parser.add_argument(
        "--code-level-requirement-output-dir",
        default="ui_reqgen_code_level_requirements",
        help="Directory used to cache generated code-level requirements.",
    )
    parser.add_argument(
        "--artifact-output-dir",
        default="ui_reqgen_artifacts",
        help="Directory used to save outputs from all downstream agents.",
    )
    parser.add_argument(
        "--generation-model",
        default=os.getenv("UI_REQGEN_GENERATION_MODEL", "gpt-4o"),
        help="LLM used by generation and evaluation agents.",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("UI_REQGEN_EMBEDDING_MODEL", "text-embedding-3-large"),
        help="Embedding model used by the text embedding agent.",
    )
    parser.add_argument(
        "--file-extension",
        action="append",
        dest="ui_layer_file_extensions",
        help="UI-layer file extension to process. Repeat for multiple values.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pipeline_result = run_ui_reqgen_pipeline(
        ui_layer_code_dir=args.ui_layer_code_dir,
        code_level_requirement_output_dir=args.code_level_requirement_output_dir,
        artifact_output_dir=args.artifact_output_dir,
        generation_model=args.generation_model,
        embedding_model=args.embedding_model,
        ui_layer_file_extensions=args.ui_layer_file_extensions,
    )
    print_ui_reqgen_result(pipeline_result)
