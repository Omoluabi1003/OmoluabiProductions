"""Layered deduplication using deterministic and fuzzy rules."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from src.models import CleanChurchRecord


@dataclass
class DuplicateFlag:
    record_id_1: str
    record_id_2: str
    similarity_score: float
    reason_flag: str


def deduplicate_records(records: list[CleanChurchRecord], fuzzy_threshold: int = 88) -> tuple[list[CleanChurchRecord], list[DuplicateFlag]]:
    """Return unique records plus a duplicate-review list."""
    unique: list[CleanChurchRecord] = []
    flags: list[DuplicateFlag] = []

    for rec in records:
        duplicate_found = False
        for kept in unique:
            reason = None
            score = 0.0

            if rec.website and kept.website and rec.website == kept.website:
                reason, score = "website_exact", 100
            elif rec.phone and kept.phone and rec.phone == kept.phone:
                reason, score = "phone_exact", 100
            elif rec.church_name.lower() == kept.church_name.lower() and (rec.city or "").lower() == (kept.city or "").lower():
                reason, score = "name_city_exact", 100
            elif rec.street_address and kept.street_address and rec.church_name and kept.church_name:
                name_score = fuzz.token_set_ratio(rec.church_name, kept.church_name)
                addr_score = fuzz.token_set_ratio(rec.street_address, kept.street_address)
                if name_score >= fuzzy_threshold and addr_score >= fuzzy_threshold:
                    reason, score = "name_street_fuzzy", (name_score + addr_score) / 2
            else:
                name_city_combo_a = f"{rec.church_name} {rec.city or ''}".strip()
                name_city_combo_b = f"{kept.church_name} {kept.city or ''}".strip()
                sim = fuzz.token_set_ratio(name_city_combo_a, name_city_combo_b)
                if sim >= fuzzy_threshold:
                    reason, score = "name_city_fuzzy", sim

            if reason:
                duplicate_found = True
                flags.append(
                    DuplicateFlag(
                        record_id_1=kept.record_id,
                        record_id_2=rec.record_id,
                        similarity_score=float(score),
                        reason_flag=reason,
                    )
                )
                break

        if not duplicate_found:
            unique.append(rec)

    return unique, flags
