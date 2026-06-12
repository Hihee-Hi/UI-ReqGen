import argparse
import json
import math
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from Requirement_Agent.openai_client import chat_completion, create_embedding


SYSTEM_LEVEL_MATCHING_PROMPT = """
You are a requirements analysis expert in the field of software engineering.

You are an expert requirement matching assistant.
Task:
Compare the following two requirement items (one from Document A and one from
Document B) and determine whether they should be classified as Match or No Match
according to the rules below.

Match: A generated requirement is classified as a match if its title and core
functional description are semantically aligned with a manually written
requirement and describe the same functionality, even if they differ in wording or
granularity.

No Match: A generated requirement is classified as no match if it does not
correspond to any manually written requirement in terms of core functionality.

Requirements:
1. Consider synonyms and paraphrases as equivalent when judging similarity.
2. Small differences in scope or level of detail should NOT prevent a Match if the
core functionality is the same.
3. Shared domain context alone is insufficient for a Match; the two requirements
must express the same main functionality.
4. Judge the most appropriate decision (Match or No Match).
5. Provide a short reason (one or two sentences) explaining your decision.
6. Output ONLY a valid JSON object in the following format:
{
  "decision": "Match" | "No Match",
  "reason": "<your explanation in English>"
}
Do not add any extra text before or after the JSON.
""".strip()


@dataclass
class RequirementItem:
    id: str
    title: str
    description: str

    @property
    def embedding_text(self) -> str:
        return f"{self.title}\n{self.description}".strip()


@dataclass
class CandidatePair:
    generated_id: str
    generated_title: str
    reference_id: str
    reference_title: str
    rank: int
    similarity: float


@dataclass
class MatchDecision:
    generated_id: str
    reference_id: str
    rank: int
    similarity: float
    decision: str
    reason: str


def load_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_requirement_item(item_id: str, payload: object) -> RequirementItem:
    if isinstance(payload, str):
        return RequirementItem(
            id=str(item_id),
            title=f"System-level requirement {item_id}",
            description=payload,
        )

    if not isinstance(payload, dict):
        raise ValueError(f"Unsupported requirement item for id {item_id}: {payload!r}")

    requirement_id = (
        payload.get("id")
        or payload.get("req_id")
        or payload.get("requirement_id")
        or item_id
    )
    title = payload.get("title") or f"System-level requirement {requirement_id}"
    description = payload.get("description") or payload.get("text") or payload.get("content")
    if description is None:
        raise ValueError(f"Requirement {requirement_id} is missing description/text.")
    return RequirementItem(
        id=str(requirement_id),
        title=str(title),
        description=str(description),
    )


def load_requirements(path: str) -> List[RequirementItem]:
    raw_data = load_json(path)

    if isinstance(raw_data, dict) and isinstance(raw_data.get("requirements"), list):
        return [
            normalize_requirement_item(str(index + 1), item)
            for index, item in enumerate(raw_data["requirements"])
        ]

    if isinstance(raw_data, list):
        return [
            normalize_requirement_item(str(index + 1), item)
            for index, item in enumerate(raw_data)
        ]

    if isinstance(raw_data, dict):
        return [
            normalize_requirement_item(str(item_id), payload)
            for item_id, payload in raw_data.items()
        ]

    raise ValueError(f"Unsupported requirement JSON format: {path}")


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if not norm_a or not norm_b:
        return 0.0
    return dot_product / (norm_a * norm_b)


def embed_requirements(
    requirements: Iterable[RequirementItem],
    embedding_model: str,
) -> Dict[str, List[float]]:
    embeddings: Dict[str, List[float]] = {}
    for requirement in requirements:
        embeddings[requirement.id] = create_embedding(
            text=requirement.embedding_text,
            model=embedding_model,
        )
    return embeddings


def retrieve_top_k_candidates(
    reference_requirements: List[RequirementItem],
    generated_requirements: List[RequirementItem],
    reference_embeddings: Dict[str, List[float]],
    generated_embeddings: Dict[str, List[float]],
    top_k: int,
) -> List[CandidatePair]:
    candidate_pairs: List[CandidatePair] = []
    for generated_requirement in generated_requirements:
        similarities = []
        generated_embedding = generated_embeddings[generated_requirement.id]
        for reference_requirement in reference_requirements:
            similarity = cosine_similarity(
                generated_embedding,
                reference_embeddings[reference_requirement.id],
            )
            similarities.append((reference_requirement, similarity))

        similarities.sort(key=lambda item: item[1], reverse=True)
        for rank, (reference_requirement, similarity) in enumerate(
            similarities[:top_k],
            start=1,
        ):
            candidate_pairs.append(
                CandidatePair(
                    generated_id=generated_requirement.id,
                    generated_title=generated_requirement.title,
                    reference_id=reference_requirement.id,
                    reference_title=reference_requirement.title,
                    rank=rank,
                    similarity=float(similarity),
                )
            )
    return candidate_pairs


