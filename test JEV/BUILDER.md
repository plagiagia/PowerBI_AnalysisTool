# Local Power BI workflow

From this folder:

```powershell
python powerbi_builder.py inspect
python powerbi_builder.py validate
python powerbi_builder.py plan --brief "Add an expenses overview using existing measures" --jev
```

`--project` accepts a PBIP file or folder containing exactly one project. Omit `--jev`
for an offline plan. Jev uses the existing `.env` automatically. No dependencies are required.

The CLI inspects, performs selected static checks and produces a work plan. It does not
generate a report by itself. The installed `powerbi-local-builder` skill guides Codex to
carry out the plan, generate artifacts in a separate copy and verify them. In a new session,
invoke `$powerbi-local-builder` with the report change you want. Low routing confidence
falls back to Codex reasoning; no repeated approvals are needed for ordinary local work.

Static checks are not DAX compilation, full JSON Schema validation, or Desktop rendering.
The scanner currently requires one local report and a byPath TMDL model.

## JEV-routed example

For a read-only request such as listing measures, use `inspect` and return the local
model metadata directly. For an authoring request, `plan --jev` sends the brief and
project inventory to Jev in one request. Jev returns a specialist and an action;
Codex then reads the actual PBIR/TMDL definitions, edits a separate project copy, and
runs the static validator. Jev routes the work; the local builder performs the edits.
Independent edits to disjoint files can run in parallel; changes to a page and its
page-order metadata stay coordinated as one update.

Completed example: open `output/jev-example/JEV.pbip`. The route, Jev confidence,
implementation choices, and verification limits are recorded in
`output/jev-example/JEV-EXAMPLE.md`.

References: https://docs.typesafe.ai/introduction and
https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
