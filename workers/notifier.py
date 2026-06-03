"""Telegram report notifier worker."""
import asyncio
import logging
from workers.base_worker import BaseWorker
from config import load_settings

log = logging.getLogger("notifier")


def format_for_telegram(markdown: str) -> str:
    """Trim to Telegram's 4096 char limit."""
    return markdown[:4090] + "\n…" if len(markdown) > 4096 else markdown


class TelegramNotifier(BaseWorker):
    def __init__(self, report_type: str = "daily"):
        self.report_type = report_type

    @property
    def name(self) -> str:
        return f"notifier_{self.report_type}"

    def run(self) -> str:
        import telegram
        from mcp_servers import reports_server
        s = load_settings()
        token = s.get("telegram", {}).get("bot_token", "")
        chat_id = s.get("telegram", {}).get("chat_id", "")

        if not token or not chat_id:
            log.warning("Telegram not configured — skipping send")
            return "skipped: not configured"

        if self.report_type == "daily":
            report = reports_server.generate_daily_report()
        elif self.report_type == "weekly":
            report = reports_server.generate_weekly_report()
        elif self.report_type == "monthly":
            report = reports_server.generate_monthly_report()
        else:
            report = reports_server.get_report(self.report_type)

        emoji = {"daily": "🎵", "weekly": "📊", "monthly": "📈"}.get(self.report_type, "📋")
        msg = format_for_telegram(
            f"{emoji} *Social Media Dept — {self.report_type.title()} Brief*\n\n{report}"
        )

        async def _send():
            bot = telegram.Bot(token=token)
            await bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="Markdown"
            )

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_send())
        finally:
            loop.close()

        log.info("Telegram %s report sent", self.report_type)
        return f"sent {self.report_type} report"


if __name__ == "__main__":
    import sys
    report_type = sys.argv[1] if len(sys.argv) > 1 else "daily"
    TelegramNotifier(report_type).execute()
