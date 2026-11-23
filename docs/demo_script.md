# Demo script (four minutes)

1. **Overview** (60 s). "How many workers did we have on 31 October?" Open rows say 1,706. Walk the bridge: duplicates,
   future starts, then the big one, 366 fixed-term placements ending after the as-of date. Rejected rows take it to 1,959.
2. **Data quality** (60 s). Rejections by reason: each row has one code. Two employers at once: both rows rejected, not a
   guess. The two master extracts look identical but differ for four workers.
3. **Seniority** (60 s). Bands on 31 October; 18 workers with insufficient evidence as a band of their own. Scroll to the
   fixtures: 31 January to 28 February is one month; a leap-day start completes its year on 28 February.
4. **Headcount** (40 s). The reconciliation table: the same total by employer, branch with Unassigned, region and band.
5. **Checks** (20 s). Every rule names its test; CI rebuilds from the seed and compares fingerprints.
