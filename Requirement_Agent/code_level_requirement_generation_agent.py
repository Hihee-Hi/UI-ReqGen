import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .artifacts import save_requirement_list_as_json
from .openai_client import chat_completion


CODE_LEVEL_REQUIREMENT_GENERATION_PROMPT = """
Follow these steps strictly and output only the final result in Step 8:
1. Silently identify the programming language used in the UI-layer code.
2. As an expert developer, analyze the provided code snippet to identify
requirement-relevant functional elements, including:
- Core functional behaviors
- Key user-related operations
- Constraint and rule logic
- Data operation types, such as creation, validation, update, transfer, or retrieval
3. Check whether the code contains comments:
- If comments are present, proceed to Step 4
- If comments are absent, skip to Step 5
4. Analyze the semantic meaning of the code comments and identify any functional
intent they imply.
5. Determine whether meaningful naming identifiers exist, such as methods,
classes, variables, or UI elements:
- If meaningful naming is present, proceed to Step 6
- If meaningful naming is absent, skip to Step 7
6. Infer the functional intent by combining comment semantics, naming semantics,
and requirement-relevant code behavior.
7. Abstract away implementation details and extract the core functional intent of
the code within its usage context.
8. Output from the perspective of a user of the system, describing how the user can
achieve the functionality through interaction. The plain text output should not
contain markdown or implementation-specific terminology, such as dao, action, jsp,
class, method, variable, API, database, or controller. The output should:
- Focus on user-facing scenarios and workflows
- Describe the functionality supported by the code
- Use requirement-oriented language rather than implementation jargon
- Highlight domain-specific characteristics when supported by the code
""".strip()

DEFAULT_UI_LAYER_EXTENSIONS = (".java", ".jsp")
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}


def normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/")


def normalize_extensions(file_extensions: Optional[Sequence[str]]) -> tuple[str, ...]:
    if not file_extensions:
        return DEFAULT_UI_LAYER_EXTENSIONS
    normalized = []
    for extension in file_extensions:
        extension = extension.strip().lower()
        if not extension:
            continue
        normalized.append(extension if extension.startswith(".") else f".{extension}")
    return tuple(normalized) or DEFAULT_UI_LAYER_EXTENSIONS


def get_ui_layer_files(
    ui_layer_code_dir: str,
    file_extensions: Optional[Sequence[str]] = None,
) -> List[str]:
    root = Path(ui_layer_code_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"UI-layer code directory does not exist: {root}")

    extensions = normalize_extensions(file_extensions)
    code_files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in EXCLUDED_DIRECTORY_NAMES
        )
        for filename in sorted(filenames):
            if filename.lower().endswith(extensions):
                code_files.append(str(Path(dirpath) / filename))
    return code_files


def read_source_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(path).read_text(encoding="latin-1")


def output_path_for_requirement(
    output_dir: str,
    relative_path: str,
) -> Path:
    safe_name = normalize_relative_path(relative_path).replace("/", "__")
    return Path(output_dir) / f"{safe_name}.txt"


def generate_code_level_requirement(
    content: str,
    relative_path: str,
    model: Optional[str] = None,
) -> str:
    user_prompt = f"{normalize_relative_path(relative_path)}:\n{content}"
    return chat_completion(
        system_prompt=CODE_LEVEL_REQUIREMENT_GENERATION_PROMPT,
        user_prompt=user_prompt,
        model=model,
    )


def process_ui_layer_files(
    ui_layer_code_dir: str,
    code_level_requirement_output_dir: Optional[str],
    generation_model: Optional[str] = None,
    ui_layer_file_extensions: Optional[Sequence[str]] = None,
) -> List[Dict[str, str]]:
    code_files = get_ui_layer_files(ui_layer_code_dir, ui_layer_file_extensions)
    if code_level_requirement_output_dir:
        Path(code_level_requirement_output_dir).mkdir(parents=True, exist_ok=True)

    code_level_requirements: List[Dict[str, str]] = []
    for code_path in code_files:
        relative_path = normalize_relative_path(
            os.path.relpath(code_path, ui_layer_code_dir)
        )
        cached_output_path = (
            output_path_for_requirement(code_level_requirement_output_dir, relative_path)
            if code_level_requirement_output_dir
            else None
        )

        if cached_output_path and cached_output_path.exists():
            generated_requirement = cached_output_path.read_text(encoding="utf-8")
        else:
            source_content = read_source_file(code_path)
            generated_requirement = generate_code_level_requirement(
                source_content,
                relative_path,
                model=generation_model,
            )
            if cached_output_path:
                cached_output_path.write_text(generated_requirement, encoding="utf-8")
            time.sleep(1)

        code_level_requirements.append({relative_path: generated_requirement})

    return code_level_requirements


def generate_code_level_requirements_node(state: Dict) -> Dict:
    code_level_requirements = process_ui_layer_files(
        ui_layer_code_dir=state["ui_layer_code_dir"],
        code_level_requirement_output_dir=state.get(
            "code_level_requirement_output_dir"
        ),
        generation_model=state.get("generation_model"),
        ui_layer_file_extensions=state.get("ui_layer_file_extensions"),
    )
    save_requirement_list_as_json(
        state,
        "01_code_level_requirement_generation/code_level_requirements.json",
        code_level_requirements,
    )
    return {"code_level_requirements": code_level_requirements}
