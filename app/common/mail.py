"""
Mail Service Utility
Handles email sending via SMTP with TLS using application configuration.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Union, Optional
from flask import current_app

logger = logging.getLogger(__name__)


def send_email(
    to: Union[str, List[str]],
    subject: str,
    body: str,
    html: Optional[str] = None,
    sender: Optional[str] = None
) -> bool:
    """
    Send an email via SMTP (TLS).

    Args:
        to: Recipient email address or list of addresses.
        subject: Subject line.
        body: Plain text body.
        html: Optional HTML body.
        sender: Optional sender address (defaults to configured Gmail_Username).

    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        if current_app:
            server_host = current_app.config.get("SMTP_SERVER") or os.getenv("SMTP_Server", "smtp.gmail.com")
            port = int(current_app.config.get("SMTP_PORT_TLS") or os.getenv("SMTP_Port_TLS", 587))
            username = current_app.config.get("GMAIL_USERNAME") or os.getenv("Gmail_Username", "")
            password = current_app.config.get("GMAIL_PASSWORD") or os.getenv("Gmail_Password", "")
            default_sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username
        else:
            server_host = os.getenv("SMTP_Server", "smtp.gmail.com")
            port = int(os.getenv("SMTP_Port_TLS", 587))
            username = os.getenv("Gmail_Username", "")
            password = os.getenv("Gmail_Password", "")
            default_sender = username

        from_addr = sender or default_sender
        recipients = [to] if isinstance(to, str) else list(to)

        msg = MIMEMultipart("alternative")
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        # Attach text and html parts
        msg.attach(MIMEText(body, "plain", "utf-8"))
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(server_host, port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(from_addr, recipients, msg.as_string())

        logger.info(f"Email successfully sent to {recipients} with subject: '{subject}'")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
        return False
