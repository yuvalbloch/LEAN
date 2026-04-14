"""
emailer.py — send the HTML digest via SMTP (works with Gmail, Fastmail, etc.).

For Gmail: enable 2FA and create an App Password at
https://myaccount.google.com/apppasswords — use that as SMTP_PASSWORD.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(
    html_body: str,
    subject: str,
    to_address: str,
    from_address: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_address
    msg["To"]      = to_address

    # Plain-text fallback (minimal — most clients will render HTML)
    plain = "Your morning digest is ready. Open this email in an HTML-capable client to read it."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_address, [to_address], msg.as_string())
