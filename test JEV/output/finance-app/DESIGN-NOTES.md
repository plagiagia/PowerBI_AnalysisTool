# Finance workspace

Open `JEV.pbip`. The active landing page is Overview.

Five sections share a navy navigation rail: Overview, Cash flow, Transactions,
Payroll and Pay components. The canvas is 1600 by 900 with Segoe UI typography,
white chart surfaces, restrained borders, and teal highlights. Income and expense
series on the overview use teal and amber respectively.

The original model, visual query bindings and visual filters are preserved.
Some existing detail charts retain their original relative-date filters; their
titles retain that context. The overview uses its own year selection. Page changes
do not imply that every original detail-page slicer is synchronized.

Verification: local static checks passed, all 25 navigation destinations resolve,
and copied semantic-model files match the source byte for byte. Existing visual
queries and filters match the source. Native Desktop inspection was unavailable
because the Computer Use native pipe could not connect. Actual rendering, formatting
support and button behavior have not been verified in Power BI Desktop.

In Desktop editing mode, page-navigation buttons normally require Ctrl+click.
The copy excludes the local .pbi cache, so a refresh may be required to populate data.
