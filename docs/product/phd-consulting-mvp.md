# PhD Consulting Agent MVP Product Spec

## Primary User

The first user is a PhD application consultant who prepares student-facing analysis, research direction suggestions, school/supervisor matching notes, confidence-building reference cases, and consultation call talking points.

## MVP Workflow

1. Create a student case.
2. Paste or upload student profile material.
3. Generate background analysis.
4. Generate theoretical, applied, and interdisciplinary research directions.
5. Generate school/project/supervisor matching notes for target regions.
6. Generate comparable reference cases or confidence talking points with clear provenance.
7. Rewrite output into consultant-ready Chinese narrative.
8. Generate consultation call prep notes.

## Non-Goals

- Multi-user CRM.
- Payment, auth, or SaaS deployment.
- Fully automated admissions decision-making.
- Unverified claims about current rankings, deadlines, scholarships, or supervisor availability.

## Provenance Rules

Every generated item must distinguish student-provided facts, extracted document facts, verified public facts, model-generated strategy, and simulated reference examples.

## First-Version Acceptance Criteria

- A consultant can create one case and run all MVP workflow steps locally.
- Generated outputs are saved under the case.
- The UI makes generated content easy to review, edit, and copy.
- Comparable cases are not presented as verified real cases unless their source is explicitly verified.
