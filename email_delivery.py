import mimetypes
import runpy
import shutil
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_print_files_and_copy_guides(base_dir, selected_dates, log=print):
    if not selected_dates:
        raise ValueError("Selecciona al menos una fecha.")

    shein_dir = Path(__file__).resolve().parent.parent / "guias-shein"
    gmail_sender = runpy.run_path(str(shein_dir / "gmail_sender.py"))
    password = gmail_sender["load_app_password"](shein_dir / ".gmail.json")
    if not password:
        raise RuntimeError("No se encontró la configuración de Gmail de guias-shein.")

    sender = "quintanatorresjoseemmanuel1dm@gmail.com"
    recipients = ("cecilia.unipride@gmail.com", "almacenu4u@gmail.com")
    files = []
    missing = []
    for date in selected_dates:
        day_dir = Path(base_dir) / date
        print_pdf = day_dir / f"PEDIDOS_{date}_print.pdf"
        guides_pdf = day_dir / f"GUIAS_{date}.pdf"
        if not print_pdf.is_file():
            missing.append(str(print_pdf))
        if not guides_pdf.is_file():
            missing.append(str(guides_pdf))
        files.append((date, print_pdf, guides_pdf))
    if missing:
        raise FileNotFoundError("Faltan archivos:\n" + "\n".join(missing))

    messages = []
    for date, print_pdf, _ in files:
        message = EmailMessage()
        message["From"] = sender
        message["To"] = ", ".join(recipients)
        message["Subject"] = f"Pedidos Liverpool - {date}"
        message.set_content(f"Hola,\n\nAdjunto el archivo de pedidos de Liverpool del {date}.\n\nSaludos.")
        mime_type, _ = mimetypes.guess_type(print_pdf.name)
        maintype, subtype = (mime_type or "application/pdf").split("/", 1)
        message.add_attachment(
            print_pdf.read_bytes(), maintype=maintype, subtype=subtype, filename=print_pdf.name
        )
        raw_message = message.as_bytes()
        if len(raw_message) > 25_000_000:
            raise ValueError(f"El correo del {date} supera el límite de 25 MB de Gmail.")
        messages.append((date, raw_message))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(sender, password.replace(" ", ""))
        for date, message in messages:
            smtp.sendmail(sender, recipients, message)
            log(f"  [OK] Correo enviado para {date}.")

    print_dir = Path.home() / "Desktop" / "guias-shein" / "imprimir"
    print_dir.mkdir(parents=True, exist_ok=True)
    for date, _, guides_pdf in files:
        shutil.copy2(guides_pdf, print_dir / guides_pdf.name)
        log(f"  [OK] Guías de {date} copiadas a imprimir.")
    return {"sent": len(files), "copied": len(files), "recipients": recipients}
