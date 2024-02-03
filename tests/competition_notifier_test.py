from io import StringIO
from typing import Any

from cube_comp import (
    CompetitionAPI,
    CompetitionNotifier,
    CompetitionNotifierOptions,
    EmailService,
)


class FakeCompetitionAPI(CompetitionAPI):
    def fetch_competitions(
        self, query: str | None, country: str | None, sort_desc=False
    ) -> list[dict[str, Any]]:
        comp_a = self.minimal_dict_with_id("A")
        comp_b = self.minimal_dict_with_id("B")
        comp_c = self.minimal_dict_with_id("C")
        return [comp_a, comp_b, comp_c]

    def minimal_dict_with_id(self, id: str) -> dict[str, Any]:
        dict = {
            "id": id,
            "name": "A Name",
            "short_name": "A Short Name",
            "start_date": "2024-01-01",
            "results_posted_at": None,
            "city": "Chicago, IL",
            "venue": "Wrigley Field",
            "website": "https://example.com/AnID/",
        }
        return dict


class EmailServiceSpy(EmailService):
    def __init__(self) -> None:
        super().__init__()
        self.configure_smtp_count = 0
        self.send_email_count = 0

    def configure_smtp(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
    ) -> None:
        self.configure_smtp_count += 1

    def send_email(
        self, to_address: str, from_address: str, subject: str, content: str
    ) -> None:
        self.send_email_count += 1
        self.sent_email_content = content


class TestCompetitionNotifierContext:
    def __init__(self) -> None:
        self.competition_api = FakeCompetitionAPI()
        self.email_service = EmailServiceSpy()
        self.stdout_io = StringIO()
        self.notifier = CompetitionNotifier(self.competition_api, self.email_service)


class TestCompetitionNotifier:
    def test_notify_to_stdout_with_no_known_competitions(self) -> None:
        ctx = TestCompetitionNotifierContext()

        options = CompetitionNotifierOptions(
            stdout_io=ctx.stdout_io,
            query="illinois",
            country="US",
        )

        ctx.notifier.notify(options)

        assert ctx.stdout_io.getvalue() != ""
        assert ctx.stdout_io.getvalue().count("ID: ") == 3
        assert ctx.email_service.configure_smtp_count == 0
        assert ctx.email_service.send_email_count == 0

    def test_notify_to_stdout_with_known_competitions(self) -> None:
        ctx = TestCompetitionNotifierContext()

        options = CompetitionNotifierOptions(
            stdout_io=ctx.stdout_io,
            query="illinois",
            country="US",
            known_competitions_io=StringIO('["A","B","C"]'),
        )

        ctx.notifier.notify(options)

        assert ctx.stdout_io.getvalue() != ""
        assert ctx.stdout_io.getvalue().count("ID: ") == 0
        assert ctx.email_service.configure_smtp_count == 0
        assert ctx.email_service.send_email_count == 0

    def test_notify_to_email_with_no_known_competitions(self) -> None:
        ctx = TestCompetitionNotifierContext()

        options = CompetitionNotifierOptions(
            stdout_io=ctx.stdout_io,
            query="illinois",
            country="US",
            email_to="user1@example.com",
            email_from="user2@example.com",
        )

        ctx.notifier.notify(options)

        assert ctx.stdout_io.getvalue() == ""
        assert ctx.stdout_io.getvalue().count("ID: ") == 0
        assert ctx.email_service.configure_smtp_count == 1
        assert ctx.email_service.send_email_count == 1
        assert ctx.email_service.sent_email_content.count("ID: ") == 3

    def test_notify_to_email_with_known_competitions(self) -> None:
        ctx = TestCompetitionNotifierContext()

        options = CompetitionNotifierOptions(
            stdout_io=ctx.stdout_io,
            query="illinois",
            country="US",
            known_competitions_io=StringIO('["A","B","C"]'),
            email_to="user1@example.com",
            email_from="user2@example.com",
        )

        ctx.notifier.notify(options)

        assert ctx.stdout_io.getvalue() == ""
        assert ctx.stdout_io.getvalue().count("ID: ") == 0
        assert ctx.email_service.configure_smtp_count == 0
        assert ctx.email_service.send_email_count == 0
