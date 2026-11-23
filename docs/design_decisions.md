# Design decisions

**Raw stays text.** Every extract column lands as a string, as it arrives. Staging parses dates with explicit formats
per pattern (ISO, day-first, compact, spreadsheet serial) and keeps the raw text and its detected format next to the
typed value, so a rejection can always show what was received.

**One reason per rejected row, in a fixed order.** A row with two problems is rejected for the first; counts by reason
therefore add up to the total rejected and never double count. Overlap is only tested between rows that passed every
earlier rule, so a bad date never creates a phantom conflict.

**Reject both sides of a conflict.** When a worker has overlapping placements with two employers, neither is chosen.
Picking the later or longer one would be a guess; the worker is listed for review instead.

**Exact duplicates are not errors.** Rows equal in every field are collapsed and counted. Rows sharing a natural key with
different details are conflicts and are rejected.

**System plus ID is the worker.** The two payroll systems reuse numbers. A surrogate key on both columns keeps 15 pairs
of different people apart; a test fails if they merge.

**Effective-dated facts, slowly changing branches.** `fct_placement` holds valid periods; `fct_worker_month` resolves
them on each month-end and joins the branch row in effect that day, so a branch that moved region reports under its old
region before the change.

**Unassigned is a member, not a gap.** Placements with no branch join a branch called Unassigned, so the sum over
branches equals the total.

**Insufficient evidence is a band.** Workers without a defensible seniority start are counted in headcount and shown in
their own band, instead of being dropped or given an estimate.

**Counts only in published material.** The rejection table carries surrogate keys for the data team; report marts,
the dashboard export and the audit report carry aggregates. A dbt test and a pytest check enforce it.