def build_pair_prompt(
    reference_requirement: RequirementItem,
    generated_requirement: RequirementItem,
) -> str:
    return (
        "Document A:\n"
        f"id: {reference_requirement.id}\n"
        f"Title: {reference_requirement.title}\n"
        f"Description: {reference_requirement.description}\n\n"
        "Document B:\n"
        f"id: {generated_requirement.id}\n"
        f"Title: {generated_requirement.title}\n"
        f"Description: {generated_requirement.description}"
    )


def extract_json_object(text: str) -> Dict:
    stripped_text = text.strip()
    fenced_match = re.search(
        r"```(?:json)?\s*(.*?)```",
        stripped_text,
        re.DOTALL | re.IGNORECASE,
    )
    if fenced_match:
        stripped_text = fenced_match.group(1).strip()
    else:
        start = stripped_text.find("{")
        end = stripped_text.rfind("}")
        if start >= 0 and end > start:
            stripped_text = stripped_text[start : end + 1]

    parsed = json.loads(stripped_text)
    if parsed.get("decision") not in {"Match", "No Match"}:
        raise ValueError(f"Invalid decision in evaluator response: {parsed!r}")
    return parsed


def judge_candidate_pair(
    reference_requirement: RequirementItem,
    generated_requirement: RequirementItem,
    evaluator_model: str,
    max_retries: int,
) -> Dict[str, str]:
    user_prompt = build_pair_prompt(reference_requirement, generated_requirement)
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = chat_completion(
                system_prompt=SYSTEM_LEVEL_MATCHING_PROMPT,
                user_prompt=user_prompt,
                model=evaluator_model,
            )
            parsed = extract_json_object(response)
            return {
                "decision": parsed["decision"],
                "reason": str(parsed.get("reason", "")),
            }
        except Exception as exc:
            last_error = exc
            print(
                f"[WARN] Pair {generated_requirement.id}->{reference_requirement.id} "
                f"failed (attempt {attempt}/{max_retries}): {exc}"
            )
            if attempt < max_retries:
                time.sleep(min(2**attempt, 20))

    raise RuntimeError(
        "Evaluator failed after "
        f"{max_retries} retries for pair "
        f"{generated_requirement.id}->{reference_requirement.id}: {last_error}"
    )


def evaluate_candidate_pairs(
    reference_requirements: List[RequirementItem],
    generated_requirements: List[RequirementItem],
    candidate_pairs: List[CandidatePair],
    evaluator_model: str,
    max_retries: int,
) -> List[MatchDecision]:
    reference_by_id = {item.id: item for item in reference_requirements}
    generated_by_id = {item.id: item for item in generated_requirements}
    decisions: List[MatchDecision] = []

    for pair in candidate_pairs:
        print(
            f"[INFO] Judging generated {pair.generated_id} "
            f"against reference {pair.reference_id} (rank {pair.rank})"
        )
        judgment = judge_candidate_pair(
            reference_requirement=reference_by_id[pair.reference_id],
            generated_requirement=generated_by_id[pair.generated_id],
            evaluator_model=evaluator_model,
            max_retries=max_retries,
        )
        decisions.append(
            MatchDecision(
                generated_id=pair.generated_id,
                reference_id=pair.reference_id,
                rank=pair.rank,
                similarity=pair.similarity,
                decision=judgment["decision"],
                reason=judgment["reason"],
            )
        )
    return decisions


