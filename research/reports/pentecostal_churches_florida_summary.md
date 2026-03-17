# Florida Pentecostal Churches Research Summary

## Outcome
No church records were included in this run because external web access was blocked in the execution environment, preventing retrieval and verification from required Tier-1/Tier-2 sources.

- **Total churches found:** 0
- **Count by denomination:** none
- **Count by county:** none
- **Confidence distribution:** none

## Evidence of network limitation
The following checks were attempted and failed with `CONNECT tunnel failed, response 403`:

1. `curl -I https://ag.org --max-time 20`
2. `curl -I https://www.wikipedia.org --max-time 20`
3. `curl -I https://overpass-api.de/api/status --max-time 20`

Because the dataset quality rules prohibit hallucinated or weakly supported records, no unverifiable entries were added.

## Files produced
- `research/data/pentecostal_churches_florida.csv` (header-only CSV schema)
- `research/data/pentecostal_churches_florida.json` (empty JSON array)

## Next step (when network access is available)
Re-run the data collection workflow against:
1. Denominational directories (Assemblies of God, COGIC, Church of God Cleveland, UPCI, IPHC, Foursquare)
2. Official church websites
3. Florida Sunbiz confirmation for legal registration
4. Secondary corroboration (Google Maps / established directories)
