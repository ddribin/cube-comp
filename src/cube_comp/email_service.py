import smtplib
from email.message import EmailMessage

from typing_extensions import Protocol


class EmailService(Protocol):
    def configure_smtp(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
    ) -> None:
        pass

    def send_email(
        self, to_address: str, from_address: str, subject: str, content: str
    ) -> None:
        pass


class SMTPEmailService(EmailService):
    def __init__(self) -> None:
        self.smtp_host = "localhost"
        self.smtp_port = 25
        self.smtp_user: str | None = None
        self.smtp_password: str | None = None

    def configure_smtp(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send_email(
        self, to_address: str, from_address: str, subject: str, content: str
    ) -> None:
        msg = EmailMessage()
        msg.set_content(content)
        msg["Subject"] = subject
        msg["To"] = to_address
        msg["From"] = from_address

        s = smtplib.SMTP(self.smtp_host, port=self.smtp_port)
        if self.smtp_port == 587:
            s.starttls()
            if self.smtp_user is not None:
                assert self.smtp_password is not None
                s.login(self.smtp_user, self.smtp_password)
        s.send_message(msg)
        s.quit()
