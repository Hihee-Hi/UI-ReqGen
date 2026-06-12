import argparse
import json
import math
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Type

from pydantic import BaseModel, Field

from Requirement_Agent.openai_client import chat_completion


class SystemRequirement(BaseModel):
    req_id: str = Field(description="Stable ID, e.g. SR-01")
    title: str = Field(description="Short system-level requirement title")
    description: str = Field(
        description="2-4 sentence user/stakeholder-facing functional description"
    )
    source_files: List[str] = Field(
        default_factory=list,
        description="Relevant source txt files",
    )


class SystemRequirementSet(BaseModel):
    requirements: List[SystemRequirement]


class ChunkTheme(BaseModel):
    theme_id: str
    title: str
    description: str
    source_files: List[str] = Field(default_factory=list)


class ChunkSummary(BaseModel):
    chunk_id: str
    themes: List[ChunkTheme]


DIRECT_SYSTEM_REQUIREMENT_PROMPT = """
You are an expert requirements engineer.

Your task is to synthesize a set of CODE-LEVEL functional requirements into a
smaller set of SYSTEM-LEVEL functional requirements for the same software project.

Instructions:
1. Merge overlapping or near-duplicate code-level requirements into broader
functional themes.
2. Focus on user-visible or stakeholder-relevant functionality.
3. Do NOT hallucinate unsupported functionality.
4. Do NOT merely paraphrase file-level requirements one by one.
5. Abstract away low-level implementation details, UI widget names, code
identifiers, and file-local mechanics.
6. Keep only functional content. Ignore purely technical plumbing unless it is
clearly user-facing functionality.
7. Use source_files to record which txt files most strongly support each
synthesized requirement.
8. Output 6-20 system-level requirements depending on project size.

You MUST return valid JSON only.
Do NOT use markdown.
Do NOT wrap the JSON in ```json fences.

Required JSON format:
{
  "requirements": [
    {
      "req_id": "SR-01",
      "title": "Requirement title",
      "description": "2-4 sentence user/stakeholder-facing functional description.",
      "source_files": ["file1.txt", "module/file2.txt"]
    }
  ]
}
""".strip()


CHUNK_SUMMARY_PROMPT = """
You are an expert requirements engineer.

You are given ONE CHUNK of code-level functional requirements from a software
project. Summarize this chunk into a SMALL set of LOCAL THEMES.

Instructions:
1. Merge overlapping items inside this chunk only.
2. Focus on functional meaning, not implementation details.
3. Do NOT invent missing functionality.
4. Keep the themes local to this chunk; do not assume knowledge outside this
chunk.
5. Use source_files to record which txt files support each local theme.
6. Produce around 3-8 local themes depending on chunk size.

You MUST return valid JSON only.
Do NOT use markdown.
Do NOT wrap the JSON in ```json fences.

Required JSON format:
{
  "chunk_id": "chunk-01",
  "themes": [
    {
      "theme_id": "T-01",
      "title": "Theme title",
      "description": "A concise functional theme summary.",
      "source_files": ["file1.txt", "module/file2.txt"]
    }
  ]
}
""".strip()


CHUNK_REDUCTION_PROMPT = """
You are an expert requirements engineer.

You are given a set of CHUNK-LEVEL local themes that were summarized from
code-level requirements. Your task is to merge these local themes into final
SYSTEM-LEVEL functional requirements.

Instructions:
1. Merge duplicates and semantically overlapping themes across chunks.
2. Produce coherent project-level functional abstractions.
3. Focus on user/stakeholder-facing functionality.
4. Do NOT include low-level implementation details.
5. Do NOT hallucinate unsupported functionality.
6. Preserve traceability using source_files.
7. Output 6-20 system-level requirements depending on project size.

You MUST return valid JSON only.
Do NOT use markdown.
Do NOT wrap the JSON in ```json fences.

Required JSON format:
{
  "requirements": [
    {
      "req_id": "SR-01",
      "title": "Requirement title",
      "description": "2-4 sentence user/stakeholder-facing functional description.",
      "source_files": ["file1.txt", "module/file2.txt"]
    }
  ]
}
""".strip()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned: List[str] = []
    previous_line_blank = False
    for line in lines:
        if not line.strip():
            if not previous_line_blank:
                cleaned.append("")
            previous_line_blank = True
            continue
        cleaned.append(line)
        previous_line_blank = False
    return "\n".join(cleaned).strip()


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def load_code_level_requirement_files(input_dir: str) -> List[Dict[str, str]]:
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    docs: List[Dict[str, str]] = []
    for path in sorted(root.rglob("*.txt")):
        if not path.is_file():
            continue
        content = normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
        if content:
            docs.append(
                {
                    "file_name": str(path.relative_to(root)).replace("\\", "/"),
                    "text": content,
                }
            )

    if not docs:
        raise ValueError(f"No non-empty .txt files found in: {input_dir}")
    return docs


