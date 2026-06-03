from unittest.mock import MagicMock, patch
from workers.base_worker import BaseWorker

class ConcreteWorker(BaseWorker):
    name = "test_worker"
    def run(self): return "done"

def test_base_worker_returns_result():
    with patch("db.sqlite_db.get_connection") as mock_conn, \
         patch("db.sqlite_db.update_employee_status") as mock_status:
        mock_conn.return_value = MagicMock()
        w = ConcreteWorker()
        result = w.execute()
    assert result == "done"
    mock_status.assert_called_once()

def test_base_worker_updates_status_on_error():
    class FailWorker(BaseWorker):
        name = "fail_worker"
        def run(self): raise ValueError("oops")

    with patch("db.sqlite_db.get_connection") as mock_conn, \
         patch("db.sqlite_db.update_employee_status") as mock_status:
        mock_conn.return_value = MagicMock()
        import pytest
        with pytest.raises(ValueError):
            FailWorker().execute()
    # status should be called with error message
    mock_status.assert_called_once()
    args = mock_status.call_args[0]
    assert "error" in args[2]
