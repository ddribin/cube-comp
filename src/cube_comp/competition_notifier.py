import inspect
import logging
from dataclasses import dataclass
from typing import Any, TextIO

from jinja2 import Environment, PackageLoader, select_autoescape

from .command_error import CommandError
from .competition import Competition
from .competition_api import CompetitionAPI
from .email_service import EmailService
from .known_competitions import KnownCompetitions


@dataclass
class CompetitionNotifierOptions:
    stdout_io: TextIO

    query: str | None = None
    country: str | None = None
    known_competitions_io: TextIO | None = None

    email_to: str | None = None
    email_from: str | None = None

    smtp_host = "localhost"
    smtp_port = 25
    smtp_user: str | None = None
    smtp_password: str | None = None


class CompetitionNotifierInvocation:
    def __init__(
        self,
        competition_api: CompetitionAPI,
        email_service: EmailService,
        options: CompetitionNotifierOptions,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.competition_api = competition_api
        self.email_service = email_service
        self.opts = options

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        competitions = self.fetch_competitions()
        filtered_competitions = self.filter_competitions(competitions)
        self.output_competitions(filtered_competitions)

    def fetch_competitions(self) -> list[Competition]:
        self.logger.info(
            "Fetching competitions with query: %r, country: %r",
            self.opts.query,
            self.opts.country,
        )
        json_competitions = self.competition_api.fetch_competitions(
            query=self.opts.query, country=self.opts.country
        )
        competitions = [
            self.competition_from_dict(json_comp) for json_comp in json_competitions
        ]
        return competitions

    def competition_from_dict(self, dict: dict[str, Any]) -> Competition:
        self.logger.debug("Converting competition:\n%r", dict)
        competition = Competition.from_dict(dict)
        self.logger.debug("Converted competition %r", competition)
        return competition

    def filter_competitions(self, competitions: list[Competition]) -> list[Competition]:
        if self.opts.known_competitions_io is None:
            self.logger.info("Not filtering competitions")
            return competitions

        known_comps = KnownCompetitions(self.opts.known_competitions_io)
        filtered_comps = known_comps.filter_competitions(competitions)
        return filtered_comps

    def output_competitions(self, competitions: list[Competition]) -> None:
        if self.opts.email_to is None:
            self.print_competitions(competitions)
        else:
            self.email_competitions(competitions, self.opts.email_to)

    def print_competitions(self, competitions: list[Competition]) -> None:
        self.logger.info("Printing %r competitions", len(competitions))
        rendered = self.render_competitions(competitions)
        print(rendered, file=self.opts.stdout_io)

    def email_competitions(
        self, competitions: list[Competition], email_address: str
    ) -> None:
        if len(competitions) > 0:
            self.send_email(competitions, email_address)
        else:
            self.logger.info("No competitions, so skipping email")

    def send_email(self, competitions: list[Competition], to_address: str) -> None:
        try:
            self.logger.info(
                "Emailing %r competitions to %r", len(competitions), to_address
            )

            self.email_service.configure_smtp(
                self.opts.smtp_host,
                self.opts.smtp_port,
                self.opts.smtp_user,
                self.opts.smtp_password,
            )

            rendered = self.render_competitions(competitions)
            from_address = (
                self.opts.email_from if self.opts.email_from is not None else to_address
            )
            self.email_service.send_email(
                to_address=to_address,
                from_address=from_address,
                subject="WCA Competition Notification",
                content=rendered,
            )
        except ConnectionRefusedError:
            raise CommandError(
                f"Cannot send email: Connection refused: {self.opts.smtp_host}"
            )

    def render_competitions(self, competitions: list[Competition]) -> str:
        env = Environment(
            loader=PackageLoader("cube_comp"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )
        template = env.get_template("competitions.txt.j2")
        rendered = template.render(competitions=competitions)
        rendered = inspect.cleandoc(rendered)
        return rendered


class CompetitionNotifier:
    def __init__(
        self,
        competition_api: CompetitionAPI,
        email_service: EmailService,
    ) -> None:
        self._competition_api = competition_api
        self._email_service = email_service

    def configure_smtp(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
    ) -> None:
        pass

    def notify(self, options: CompetitionNotifierOptions) -> None:
        invocation = CompetitionNotifierInvocation(
            self._competition_api, self._email_service, options
        )
        invocation()