def format_documents_for_prompt(docs: List[Dict[str, str]]) -> str:
    blocks = []
    for index, doc in enumerate(docs, start=1):
        blocks.append(
            f"## Document {index}\n"
            f"FILE: {doc['file_name']}\n"
            f"CONTENT:\n{doc['text']}"
        )
    return "\n\n".join(blocks)


def chunk_documents_by_chars(
    docs: List[Dict[str, str]],
    max_chars: int,
) -> List[List[Dict[str, str]]]:
    chunks: List[List[Dict[str, str]]] = []
    current_chunk: List[Dict[str, str]] = []
    current_chars = 0

    for doc in docs:
        doc_chars = len(doc["text"]) + len(doc["file_name"]) + 64
        if doc_chars > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_chars = 0
            chunks.append([doc])
            continue

        if current_chunk and current_chars + doc_chars > max_chars:
            chunks.append(current_chunk)
            current_chunk = [doc]
            current_chars = doc_chars
            continue

        current_chunk.append(doc)
        current_chars += doc_chars

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def ensure_output_dir(output_dir: str) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump_model(model: BaseModel) -> Dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def validate_model(schema_cls: Type[BaseModel], data: Dict):
    if hasattr(schema_cls, "model_validate"):
        return schema_cls.model_validate(data)
    return schema_cls.parse_obj(data)


def render_system_requirements_markdown(
    requirement_set: SystemRequirementSet,
    title: str,
) -> str:
    parts = [f"# {title}", ""]
    for requirement in requirement_set.requirements:
        parts.append(f"## {requirement.req_id} - {requirement.title}")
        parts.append(requirement.description)
        if requirement.source_files:
            parts.append("")
            parts.append("**Source files:**")
            for source_file in requirement.source_files:
                parts.append(f"- {source_file}")
        parts.append("")
    return "\n".join(parts).strip() + "\n"


def render_chunk_summary_markdown(
    chunk_summary: ChunkSummary,
    title: str,
) -> str:
    parts = [f"# {title}", ""]
    for theme in chunk_summary.themes:
        parts.append(f"## {theme.theme_id} - {theme.title}")
        parts.append(theme.description)
        if theme.source_files:
            parts.append("")
            parts.append("**Source files:**")
            for source_file in theme.source_files:
                parts.append(f"- {source_file}")
        parts.append("")
    return "\n".join(parts).strip() + "\n"


def extract_json_text(text: str) -> str:
    if not text:
        raise ValueError("Empty response from model.")

    stripped_text = text.strip()
    fenced_match = re.search(
        r"```(?:json)?\s*(.*?)```",
        stripped_text,
        re.DOTALL | re.IGNORECASE,
    )
    if fenced_match:
        return fenced_match.group(1).strip()

    start = stripped_text.find("{")
    end = stripped_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped_text[start : end + 1]

    raise ValueError(
        "Could not extract JSON from model output:\n"
        f"{stripped_text[:1000]}"
    )


class RequirementBaselineRunner:
    def __init__(self, model: str, max_retries: int = 5):
        self.model = model
        self.max_retries = max_retries

    def call_json_model(
        self,
        schema_cls: Type[BaseModel],
        system_prompt: str,
        user_prompt: str,
    ):
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw_text = chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=self.model,
                )
                json_text = extract_json_text(raw_text)
                data = json.loads(json_text)
                return validate_model(schema_cls, data)
            except Exception as exc:
                last_error = exc
                sleep_seconds = min(2**attempt, 20)
                print(
                    f"[WARN] API call failed "
                    f"(attempt {attempt}/{self.max_retries}): {exc}"
                )
                if attempt < self.max_retries:
                    time.sleep(sleep_seconds)

        raise RuntimeError(
            f"API call failed after {self.max_retries} retries: {last_error}"
        )

    def run_direct_llm_summarization(
        self,
        project_name: str,
        docs: List[Dict[str, str]],
    ) -> SystemRequirementSet:
        corpus = format_documents_for_prompt(docs)
        user_prompt = (
            f"Project name: {project_name}\n\n"
            "Below are code-level requirements extracted from source files.\n\n"
            f"{corpus}\n\n"
            "Please synthesize final system-level functional requirements."
        )
        return self.call_json_model(
            SystemRequirementSet,
            DIRECT_SYSTEM_REQUIREMENT_PROMPT,
            user_prompt,
        )

    def summarize_chunk(
        self,
        project_name: str,
        chunk_id: str,
        docs: List[Dict[str, str]],
    ) -> ChunkSummary:
        corpus = format_documents_for_prompt(docs)
        user_prompt = (
            f"Project name: {project_name}\n"
            f"Chunk ID: {chunk_id}\n\n"
            "Below are code-level requirements in this chunk.\n\n"
            f"{corpus}\n\n"
            "Please summarize this chunk into local functional themes.\n"
            f'Remember: the "chunk_id" field in the JSON must be exactly '
            f'"{chunk_id}".'
        )
        result = self.call_json_model(ChunkSummary, CHUNK_SUMMARY_PROMPT, user_prompt)
        result.chunk_id = chunk_id
        return result

    def reduce_chunk_summaries(
        self,
        project_name: str,
        chunk_summaries: List[ChunkSummary],
    ) -> SystemRequirementSet:
        blocks: List[str] = []
        for summary in chunk_summaries:
            blocks.append(f"## {summary.chunk_id}")
            for theme in summary.themes:
                blocks.append(f"THEME ID: {theme.theme_id}")
                blocks.append(f"TITLE: {theme.title}")
                blocks.append(f"DESCRIPTION: {theme.description}")
                blocks.append(f"SOURCE FILES: {', '.join(theme.source_files)}")
                blocks.append("")

        user_prompt = (
            f"Project name: {project_name}\n\n"
            "Below are chunk-level local themes.\n\n"
            f"{chr(10).join(blocks)}\n\n"
            "Please merge them into final system-level functional requirements."
        )
        return self.call_json_model(
            SystemRequirementSet,
            CHUNK_REDUCTION_PROMPT,
            user_prompt,
        )


