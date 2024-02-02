from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Competition:
    # Required
    id: str
    name: str
    short_name: str
    start_date: date
    results_posted: bool
    city: str
    venue: str
    website: str

    # Optional
    display_name: str | None

    @classmethod
    def from_dict(cls, dict: dict) -> Competition:
        return cls(
            # Required
            id=dict["id"],
            name=dict["name"],
            short_name=dict["short_name"],
            start_date=date.fromisoformat(dict["start_date"]),
            results_posted=dict["results_posted_at"] is not None,
            city=dict["city"],
            venue=dict["venue"],
            website=dict["website"],
            # Optional
            display_name=dict.get("short_display_name"),
        )
