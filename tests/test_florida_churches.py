"""Tests for the Florida churches data agent pipeline helpers."""

import json
import tempfile
import unittest
from pathlib import Path

from florida_churches import church_from_element, write_json


class TestFloridaChurchesHelpers(unittest.TestCase):
    def test_church_from_element_extracts_contact_and_operator_fields(self) -> None:
        element = {
            "type": "node",
            "id": 123,
            "lat": 30.25,
            "lon": -81.6,
            "tags": {
                "name": "new life church",
                "addr:housenumber": "101",
                "addr:street": "Main Street",
                "addr:city": "Jacksonville",
                "addr:state": "Florida",
                "addr:postcode": "32202-1234",
                "addr:county": "Duval",
                "contact:phone": "(904) 555-0001",
                "contact:website": "https://newlife.example.org",
                "contact:email": "info@newlife.example.org",
                "operator": "New Life Ministries",
            },
        }

        row = church_from_element(element, "2026-01-01T00:00:00+00:00")

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.name, "New Life Church")
        self.assertEqual(row.street, "101 Main St")
        self.assertEqual(row.state, "FL")
        self.assertEqual(row.zip, "32202")
        self.assertEqual(row.phone, "(904) 555-0001")
        self.assertEqual(row.website, "https://newlife.example.org")
        self.assertEqual(row.email, "info@newlife.example.org")
        self.assertEqual(row.operator, "New Life Ministries")

    def test_write_json_serializes_rows(self) -> None:
        element = {
            "type": "node",
            "id": 456,
            "lat": 27.95,
            "lon": -82.46,
            "tags": {
                "name": "Grace Chapel",
                "addr:street": "Elm Road",
                "addr:housenumber": "10",
                "addr:city": "Tampa",
                "addr:postcode": "33601",
                "addr:county": "Hillsborough",
            },
        }
        row = church_from_element(element, "2026-01-01T00:00:00+00:00")
        self.assertIsNotNone(row)
        assert row is not None

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "rows.json"
            write_json(output, [row])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["name"], "Grace Chapel")
        self.assertEqual(payload[0]["city"], "Tampa")


if __name__ == "__main__":
    unittest.main()
