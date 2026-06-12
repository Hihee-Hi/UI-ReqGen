import ast
import json
from typing import Dict, Iterable, List, Optional

from .artifacts import save_json, save_requirement_list_as_json
from .openai_client import chat_completion


NON_FUNCTIONAL_REQUIREMENT_FILTERING_PROMPT = """
You are given a set of UI-layer files that have been converted into code-level
requirement descriptions in the format: {relative_path: requirement_description}.
These descriptions were generated to recover functional requirement information
from UI-layer files. However, some descriptions may contain NFR-related,
infrastructure-oriented, or irrelevant content.

Please review each code-level requirement description and identify any files that
should be removed because they contain NFR-related, infrastructure-oriented, or
otherwise irrelevant content.

Additional context:
1. The input may contain UI-layer code files written in different technologies
(e.g., JSP or Java/Vaadin), depending on the target project.
2. Definitions:
- Functional Requirements (FRs): Specific functions or services the system must
provide. These describe what the system must do and are typically user-facing.
Examples include: user login, data search, button interactions, or order submissions
in an e-commerce application.
- Non-Functional Requirements (NFRs): Constraints on how the system operates,
rather than what it does. These refer to performance, security, maintainability,
scalability, development cost, memory usage limits, or general usability. NFRs do
not involve specific user-visible actions but influence overall system quality.
3. Your task:
a. Analyze each code-level requirement description.
b. Return a JSON list of relative file paths that should be removed because they
contain NFR-related, infrastructure-oriented, or otherwise irrelevant content.

Important:
- Only return the JSON array of strings. Do not include explanations or additional
text.
- If no files should be removed, return: []
- I will provide the format as {path}: {content}, please only give me the JSON for
the content of the path.

Example:
["src/ui/Settings.java", "src/utils/Logger.java"]
""".strip()


def normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/")


def code_level_requirements_to_dict(
    code_level_requirements: Iterable[Dict[str, str]],
) -> Dict[str, str]:
    requirements_by_path: Dict[str, str] = {}
    for item in code_level_requirements:
        for path, requirement in item.items():
            requirements_by_path[normalize_relative_path(path)] = requirement
    return requirements_by_path


def strip_fenced_response(response: str) -> str:
    text = response.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_paths_to_filter(response: str) -> List[str]:
    text = strip_fenced_response(response)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        text = text[start : end + 1]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(text)

    if not isinstance(parsed, list):
        raise ValueError("NFR filtering response must be a JSON array.")
    return [normalize_relative_path(str(path)) for path in parsed]


def identify_non_functional_requirement_paths(
    code_level_requirements: List[Dict[str, str]],
    generation_model: Optional[str] = None,
) -> List[str]:
    requirements_by_path = code_level_requirements_to_dict(code_level_requirements)
    if not requirements_by_path:
        return []

    user_prompt = "\n\n".join(
        f"{path}: {requirement}" for path, requirement in requirements_by_path.items()
    )
    response = chat_completion(
        system_prompt=NON_FUNCTIONAL_REQUIREMENT_FILTERING_PROMPT,
        user_prompt=user_prompt,
        model=generation_model,
    )
    return parse_paths_to_filter(response)


def filter_code_level_requirements_by_path(
    code_level_requirements: List[Dict[str, str]],
    paths_to_filter: List[str],
) -> List[Dict[str, str]]:
    normalized_paths_to_filter = set(
        normalize_relative_path(path) for path in paths_to_filter
    )
    filtered_requirements: List[Dict[str, str]] = []
    for item in code_level_requirements:
        for path, requirement in item.items():
            normalized_path = normalize_relative_path(path)
            if normalized_path not in normalized_paths_to_filter:
                filtered_requirements.append({normalized_path: requirement})
    return filtered_requirements


def filter_non_functional_requirements_node(state: Dict) -> Dict:
    code_level_requirements = state.get("code_level_requirements", [])
    paths_to_filter = identify_non_functional_requirement_paths(
        code_level_requirements,
        generation_model=state.get("generation_model"),
    )
    filtered_code_level_requirements = filter_code_level_requirements_by_path(
        code_level_requirements,
        paths_to_filter,
    )
    save_json(
        state,
        "02_non_functional_requirement_filtering/nfr_filtered_paths.json",
        paths_to_filter,
    )
    save_requirement_list_as_json(
        state,
        "02_non_functional_requirement_filtering/filtered_code_level_requirements.json",
        filtered_code_level_requirements,
    )
    return {
        "filtered_code_level_requirements": filtered_code_level_requirements,
        "nfr_filtered_paths": paths_to_filter,
    }
