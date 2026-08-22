# Existing Literature Audit v1

## Scope

This audit covers repository-local dissertation and research materials only.

Searched locations:

- `D:\Sumo\sumo_train\docs\research\`
- `D:\Sumo\sumo_train\docs\dissertation\`
- all repository `*.md`, `*.txt`, `*.bib`, `*.docx`, and `*.pdf` files

Search keywords:

- `References`
- `Bibliography`
- `Literature Review`
- `Related Work`
- `citation`
- `LLM`
- `large language model`
- `autonomous driving`
- `intersection`
- `unsignalised intersection`
- `cooperative driving`
- `SUMO`
- `decision making`
- `safety`
- `fallback`

## Method Summary

The repository was scanned for:

1. actual external bibliography files,
2. inline citation markers,
3. explicit literature-review sections,
4. title/author/year/venue/DOI/URL metadata,
5. dissertation text that already refers to literature or related work.

The important distinction is between:

- **real bibliographic entries** and
- **internal engineering documents that mention literature-related concepts**

This audit only counts the former as verifiable references.

## Findings Summary

### External bibliography files

- `.bib` files found: `0`
- `.docx` files found: `0`
- `.pdf` files found: `0`

### Verified external references

- Verified external papers with title/author/year/venue/DOI/URL recovered from repository materials: `0`

### Citation placeholders

- Citation placeholders found in dissertation prose: `2`
- Literature review placeholder found in full draft: `1`
- Structural "Related Work" / "Literature Review" headings found: yes

## Classification Results

### VERIFIED_EXISTING_REFERENCE

No verified external reference could be extracted from repository materials.

### INCOMPLETE_REFERENCE

No incomplete bibliographic entry with recoverable title/author/year/venue metadata was found in the repository.

### CITATION_PLACEHOLDER

| File | Location | Text | Current use |
| --- | --- | --- | --- |
| `D:\Sumo\sumo_train\docs\dissertation\introduction_v1.md` | line 5 | `[CITATION NEEDED]` | Background / motivation sentence about unsignalised intersection control |
| `D:\Sumo\sumo_train\docs\dissertation\introduction_v1.md` | line 39 | `[CITATION NEEDED]` | Research-gap sentence about the need for reproducible pipeline-level comparison |
| `D:\Sumo\sumo_train\docs\dissertation\full_draft_v1.md` | section 2 | `[LITERATURE REVIEW TO BE COMPLETED AFTER SOURCE AUDIT]` | Literature Review placeholder |

### NEEDS_EXTERNAL_VERIFICATION

The following dissertation claims are currently supported only as general conceptual statements in the repository and need real external literature before they can become full literature-review claims:

- unsignalised intersection control as a research problem,
- cooperative multi-vehicle decision-making,
- LLM-assisted control for traffic decision support,
- deterministic fallback and safety verification as a control architecture,
- SUMO as an evaluation environment for traffic-control experiments,
- reliability / fallback as a validity threat in LLM-integrated systems.

These are reasonable dissertation themes, but the repository does not currently contain the external references needed to write a proper literature review section.

## Where literature-like material already exists

The repository already contains dissertation or research documents that describe the project’s own method and evidence, but they are not external literature references.

### Existing sections / documents

- `D:\Sumo\sumo_train\docs\dissertation\dissertation_outline_v1.md`
- `D:\Sumo\sumo_train\docs\dissertation\full_draft_v1.md`
- `D:\Sumo\sumo_train\docs\dissertation\introduction_v1.md`
- `D:\Sumo\sumo_train\docs\dissertation\writing_gap_audit_v1.md`
- `D:\Sumo\sumo_train\docs\research\research_traceability_matrix.md`
- `D:\Sumo\sumo_train\docs\research\research_design_v1.md`
- `D:\Sumo\sumo_train\docs\research\experimental_protocol_v1.md`
- `D:\Sumo\sumo_train\docs\research\simulation_assumptions.md`

These documents support methodology and evidence framing, not literature review citations.

## Existing dissertation sections that already refer to literature work

### 1. `docs/dissertation/dissertation_outline_v1.md`

- Contains a chapter heading: `Background and Related Work`
- This is a structure placeholder only.

### 2. `docs/dissertation/full_draft_v1.md`

- Contains `## 2. Literature Review / Background`
- Contains the explicit placeholder:
  - `[LITERATURE REVIEW TO BE COMPLETED AFTER SOURCE AUDIT]`
- This confirms that the literature review has not yet been written.

### 3. `docs/dissertation/introduction_v1.md`

- Contains two `[CITATION NEEDED]` placeholders.
- These are not references; they are prompts for later literature support.

### 4. `docs/dissertation/writing_gap_audit_v1.md`

- Explicitly marks the Literature Review as `MISSING`
- Explicitly notes that the introduction needs citation support for the research-gap sentence

## What can be used immediately in the dissertation

Because no verified external references were recovered, the repository can currently support only the following at dissertation-writing time:

- methodology and system design claims based on internal implementation evidence,
- experimental design claims based on the formal v2 manifest and protocol,
- results claims based on formal v2 raw evidence,
- discussion and limitations claims based on observed behavior and documented validity threats.

The repository does **not** yet support a real literature review section with properly recoverable external citations.

## What needs re-verification

Any claim in the introduction that depends on the broader research field, such as:

- why unsignalised intersection control matters in the literature,
- whether LLM-assisted control is a known or emerging direction,
- how prior work treats cooperative control or fallback/safety logic,
- how SUMO is positioned in the wider traffic-control literature,

must be verified against external sources before becoming dissertation text.

## Can the Literature Review continue from existing material?

### Short answer

**Only structurally, not substantively.**

### Explanation

The repository already has:

- chapter headings,
- a placeholder literature review slot,
- citation markers in the introduction,
- internal method and results evidence.

So the dissertation can continue from the existing scaffold.

However, it cannot yet continue from a real literature-review evidence base, because no external paper bibliography was recovered from the repository.

## Final counts

- Verified existing external papers found: `0`
- Incomplete bibliographic entries found: `0`
- Citation placeholders found: `3`
- Files with literature-review structure: `4`
- Files with internal evidence useful for later dissertation writing: many

## Bottom line

The repository currently contains **dissertation structure and engineering evidence**, but **no recoverable external literature library**.

That means the Literature Review can continue only after an external source audit, not from repository materials alone.
