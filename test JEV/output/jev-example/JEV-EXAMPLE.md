# JEV-routed Power BI example

## Request

Create a new Executive Expenses page in a separate project copy. Use the existing `Total Expenses Clean` and `Total Income Clean` measures. Add income and expense KPI cards, a time trend, and a top-expense visual. Preserve the existing pages and follow the finance styling.

## Jev decision

The project inventory and brief were sent in one System One request. Jev 1.13 returned:

- `worker`: `REPORT_AGENT` (confidence 1.00)
- `action`: `generate` (probability 0.84; confidence 0.80)

The router treats confidence below 0.90 as advisory, so I inspected the PBIR definitions and measure expressions locally before editing.

## Execution

1. Copy the PBIP project to this folder, excluding credentials and local Power BI caches.
2. Reuse the existing finance-app visual definitions for the year slicer, KPI cards, line chart and Top N bar chart.
3. Bind the page to existing measures and fields; no DAX or model changes were needed.
4. Add the page to `pages.json`, retain the original pages, and validate the copy.

For this page addition, the visual definitions and page-order entry are coupled, so
they were applied together. A separate theme-file edit could run alongside page work
because it touches a disjoint artifact.

The model's expense `Category` column distinguishes credit from debit; it does not contain spending categories. The breakdown therefore uses the existing `Description` field and its Top 10 visual.

## Output and verification

Open `JEV.pbip` in this folder. The JEV Expenses page is the active landing page. Static validation passed: JSON syntax, page order, direct field references and canvas bounds are clean. DAX execution, full PBIR schema validation and Power BI Desktop rendering were not performed.
