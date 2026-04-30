# PhD Consulting Agent Project Notes

## Project Purpose

This project builds a practical AI workbench for a PhD application consultant.
The first real user is the consultant herself, so product decisions should be
driven by her existing workflow rather than by a generic agent demo.

The product has two goals:

- Business goal: reduce repeated consulting work and make student-facing output
  faster, clearer, and more consistent.
- Technical goal: validate a reusable agent + skill + workflow architecture on a
  real consulting scenario.

## Current Direction

Use a hybrid of:

1. A **student case workbench** as the user-facing product.
2. A set of **Hermes skills** as the underlying capability modules.

The workbench should organize each student as one case. The case should preserve
the student profile, uploaded materials, generated analysis, selected research
directions, school/supervisor matches, comparable cases, and final consultant
talking points.

## Data Source Already Cleaned

The consultant's Gemini activity export was cleaned into structured files under:

`data/cleaned/gemini_takeout/`

Important files:

- `gemini_activity_all.jsonl`: all parsed Gemini activity records.
- `gemini_activity_relevant.jsonl`: records matching PhD consulting keywords.
- `gemini_activity_relevant_index.csv`: compact browsing index with prompts,
  task tags, dates, and attachment names.
- `gemini_attachment_references.csv`: mapping from uploaded files to activity
  records.
- `gemini_files_manifest.jsonl`: local attachment manifest.
- `summary.json`: count summary and keyword/task tag breakdown.

Do not mutate the raw Takeout folder. Treat cleaned files as derived artifacts
that can be regenerated with:

```bash
python3 scripts/clean_gemini_takeout.py \
  --input-dir "/Users/zhangchi/Projects/python/phd-consulting-agent/Takeout/My Activity/Gemini Apps" \
  --output-dir "/Users/zhangchi/Projects/python/phd-consulting-agent/data/cleaned/gemini_takeout"
```

## Real Workflow Observed From Data

The cleaned Gemini data shows that the consultant's actual workflow is not just
"write outreach emails." The repeated workflow is:

1. **Student profile intake**
   - Input: education history, GPA/grades, publications, research experience,
     work experience, target regions, funding requirements, career goals, and
     uploaded CV/RP/SOP/screenshots.
   - Output: consultant-readable profile diagnosis.

2. **Background diagnosis**
   - Evaluate strengths, weaknesses, risks, and positioning.
   - Explain whether the student is suitable for direct PhD, MPhil + PhD,
     taught master's first, or a lower-risk route.
   - Identify missing information the consultant should ask for.

3. **Research direction design**
   - This is one of the highest-frequency tasks.
   - Directions are often framed as theoretical, applied, and interdisciplinary.
   - The consultant often asks for alternatives when the student dislikes
     quantitative work, policy, education, technical AI, or another category.

4. **Region / school / project / supervisor matching**
   - The normal chain is: direction -> target region -> universities -> school
     or department -> project/program -> potential supervisors.
   - Output should include matching reasons and risks, not just a list.
   - The consultant frequently asks for Hong Kong, Macau, Australia, New
     Zealand, Singapore, the UK, and the US.

5. **Comparable case / confidence material**
   - Very frequent.
   - The consultant asks for "students with slightly weaker backgrounds" to help
     build confidence.
   - Product wording must be careful: prefer "comparable reference profiles,"
     "sanitized prior cases," or "simulated reference cases" depending on data
     provenance. Do not present generated cases as verified real cases.

6. **Consultant-ready delivery**
   - The final output should often be narrative, not a table.
   - The consultant frequently asks for richer wording, specific schools,
     Chinese school names, city/ranking details, and wording she can send or say
     directly to a student.

7. **Consultation call preparation**
   - Some prompts prepare for voice calls with students.
   - The product should eventually create a "call prep pack": key talking
     points, likely student/parent questions, suggested answers, and risk
     disclaimers.

## MVP Scope

First version should cover all observed first-version scenarios:

- Student case creation and profile intake.
- Background analysis.
- Research direction recommendation.
- School/project/supervisor matching.
- Comparable case or confidence-talking-point generation.
- Consultant-ready response rewriting.
- Consultation call prep pack.

The first UI should be a case workbench, not a marketing page and not three
isolated buttons.

## Initial Skill Modules

Start with these Hermes skill concepts:

1. `student_profile_analysis`
   - Takes structured or pasted student profile plus optional extracted
     document text.
   - Returns diagnosis, strengths, risks, missing info, positioning, and next
     recommended action.

2. `research_direction_design`
   - Generates theoretical, applied, and interdisciplinary research directions.
   - Supports constraints such as "avoid quantitative," "avoid policy," "prefer
     AI crossover," "target Hong Kong," or "needs employability."

3. `school_supervisor_matching`
   - Converts chosen directions and target regions into school/program/supervisor
     candidates.
   - Should separate verified facts from model inference.
   - Current information must be verified before producing claims about current
     rankings, deadlines, supervisors, scholarships, or program requirements.

4. `comparable_case_generator`
   - Produces confidence-building reference cases.
   - Must clearly label whether cases come from verified historical data,
     sanitized internal examples, or generated simulations.

5. `consultant_delivery_rewriter`
   - Rewrites outputs into the consultant's preferred style: narrative,
     specific, rich, practical, mostly Chinese, and easy to send to a student.
   - Supports "no table" as a default unless the user asks for tabular output.

6. `consultation_call_prep`
   - Creates call notes, likely questions, suggested answers, and risk points.

## Design Principles

- Optimize for the consultant's real repeated work, not generic admissions
  advice.
- Keep human-in-the-loop editing central. The system drafts and structures; the
  consultant decides.
- Preserve provenance. Separate:
  - student-provided facts,
  - extracted document facts,
  - verified public facts,
  - model-generated strategy,
  - simulated examples.
- Avoid overclaiming. Admissions outcomes, supervisor availability, funding, and
  rankings are unstable and must be verified with current sources when used for
  real decisions.
- Default output should be practical Chinese consulting language. English output
  is needed for emails, RP/SOP fragments, or academic phrasing.
- Tables are useful for internal comparison, but many final outputs should be
  narrative because the consultant often asks for non-table responses.
- Protect student privacy. Avoid exposing personal names or sensitive details in
  generated docs unless they are needed for the specific task.

## Likely Architecture

Early version:

- Local web app for the case workbench.
- Local data storage using JSON/Markdown or SQLite.
- Hermes skills for the consulting capability modules.
- Optional document extraction pipeline for CV/RP/SOP/PDF/DOCX attachments.

Later version:

- Case library with retrieval.
- Verified school/program/supervisor knowledge base.
- Reminder and follow-up workflows.
- Multi-user CRM-style features only after the single-consultant workflow works.

## Open Questions

- Which data should be persisted first: full case records, generated outputs, or
  only prompts/results?
- Should comparable cases initially be generated simulations, manually curated
  examples, or retrieved from cleaned historical interactions?
- How much school/supervisor information should be verified live versus stored
  locally?
- What is the minimum acceptable UI for the consultant to use this in real work:
  one-page case workbench, multi-step wizard, or chat-first interface?

