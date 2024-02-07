import argparse
import logging
import sys
from pathlib import Path

from .command_error import CommandError
from .competition_api import WCACompetitionAPI
from .competition_notifier import CompetitionNotifier, CompetitionNotifierOptions
from .email_service import SMTPEmailService


class CommandLine:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._log_option: str | None = None
        self.prog: str
        self.notifier_opts = CompetitionNotifierOptions(stdout_io=sys.stdout)
        self.known_comps_file: str | None = None

    def execute(self) -> int:
        try:
            self.parse_arguments()
            self.run()
            return 0
        except CommandError as e:
            message = e.args[0]
            sys.stderr.write(f"{self.prog}: {message}\n")
            result = e.args[1] if len(e.args) == 2 else 1
            return result
        except Exception as e:
            self.logger.exception(e)
            sys.stderr.write(f"{self.prog}: Caught exception: {e}\n")
            return 2

    def run(self) -> None:
        logging.basicConfig(level=self.log_level)
        competition_api = WCACompetitionAPI()
        email_service = SMTPEmailService()
        notifier = CompetitionNotifier(competition_api, email_service)

        if self.known_comps_file is None:
            notifier.notify(self.notifier_opts)
        else:
            with open(self.known_comps_file, "a+") as known_comps_io:
                self.notifier_opts.known_competitions_io = known_comps_io
                notifier.notify(self.notifier_opts)

    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser()
        self.prog = parser.prog
        parser.add_argument(
            "query", type=str, help="query string", nargs="?", default=None
        )
        parser.add_argument(
            "-c", "--country", type=str, help="ISO country code", default="US"
        )
        parser.add_argument(
            "-k",
            "--known",
            type=str,
            help="known competitions JSON file",
            metavar="FILE",
        )
        parser.add_argument(
            "--email-to", type=str, help="Email output to ADDRESS", metavar="ADDRESS"
        )
        parser.add_argument(
            "--email-from",
            type=str,
            help="Use ADDRESS as From address",
            metavar="ADDRESS",
        )
        parser.add_argument(
            "--smtp-host", type=str, help="SMTP server host", metavar="HOST"
        )
        parser.add_argument("--smtp-port", type=int, help="SMTP port", default=0)
        parser.add_argument("--smtp-user", type=str, help="SMTP user")
        parser.add_argument(
            "--smtp-password-file", type=Path, help="SMTP password file"
        )

        parser.add_argument(
            "-L",
            "--log",
            choices=["debug", "info", "warning", "error"],
            default="warning",
            help="Set log level",
        )

        args = parser.parse_args()

        opts = self.notifier_opts

        opts.query = args.query
        opts.country = args.country
        self.known_comps_file = args.known

        opts.email_to = args.email_to
        opts.email_from = args.email_from

        if args.smtp_host is not None:
            opts.smtp_host = args.smtp_host
        opts.smtp_port = args.smtp_port
        self._parse_smtp_user_and_password(args, opts)
        self._log_option = args.log

    def _parse_smtp_user_and_password(
        self, args: argparse.Namespace, opts: CompetitionNotifierOptions
    ):
        # If there's a user the must be a password file
        if args.smtp_user is None:
            return
        if args.smtp_password_file is None:
            raise CommandError("SMTP user specified but no password file")
        smtp_password_file: Path = args.smtp_password_file

        opts.smtp_user = args.smtp_user
        opts.smtp_password = smtp_password_file.read_text().rstrip()

    @property
    def log_level(self) -> int:
        match self._log_option:
            case "debug":
                return logging.DEBUG

            case "info":
                return logging.INFO

            case "warning":
                return logging.WARNING

            case _:
                return logging.WARNING


def main() -> int:
    cli = CommandLine()
    return cli.execute()
