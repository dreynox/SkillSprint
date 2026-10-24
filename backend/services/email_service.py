import logging
import smtplib
from email.mime.text import MIMEText
from config import (
    OTP_EXPIRY_MINUTES,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)

class EmailService:
    def send_otp_email(self, email: str, otp: str, decoy_key: str = None) -> None:
        """Deliver OTP securely, containing SMTP failures."""
        try:
            self._send_raw_otp_email(email, otp)
        except Exception:
            # Do not log the email, OTP, SMTP password, or provider exception text.
            logger.error(
                "Password-reset OTP delivery failed",
                extra={
                    "event": "password_reset_otp_delivery_failed",
                    "recipient_key": decoy_key,
                },
            )

    def _send_raw_otp_email(self, email: str, otp: str) -> None:
        if not SMTP_HOST or not SMTP_FROM_EMAIL:
            # Local-development fallback retained from the existing application.
            print(f"[OTP][DEV] Password reset OTP for {email}: {otp}")
            return

        subject = "SkillSprint Password Reset OTP"
        body = (
            f"Your SkillSprint OTP is: {otp}\n\n"
            f"This code expires in {OTP_EXPIRY_MINUTES} minutes."
        )
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = email

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
        try:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls()
                server.ehlo()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, [email], msg.as_string())
        finally:
            server.quit()


def get_email_service() -> EmailService:
    return EmailService()
