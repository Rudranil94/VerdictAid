from typing import Dict, Any, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_config = {
            "hostname": settings.SMTP_SERVER,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "use_tls": True
        }
        self.template_env = Environment(
            loader=FileSystemLoader("app/templates/email")
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        from_name: Optional[str] = None
    ) -> bool:
        """Send an email using a template."""
        try:
            # Create message
            message = MIMEMultipart()
            from_name = from_name or settings.EMAIL_FROM_NAME
            message["From"] = f"{from_name} <{settings.EMAIL_FROM_ADDRESS}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Render template
            template = self.template_env.get_template(f"{template_name}.html")
            html_content = template.render(**template_data)
            message.attach(MIMEText(html_content, "html"))

            # Send email
            await aiosmtplib.send(
                message,
                sender=settings.EMAIL_FROM_ADDRESS,
                recipients=[to_email],
                **self.smtp_config
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_notification_email(
        self,
        to_email: str,
        notification_type: str,
        notification_data: Dict[str, Any]
    ) -> bool:
        """Send a notification email."""
        template_map = {
            "document_processed": {
                "template": "document_processed",
                "subject": "Document Processing Complete"
            },
            "task_completed": {
                "template": "task_completed",
                "subject": "Task Completion Notification"
            }
        }

        template_info = template_map.get(notification_type)
        if not template_info:
            logger.error(f"Unknown notification type: {notification_type}")
            return False

        return await self.send_email(
            to_email=to_email,
            subject=template_info["subject"],
            template_name=template_info["template"],
            template_data=notification_data
        )

email_service = EmailService()
