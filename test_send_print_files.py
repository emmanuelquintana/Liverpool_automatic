import unittest
from pathlib import Path
from unittest.mock import patch

from email_delivery import send_print_files_and_copy_guides


class SendPrintFilesTest(unittest.TestCase):
    def test_sends_print_per_date_and_copies_merged_guides(self):
        class FakeSmtp:
            sent = []

            def __init__(self, *args, **kwargs): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def login(self, sender, password): self.login_args = (sender, password)
            def sendmail(self, sender, recipients, message): self.sent.append((recipients, message))

        date = "2026-09-09"
        root = Path("C:/Liverpool/auto")
        home = Path("C:/Users/test")
        with patch("email_delivery.runpy.run_path", return_value={"load_app_password": lambda _: "secret"}), patch(
            "email_delivery.smtplib.SMTP_SSL", FakeSmtp
        ), patch("email_delivery.Path.home", return_value=home), patch.object(
            Path, "is_file", return_value=True
        ), patch.object(Path, "read_bytes", return_value=b"%PDF-pedidos"), patch.object(
            Path, "mkdir"
        ), patch("email_delivery.shutil.copy2") as copy2:
            result = send_print_files_and_copy_guides(root, [date], log=lambda _: None)

        self.assertEqual(result["sent"], 1)
        self.assertEqual(
            result["recipients"],
            ("cecilia.unipride@gmail.com", "almacenu4u@gmail.com"),
        )
        self.assertEqual(len(FakeSmtp.sent), 1)
        copy2.assert_called_once_with(
            root / date / f"GUIAS_{date}.pdf",
            home / "Desktop" / "guias-shein" / "imprimir" / f"GUIAS_{date}.pdf",
        )


if __name__ == "__main__":
    unittest.main()