def run_direct_baseline(
    runner: RequirementBaselineRunner,
    project_name: str,
    docs: List[Dict[str, str]],
    output_dir: Path,
) -> None:
    print("\n[INFO] Running baseline: Direct LLM Summarization")
    result = runner.run_direct_llm_summarization(project_name, docs)

    json_path = output_dir / "direct_llm_system_level_requirements.json"
    markdown_path = output_dir / "direct_llm_system_level_requirements.md"
    save_json(json_path, dump_model(result))
    save_text(
        markdown_path,
        render_system_requirements_markdown(
            result,
            f"{project_name} - Direct LLM Summarization",
        ),
    )
    print(f"[DONE] Saved: {json_path}")
    print(f"[DONE] Saved: {markdown_path}")


def run_chunked_baseline(
    runner: RequirementBaselineRunner,
    project_name: str,
    docs: List[Dict[str, str]],
    output_dir: Path,
    chunk_chars: int,
) -> None:
    print("\n[INFO] Running baseline: Naive Chunk-based Summarization")
    chunks = chunk_documents_by_chars(docs, max_chars=chunk_chars)
    print(f"[INFO] Number of chunks: {len(chunks)}")

    chunk_output_dir = output_dir / "chunk_intermediates"
    chunk_summaries: List[ChunkSummary] = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = f"chunk-{index:02d}"
        print(f"[INFO] Summarizing {chunk_id} ({len(chunk)} files)")
        summary = runner.summarize_chunk(project_name, chunk_id, chunk)
        chunk_summaries.append(summary)

        save_json(chunk_output_dir / f"{chunk_id}.json", dump_model(summary))
        save_text(
            chunk_output_dir / f"{chunk_id}.md",
            render_chunk_summary_markdown(
                summary,
                f"{project_name} - {chunk_id} local themes",
            ),
        )

    final_result = runner.reduce_chunk_summaries(project_name, chunk_summaries)
    json_path = output_dir / "chunked_system_level_requirements.json"
    markdown_path = output_dir / "chunked_system_level_requirements.md"
    save_json(json_path, dump_model(final_result))
    save_text(
        markdown_path,
        render_system_requirements_markdown(
            final_result,
            f"{project_name} - Naive Chunk-based Summarization",
        ),
    )
    print(f"[DONE] Saved: {json_path}")
    print(f"[DONE] Saved: {markdown_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run requirement-generation baselines from code-level requirement txt files."
        )
    )
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument(
        "--baseline",
        default="both",
        choices=["direct", "chunked", "both"],
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Generation model. Credentials are read from OPENAI_API_KEY and OPENAI_BASE_URL.",
    )
    parser.add_argument("--chunk-chars", type=int, default=120_000)
    parser.add_argument("--max-retries", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    docs = load_code_level_requirement_files(args.input_dir)
    print(f"[INFO] Loaded {len(docs)} txt files")

    total_text = format_documents_for_prompt(docs)
    print(f"[INFO] Rough total token estimate: ~{estimate_tokens(total_text):,}")

    runner = RequirementBaselineRunner(
        model=args.model,
        max_retries=args.max_retries,
    )

    if args.baseline in {"direct", "both"}:
        run_direct_baseline(
            runner=runner,
            project_name=args.project_name,
            docs=docs,
            output_dir=output_dir,
        )

    if args.baseline in {"chunked", "both"}:
        run_chunked_baseline(
            runner=runner,
            project_name=args.project_name,
            docs=docs,
            output_dir=output_dir,
            chunk_chars=args.chunk_chars,
        )

    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()
