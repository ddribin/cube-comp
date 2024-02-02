import pytest
from typing import Any
from datetime import date

from cube_comp import Competition

class TestCompetion:
    @property
    def minimal_dict(self) -> dict[str, Any]:
        dict = {
            "id": "AnID",
            "name": "A Name",
            "short_name": "A Short Name",
            "start_date": "2024-01-01",
            "results_posted_at": None,
            "city": "Chicago, IL",
            "venue": "Wrigley Field",
            "website": "https://example.com/AnID/",
        }
        return dict


    def test_parse_minimally_valid_dict(self) -> None:
        dict = self.minimal_dict

        comp = Competition.from_dict(dict)

        # Required
        assert comp.id == "AnID"
        assert comp.name == "A Name"
        assert comp.short_name == "A Short Name"
        assert comp.start_date == date.fromisoformat("2024-01-01")
        assert comp.results_posted is False
        assert comp.city == "Chicago, IL"
        assert comp.venue == "Wrigley Field"
        assert comp.website == "https://example.com/AnID/"

        # Optional
        assert comp.display_name is None

    def test_fully_populated_valid_dict(self) -> None:
        dict = self.minimal_dict
        dict["short_display_name"] = "A Short Display Name"

        comp = Competition.from_dict(dict)

        # Required
        assert comp.id == "AnID"
        assert comp.name == "A Name"
        assert comp.short_name == "A Short Name"
        assert comp.start_date == date.fromisoformat("2024-01-01")
        assert comp.results_posted is False
        assert comp.city == "Chicago, IL"
        assert comp.venue == "Wrigley Field"
        assert comp.website == "https://example.com/AnID/"

        # Optional
        assert comp.display_name == "A Short Display Name"
