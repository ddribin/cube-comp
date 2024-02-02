import json
import logging

from .competition import Competition


class KnownCompetitions:
    def __init__(self, file: str | None) -> None:
        self.logger = logging.getLogger(__name__)
        self.file = file

    def filter_competitions(self, competitions: list[Competition]) -> list[Competition]:
        if self.file is None:
            return competitions

        known_comps = self.read_known_comps_file(self.file)
        self.logger.debug("Known comps: %r" % known_comps)
        filtered_comps = self._filter_competitions(competitions, known_comps)
        self.logger.debug("Filtered comps: %r" % filtered_comps)

        new_known_comps = [c.id for c in competitions]
        self.logger.debug("New known comps: %r" % new_known_comps)
        self.write_known_comps_file(self.file, new_known_comps)
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

    def read_known_comps_file(self, file: str) -> list[str]:
        try:
            with open(file, mode="r") as f:
                known_comps = json.load(f)
        except FileNotFoundError:
            known_comps = []
        self.logger.info("Read %r known comps" % len(known_comps))
        return known_comps

    def write_known_comps_file(self, file: str, known_comps: list[str]) -> None:
        self.logger.info("Writing %r known comps" % len(known_comps))
        with open(file, mode="w") as f:
            json.dump(known_comps, f, indent=2)
