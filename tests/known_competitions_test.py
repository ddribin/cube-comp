import json
import os
from datetime import date
from io import StringIO

from cube_comp import Competition, KnownCompetitions


class TestKnownCompetitions:
    def comp_with_id(self, id: str) -> Competition:
        comp = Competition(
            id=id,
            name=f"Name {id}",
            short_name=f"Short Name {id}",
            start_date=date.today(),
            results_posted=False,
            city="Chicago, IL",
            venue=f"Venue {id}",
            website="https:/example.com/{id}",
        )
        return comp

    def test_empty_known_comps(self):
        comp_a = self.comp_with_id("A")
        comp_b = self.comp_with_id("B")
        comp_c = self.comp_with_id("C")
        io = StringIO()
        known_competitions = KnownCompetitions(io)

        filtered_comps = known_competitions.filter_competitions(
            [comp_a, comp_b, comp_c]
        )

        assert filtered_comps == [comp_a, comp_b, comp_c]
        assert io.getvalue() == json.dumps(["A", "B", "C"], indent=2)

    def test_one_known_comps(self):
        comp_a = self.comp_with_id("A")
        comp_b = self.comp_with_id("B")
        comp_c = self.comp_with_id("C")
        io = StringIO('["B"]')
        known_competitions = KnownCompetitions(io)

        filtered_comps = known_competitions.filter_competitions(
            [comp_a, comp_b, comp_c]
        )

        assert filtered_comps == [comp_a, comp_c]
        assert io.getvalue() == json.dumps(["A", "B", "C"], indent=2)

    def test_all_known_comps(self):
        comp_a = self.comp_with_id("A")
        comp_b = self.comp_with_id("B")
        comp_c = self.comp_with_id("C")
        io = StringIO('["A", "B", "C"]')
        known_competitions = KnownCompetitions(io)

        filtered_comps = known_competitions.filter_competitions(
            [comp_a, comp_b, comp_c]
        )

        assert filtered_comps == []
        assert io.getvalue() == json.dumps(["A", "B", "C"], indent=2)

    def test_one_known_comps_seek_to_end(self):
        comp_a = self.comp_with_id("A")
        comp_b = self.comp_with_id("B")
        comp_c = self.comp_with_id("C")
        io = StringIO('["B"]')
        io.seek(0, os.SEEK_END)
        known_competitions = KnownCompetitions(io)

        filtered_comps = known_competitions.filter_competitions(
            [comp_a, comp_b, comp_c]
        )

        assert filtered_comps == [comp_a, comp_c]
        assert io.getvalue() == json.dumps(["A", "B", "C"], indent=2)
