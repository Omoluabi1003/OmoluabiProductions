from agent.cleaning.dedupe import dedupe_records
from agent.models import CleanChurchRecord


def _record(name: str, website: str, phone: str, email: str, city: str = "Miami") -> CleanChurchRecord:
    return CleanChurchRecord(
        church_name=name,
        canonical_name=name.lower().replace(" ", "_"),
        denomination="Baptist",
        website=website,
        phone=phone,
        email=email,
        address="1 Main St",
        city=city,
        state="FL",
        zip="33101",
        county="Miami-Dade",
        source_url=website,
        source_type="official_church_website",
        extraction_confidence=0.8,
    )


def test_exact_dedupe():
    a = _record("Grace Church", "https://grace.org", "(305) 555-1212", "info@grace.org")
    b = _record("Grace Church Miami", "https://grace.org", "(305) 555-1212", "info@grace.org")
    unique, dupes = dedupe_records([a, b])
    assert len(unique) == 1
    assert len(dupes) == 1
