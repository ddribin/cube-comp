import json
import logging
from typing import TextIO

from .competition import Competition


class KnownCompetitions:
    def __init__(self, file_io: TextIO | None) -> None:
        self.logger = logging.getLogger(__name__)
        assert file_io is not None
        self.file_io: TextIO = file_io

    def filter_competitions(self, competitions: list[Competition]) -> list[Competition]:
        known_comps = self._read_known_comps_file()
        self.logger.debug("Known comps: %r" % known_comps)
        filtered_comps = self._filter_competitions(competitions, known_comps)
        self.logger.debug("Filtered comps: %r" % filtered_comps)

        new_known_comps = [c.id for c in competitions]
        self.logger.debug("New known comps: %r" % new_known_comps)
        self._write_known_comps_file(new_known_comps)
        return filtered_comps

    def _filter_competitions(
        self, competitions: list[Competition], known_competitions: list[str]
    ) -> list[Competition]:
        # This whole method could be a list comprehension but I want to log
        # skipped competitions.
        filtered_comps = []
        for comp in competitions:
            if comp.id not in known_competitions:
                filtered_comps.append(comp)
            else:
                self.logger.info(
                    "Skipping already known competition with ID %r", comp.id
                )
        return filtered_comps

    def _read_known_comps_file(self) -> list[str]:
        self.file_io.seek(0)
        known_comps_json = self.file_io.read()
        if known_comps_json == "":
            return []
        known_comps = json.loads(known_comps_json)
        self.logger.info("Read %r known comps" % len(known_comps))
        return known_comps

    def _write_known_comps_file(self, known_comps: list[str]) -> None:
        self.logger.info("Writing %r known comps" % len(known_comps))
        self.file_io.seek(0)
        self.file_io.truncate(0)
        json.dump(known_comps, self.file_io, indent=2)
