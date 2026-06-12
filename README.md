# UI-ReqGen Framework

This workspace contains a paper-aligned implementation of the UI-ReqGen
multi-agent framework, together with experiment support scripts and result
artifacts for the replication package.

## Agents

- Code-level Requirement Generation Agent
- Non-functional Requirement Filtering Agent
- Text Embedding Agent
- Clustering Agent with K-Means and HCA
- System-level Requirement Generation Agent
- Requirement Evaluation Agent

## Configuration

Set the OpenAI-compatible credentials before running:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_BASE_URL="https://your-compatible-endpoint/v1"
```

`OPENAI_BASE_URL` is optional when using the default OpenAI endpoint.

Optional model overrides:

```powershell
$env:UI_REQGEN_GENERATION_MODEL="gpt-4o"
$env:UI_REQGEN_EMBEDDING_MODEL="text-embedding-3-large"
```

## Run

```powershell
python run_ui_reqgen.py --ui-layer-code-dir "D:\path\to\ui\code" --code-level-requirement-output-dir "ui_reqgen_code_level_requirements"
```

Use `--file-extension .java` or `--file-extension .jsp` to restrict the UI-layer
file types. Repeat the option to pass multiple extensions.

Generated code-level requirements are cached in `--code-level-requirement-output-dir`.
All downstream agent outputs are saved under `--artifact-output-dir`, which defaults
to `ui_reqgen_artifacts`.

## Baselines

The optional baseline script uses the same OpenAI-compatible environment variables
as the main framework. It reads generated code-level requirement `.txt` files and
produces direct and chunked system-level requirement baselines.

```powershell
python run_requirement_baselines.py --input-dir "ui_reqgen_code_level_requirements" --output-dir "baseline_outputs" --project-name "iTrust" --baseline both --model "gpt-4o"
```

## System-Level Evaluation

The optional system-level evaluation script follows the paper's LLM-assisted
matching design: embedding-based Top-3 retrieval, LLM Match/No Match judgments,
and CR/GMR calculation.

Evaluate HCA outputs:

```powershell
python run_system_level_requirement_evaluation.py --reference-requirements "path\to\manual_requirements.json" --generated-requirements "dronology_artifacts\06_system_level_requirement_generation\hca_system_level_requirements.json" --output-dir "dronology_hca_system_level_evaluation" --evaluator-model "deepseek-r1" --embedding-model "text-embedding-3-large" --top-k 3
```

Evaluate K-Means outputs:

```powershell
python run_system_level_requirement_evaluation.py --reference-requirements "path\to\manual_requirements.json" --generated-requirements "dronology_artifacts\06_system_level_requirement_generation\kmeans_system_level_requirements.json" --output-dir "dronology_kmeans_system_level_evaluation" --evaluator-model "deepseek-r1" --embedding-model "text-embedding-3-large" --top-k 3
```

The script writes `evaluation_results.json` with the same top-level structure used
by the original experimental script: `results` and `metrics`. The matching label is
stored as `decision` (`Match` or `No Match`), and the metrics use the paper's names:
`Coverage Ratio (CR)` and `Generated Match Ratio (GMR)`.

## Code-Level LLM-Assisted Evaluation

The optional code-level LLM-assisted evaluation script follows the paper's
LLM-as-a-Judge design for RQ1. The input table is not included in the replication
package. Provide an external `.csv` or `.xlsx` table whose first three columns are:
code, reference text, and generated text. The script keeps the input columns and
adds the following output columns in an `.xlsx` file: `Completeness`,
`Conciseness`, `Correctness`, `Cohesiveness`, `Average`, and `FullEvaluation`.

```powershell
python run_llm_assisted_code_level_evaluation.py --input-table "path\to\input.xlsx" --output-xlsx "results\RQ1\LLM_assisted_evaluation_results\Dronology_zeroshot.xlsx" --model "gpt-4o"
```

Use `--reference-col` and `--generated-col` to override the default second and
third input columns.