def compute_metrics(
    reference_requirements: List[RequirementItem],
    generated_requirements: List[RequirementItem],
    decisions: List[MatchDecision],
) -> Dict[str, object]:
    matched_reference_ids = {
        decision.reference_id
        for decision in decisions
        if decision.decision == "Match"
    }
    matched_generated_ids = {
        decision.generated_id
        for decision in decisions
        if decision.decision == "Match"
    }

    reference_count = len(reference_requirements)
    generated_count = len(generated_requirements)
    coverage_ratio = (
        len(matched_reference_ids) / reference_count if reference_count else 0.0
    )
    generated_match_ratio = (
        len(matched_generated_ids) / generated_count if generated_count else 0.0
    )

    return {
        "Coverage Ratio (CR)": coverage_ratio,
        "Generated Match Ratio (GMR)": generated_match_ratio,
        "Matched Reference Requirement Count": len(matched_reference_ids),
        "Matched Generated Requirement Count": len(matched_generated_ids),
        "Reference Requirement Count": reference_count,
        "Generated Requirement Count": generated_count,
        "Matched Reference Requirement IDs": sorted(matched_reference_ids),
        "Matched Generated Requirement IDs": sorted(matched_generated_ids),
    }


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_legacy_style_results(
    generated_requirements: List[RequirementItem],
    decisions: List[MatchDecision],
) -> Dict[str, Dict[str, object]]:
    generated_by_id = {item.id: item for item in generated_requirements}
    decisions_by_generated_id: Dict[str, List[MatchDecision]] = {
        generated_requirement.id: [] for generated_requirement in generated_requirements
    }
    for decision in decisions:
        decisions_by_generated_id.setdefault(decision.generated_id, []).append(decision)

    results: Dict[str, Dict[str, object]] = {}
    for generated_requirement in generated_requirements:
        generated_decisions = sorted(
            decisions_by_generated_id.get(generated_requirement.id, []),
            key=lambda item: item.rank,
        )
        all_matches = [
            {
                "rank": decision.rank,
                "A_id": decision.reference_id,
                "similarity": float(decision.similarity),
                "decision": decision.decision,
                "reason": decision.reason,
            }
            for decision in generated_decisions
        ]

        if generated_decisions:
            best_decision = min(
                generated_decisions,
                key=lambda item: (
                    0 if item.decision == "Match" else 1,
                    -item.similarity,
                ),
            )
            decision_value = best_decision.decision
            best_match_to_reference = best_decision.reference_id
            best_reason = best_decision.reason
        else:
            decision_value = "No Match"
            best_match_to_reference = None
            best_reason = "No candidate reference requirement was retrieved."

        results[generated_requirement.id] = {
            "title": generated_by_id[generated_requirement.id].title,
            "decision": decision_value,
            "best_match_toA": best_match_to_reference,
            "reason": best_reason,
            "all_matches": all_matches,
        }
    return results


def render_summary_report(metrics: Dict[str, object]) -> str:
    return (
        "# LLM-Assisted System-Level Requirement Evaluation\n\n"
        f"- Coverage Ratio (CR): {metrics['Coverage Ratio (CR)']:.4f}\n"
        f"- Generated Match Ratio (GMR): {metrics['Generated Match Ratio (GMR)']:.4f}\n"
        f"- Matched reference requirements: "
        f"{metrics['Matched Reference Requirement Count']} / "
        f"{metrics['Reference Requirement Count']}\n"
        f"- Matched generated requirements: "
        f"{metrics['Matched Generated Requirement Count']} / "
        f"{metrics['Generated Requirement Count']}\n"
    )


def run_system_level_requirement_evaluation(
    reference_requirements_path: str,
    generated_requirements_path: str,
    output_dir: str,
    evaluator_model: str,
    embedding_model: str,
    top_k: int,
    max_retries: int,
) -> Dict[str, object]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    reference_requirements = load_requirements(reference_requirements_path)
    generated_requirements = load_requirements(generated_requirements_path)
    print(f"[INFO] Loaded {len(reference_requirements)} reference requirements")
    print(f"[INFO] Loaded {len(generated_requirements)} generated requirements")

    reference_embeddings = embed_requirements(reference_requirements, embedding_model)
    generated_embeddings = embed_requirements(generated_requirements, embedding_model)

    candidate_pairs = retrieve_top_k_candidates(
        reference_requirements=reference_requirements,
        generated_requirements=generated_requirements,
        reference_embeddings=reference_embeddings,
        generated_embeddings=generated_embeddings,
        top_k=top_k,
    )
    save_json(output_path / "candidate_pairs.json", [asdict(pair) for pair in candidate_pairs])

    decisions = evaluate_candidate_pairs(
        reference_requirements=reference_requirements,
        generated_requirements=generated_requirements,
        candidate_pairs=candidate_pairs,
        evaluator_model=evaluator_model,
        max_retries=max_retries,
    )
    save_json(output_path / "match_decisions.json", [asdict(item) for item in decisions])

    metrics = compute_metrics(
        reference_requirements=reference_requirements,
        generated_requirements=generated_requirements,
        decisions=decisions,
    )
    legacy_style_results = build_legacy_style_results(
        generated_requirements=generated_requirements,
        decisions=decisions,
    )
    save_json(
        output_path / "evaluation_results.json",
        {
            "results": legacy_style_results,
            "metrics": metrics,
        },
    )
    save_json(output_path / "metrics.json", metrics)
    (output_path / "summary_report.md").write_text(
        render_summary_report(metrics),
        encoding="utf-8",
    )
    print("[DONE] Saved evaluation outputs to", output_path)
    print(render_summary_report(metrics))
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run LLM-assisted system-level requirement evaluation."
    )
    parser.add_argument("--reference-requirements", required=True)
    parser.add_argument("--generated-requirements", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--evaluator-model", default="deepseek-r1")
    parser.add_argument("--embedding-model", default="text-embedding-3-large")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--max-retries", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_system_level_requirement_evaluation(
        reference_requirements_path=args.reference_requirements,
        generated_requirements_path=args.generated_requirements,
        output_dir=args.output_dir,
        evaluator_model=args.evaluator_model,
        embedding_model=args.embedding_model,
        top_k=args.top_k,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
