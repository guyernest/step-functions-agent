**Title: Batch Agent/Tool Execution via AI‑Evals Orchestrator**

**Summary**

- Extend the existing AI‑evals orchestration to support large batch execution of our Step Functions agents and standalone tools. Keep per‑row isolation, robust retries, and cost/latency metrics, while avoiding Step Functions payload limits. First iteration uses a Lambda pre/post wrapper around agents and produces a downloadable CSV export via Athena, without embedding spreadsheet logic into the state machine.

**Goals**

- Reuse AI‑evals dataset/results (Iceberg via S3 Tables/Athena) and its Step Functions orchestrator.
- Add execution modes: endpoint (existing), agent (new), tool (new), with JSONata mappings.
- Default sequential execution (MaxConcurrency=1); later make concurrency configurable from UI.
- Normalize agent I/O via a Lambda wrapper to keep Step Functions JSONata simple.
- Export results to a CSV in S3 via Athena (CTAS/UNLOAD), triggered outside the state machine for simplicity.

**Non‑Goals (v1)**

- No spreadsheet writing to SharePoint/Google Sheets inside the orchestrator.
- No human‑in‑the‑loop steps in the batch runner (agents can still do HITL internally if configured, but batch flow doesn’t orchestrate it).
- No cross‑run deduplication beyond `evaluation_id + sample_id` uniqueness.

**Current State**

- This repo provides Step Functions agents and tools; agents are invoked today with per‑execution orchestration and tool fan‑out.
- AI‑evals repo provides:
  - Dataset and result tables in Iceberg via S3 Tables/Athena.
  - Amplify Gen2 backend with Lambda functions and a Step Functions “evaluation orchestration” ASL.
  - UI to upload datasets, trigger runs, show progress, and view results.

**Key Decisions (from discussion)**

- Use a Lambda pre/post wrapper for agent calls to handle input mapping and output normalization. The slight latency is acceptable for long‑running batches.
- Do not embed spreadsheet export into the state machine. Generate a CSV export via Athena (CTAS/UNLOAD) that users can download from S3.
- Start with sequential processing (MaxConcurrency=1). Expose a configurable concurrency parameter in a subsequent version.

**High‑Level Architecture**

- Ingest: Dataset rows live in `s3_evaluation_db.evaluation_datasets` (Iceberg) with `sample_id` and `input`.
- Orchestrate (AI‑evals Step Functions):
  - Query dataset via Athena → Map over samples (MaxConcurrency=1 initially).
  - For each sample:
    - executionMode=endpoint: existing HTTP path.
    - executionMode=agent: call `agent-caller` Lambda → wrapper calls our Step Functions agent via `StartExecution.sync:2` and normalizes output.
    - executionMode=tool: call a tool Lambda directly and normalize.
  - Batch insert results into `evaluation_results_evaluations` via Athena INSERT to avoid large state payloads.
- Export: Separate “export” Lambda (or API) triggers an Athena CTAS/UNLOAD to produce `s3://.../exports/{executionId}.csv` based on the results table.

**Components & Changes**

- This Repo (step-functions-agent)
  - Provide/maintain target agent state machines and their input expectations.
  - Document a minimal expected input schema for agent batch runs (stable `row_id`/`sample_id`, mapped fields, and optional context).
  - No code changes required here for v1 beyond documenting agent inputs and exposing ARNs.

- AI‑Evals Repo (Amplify Backend)
  - Step Functions ASL (`ui/amplify/step-functions/evaluation-orchestration/resource.ts`):
    - Add Choice state `SelectExecutionPath` after loading configs.
    - For agent path: Task `CallAgentWrapper` → Lambda invoke with arguments from JSONata mapping. The wrapper calls our Step Functions agent via `states:startExecution.sync:2`, captures final output, and returns normalized fields: `actual_output`, `provider_name`, `tokens`, `latency_ms`.
    - For tool path: Task `CallToolLambda` → `lambda:invoke` and map the result similarly.
    - Keep nested Map + batched `INSERT` into evaluations table. Suppress large outputs to prevent state bloat.
  - New Lambda `agent-caller` (wrapper):
    - Input: `{ executionId, sampleId, agentStateMachineArn, agentInput, timeoutMs?, trace?: boolean }`.
    - Action: `StartExecution.sync:2` to the agent, poll for completion, extract final answer (and optional metrics), normalize to a compact result.
    - Output (normalized): `{ actualOutput: string, providerName?: string, promptTokens?: number, completionTokens?: number, totalTokens?: number, fullResponseBody?: string }`.
  - Export Lambda `results-exporter` (optional API + UI button):
    - Input: `{ executionId, outputMapping?, destinationPrefix }`.
    - Action: run Athena CTAS/UNLOAD to `s3://…/exports/{executionId}/` with CSV/text output.
    - Return S3 URI for download.
  - IAM (in `ui/amplify/backend.ts`):
    - Allow `states:StartExecution` on the specific agent state machine ARNs for `agent-caller` Lambda.
    - Ensure Step Functions can invoke `agent-caller` and existing processors.

