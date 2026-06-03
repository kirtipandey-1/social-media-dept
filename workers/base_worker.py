import logging
from abc import ABC, abstractmethod
from db import sqlite_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

class BaseWorker(ABC):
    name: str = "base"

    def execute(self):
        log = logging.getLogger(self.name)
        log.info("Starting")
        conn = None
        try:
            conn = sqlite_db.get_connection()
            result = self.run()
            sqlite_db.update_employee_status(conn, self.name, "ok")
            log.info("Completed: %s", result)
            return result
        except Exception as e:
            log.error("Failed: %s", e)
            if conn:
                try:
                    sqlite_db.update_employee_status(conn, self.name, f"error: {str(e)[:100]}")
                except Exception:
                    pass
            raise

    @abstractmethod
    def run(self): ...
