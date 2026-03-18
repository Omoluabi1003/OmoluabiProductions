"""Deduplication logic for clean church records."""

from __future__ import annotations

from rapidfuzz import fuzz

from agent.models import CleanChurchRecord, DuplicateAuditRecord


def dedupe_records(records: list[CleanChurchRecord], fuzzy_threshold: float = 90.0) -> tuple[list[CleanChurchRecord], list[DuplicateAuditRecord]]:
    seen_keys: dict[str, int] = {}
    unique: list[CleanChurchRecord] = []
    dupes: list[DuplicateAuditRecord] = []

    for record in records:
        exact_key = "|".join(filter(None, [record.website, record.phone, record.email]))
        if exact_key and exact_key in seen_keys:
            retained = unique[seen_keys[exact_key]]
            dupes.append(
                DuplicateAuditRecord(
                    left_record_id=retained.canonical_name,
                    right_record_id=record.canonical_name,
                    match_score=100.0,
                    dedupe_reason="exact_key",
                    retained_record_id=retained.canonical_name,
                    discarded_record_id=record.canonical_name,
                )
            )
            continue

        duplicate_found = False
        for idx, candidate in enumerate(unique):
            left = f"{record.church_name} {record.city} {record.address}".strip()
            right = f"{candidate.church_name} {candidate.city} {candidate.address}".strip()
            score = float(fuzz.token_set_ratio(left, right))
            if score >= fuzzy_threshold:
                dupes.append(
                    DuplicateAuditRecord(
                        left_record_id=candidate.canonical_name,
                        right_record_id=record.canonical_name,
                        match_score=score,
                        dedupe_reason="fuzzy_name_city_address",
                        retained_record_id=candidate.canonical_name,
                        discarded_record_id=record.canonical_name,
                    )
                )
                duplicate_found = True
                break
        if not duplicate_found:
            seen_keys[exact_key or record.canonical_name] = len(unique)
            unique.append(record)

    return unique, dupes