**Configuration Schema (Evaluation Config)**

- New fields (stored in DynamoDB via Amplify Data):
  - `executionMode`: `"endpoint" | "agent" | "tool"` (default: `endpoint`).
  - Agent mode: `agentStateMachineArn` (string), `agentInputMapping` (JSONata), `agentOutputMapping` (JSONata, optional — wrapper already returns normalized output; mapping is for custom field extraction if needed).
  - Tool mode: `toolLambdaArn` (string), `toolInputMapping` (JSONata), `toolOutputMapping` (JSONata, optional).
  - Executor config: `maxConcurrency` (int, default 1 in v1), `retryPolicy` (optional overrides).
  - Export config (not part of the state machine in v1): `export: { enabled: boolean, destinationPrefix?: string }`.

**State Machine Flow (Agent Path)**

- For each row in `Samples`:
  - `PrepareInput` → map dataset `input` with `agentInputMapping`.
  - `CallAgentWrapper` (Lambda):
    - `FunctionName`: `${AgentCallerFunctionArn}`
    - `Payload`: `{ executionId, sampleId, agentStateMachineArn, agentInput }`
  - `ProcessResponse` (reuse existing response step or pass-through) → produce a compact result object with required fields for Athena INSERT (e.g., `evaluation_id`, `sample_id`, `actual_output`, `provider_name`, token counts, latency, etc.).
  - Results of an inner batch are inserted via the existing batched `INSERT` Task (suppress Task output).

**Concurrency and Limits**

- `MaxConcurrency=1` initially; later pass from UI via `executorConfig.maxConcurrency`.
- Keep using batched `INSERT` and suppress outputs to avoid state payload/history growth.
- Per‑item retries/backoff remain at the Task level (HTTP calls, Lambda invokes, Athena queries).

**Export Strategy (v1)**

- Provide a UI action “Export CSV” that calls `results-exporter` Lambda.
- Lambda runs an Athena CTAS/UNLOAD query for `evaluation_id=<executionId>` to `s3://…/exports/{executionId}/` (CSV/text).
- Return S3 URI to UI for user download.

**Observability**

- Continue emitting CloudWatch logs/metrics for:
  - Items processed, success/failure, retries.
  - Per‑row latency; totals at report summary.
  - Token counts and estimated costs (if available from agent/tool response).
- X‑Ray tracing on Lambdas and Step Functions.

**Error Handling & Idempotency**

- Per‑row retries with exponential backoff; classify transient provider errors vs. validation errors.
- Use `evaluation_id + sample_id` as logical uniqueness. If a run is restarted, avoid duplicate inserts by filtering at query time for export; strict upserts are a future enhancement.

**Testing Plan**

- Unit: `agent-caller` wrapper (mock `StartExecution`), `results-exporter` (mock Athena).
- Integration: Dry‑run an evaluation with 3–5 rows across all execution modes; verify Athena rows and UI progress counters.
- Scale smoke test: 100–500 rows with MaxConcurrency=1; verify no Step Functions size/timeout issues and reasonable Athena throughput.

**Rollout Steps**

- Phase 1 (Backend foundations)
  - Add `executionMode` and agent/tool fields to evaluation config schema (Amplify Data).
  - Implement `agent-caller` Lambda and permissions for `states:StartExecution` to our agent ARNs.
  - Update Step Functions definition: add Choice `SelectExecutionPath`, `CallAgentWrapper`, `CallToolLambda` paths, reuse batched `INSERT`.
  - Keep `MaxConcurrency=1` (hardcoded or config default).
  - Validate end‑to‑end on a test dataset.

- Phase 2 (Export)
  - Implement `results-exporter` Lambda with Athena CTAS/UNLOAD to CSV.
  - Add UI button/API to trigger export for a given `executionId`; present S3 URI.

- Phase 3 (Quality of life)
  - UI control for `maxConcurrency` and basic retry policy.
  - Enhanced metrics dashboard (success rate, latency, token/cost per run).

**Open Items (Future)**

- Optional: shareable pre‑signed S3 URLs for exports; SharePoint/Google Sheets publishing as separate actions.
- Optional: token‑bucket throttling for provider quotas.
- Optional: DLQ/SNS for failed rows above retry budget.

**References**

- Orchestrator ASL: `ui/amplify/step-functions/evaluation-orchestration/resource.ts`
- Backend policies and S3 Tables: `ui/amplify/backend.ts`
- Wrapper Lambda (new): `ui/amplify/functions/agent-caller/`
- Export Lambda (new): `ui/amplify/functions/results-exporter/`

