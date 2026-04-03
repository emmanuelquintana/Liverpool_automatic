# dialogs.py
"""
Modales personalizados con CustomTkinter para reemplazar los messagebox nativos.
Uso:
    from dialogs import show_info, show_warning, show_error, show_confirm
    show_info(parent, "Título", "Mensaje")
    ok = show_confirm(parent, "¿Continuar?", "¿Estás seguro?")
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional


# ──────────────────────────────────────────────
#  Paleta de colores para cada tipo de modal
# ──────────────────────────────────────────────
_STYLES = {
    "info": {
        "accent":   "#3498db",   # azul
        "icon":     "ℹ",
        "btn_ok":   "#3498db",
        "btn_ok_h": "#2980b9",
    },
    "success": {
        "accent":   "#2ecc71",   # verde
        "icon":     "✔",
        "btn_ok":   "#2ecc71",
        "btn_ok_h": "#27ae60",
    },
    "warning": {
        "accent":   "#e67e22",   # naranja
        "icon":     "⚠",
        "btn_ok":   "#e67e22",
        "btn_ok_h": "#d35400",
    },
    "error": {
        "accent":   "#e74c3c",   # rojo
        "icon":     "✖",
        "btn_ok":   "#e74c3c",
        "btn_ok_h": "#c0392b",
    },
}


class _BaseDialog(ctk.CTkToplevel):
    """
    Ventana modal base.  Las subclases sólo eligen el estilo y los botones.
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        style: str = "info",
        confirm: bool = False,   # True → muestra botón Cancelar
    ):
        super().__init__(parent)

        self._result: Optional[bool] = None
        style_cfg = _STYLES.get(style, _STYLES["info"])

        # ── Ventana ──────────────────────────────────────────
        self.title(title)
        self.resizable(False, False)
        self.grab_set()          # modal
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # ── Barra de acento lateral ───────────────────────────
        accent_bar = ctk.CTkFrame(self, width=6, fg_color=style_cfg["accent"], corner_radius=0)
        accent_bar.pack(side="left", fill="y")

        # ── Contenido principal ───────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True, padx=(16, 20), pady=20)

        # Fila superior: icono + título
        top_row = ctk.CTkFrame(main, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_row,
            text=style_cfg["icon"],
            font=("Segoe UI", 26),
            text_color=style_cfg["accent"],
            width=36,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_row,
            text=title,
            font=("Roboto Medium", 16),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Separador
        ctk.CTkFrame(main, height=1, fg_color="#444").pack(fill="x", pady=(0, 12))

        # Mensaje
        ctk.CTkLabel(
            main,
            text=message,
            font=("Roboto", 13),
            wraplength=380,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 20))

        # Botones
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x")

        if confirm:
            ctk.CTkButton(
                btn_row,
                text="Cancelar",
                command=self._on_cancel,
                fg_color="#555",
                hover_color="#666",
                width=110,
                height=36,
                font=("Roboto", 13),
                corner_radius=8,
            ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Aceptar",
            command=self._on_ok,
            fg_color=style_cfg["btn_ok"],
            hover_color=style_cfg["btn_ok_h"],
            width=110,
            height=36,
            font=("Roboto Medium", 13),
            corner_radius=8,
        ).pack(side="right")

        # ── Centrar sobre el padre ────────────────────────────
        self.update_idletasks()
        self._center(parent)

    def _center(self, parent):
        dw = self.winfo_width()
        dh = self.winfo_height()

        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except Exception:
            # fallback: centrar en pantalla
            px = (self.winfo_screenwidth() - dw) // 2
            py = (self.winfo_screenheight() - dh) // 2
            self.geometry(f"+{px}+{py}")
            return

        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _on_ok(self):
        self._result = True
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self._result = False
        self.grab_release()
        self.destroy()

    def get_result(self) -> Optional[bool]:
        return self._result


# ──────────────────────────────────────────────
#  Funciones de conveniencia (API pública)
# ──────────────────────────────────────────────

def _show(parent, title: str, message: str, style: str, confirm: bool = False) -> Optional[bool]:
    """Muestra el diálogo y espera a que se cierre (bloqueante)."""
    dlg = _BaseDialog(parent, title, message, style=style, confirm=confirm)
    parent.wait_window(dlg)
    return dlg.get_result()


def show_info(parent, title: str, message: str):
    _show(parent, title, message, style="info")


def show_success(parent, title: str, message: str):
    _show(parent, title, message, style="success")


def show_warning(parent, title: str, message: str):
    _show(parent, title, message, style="warning")


def show_error(parent, title: str, message: str):
    _show(parent, title, message, style="error")


def show_confirm(parent, title: str, message: str) -> bool:
    """Devuelve True si el usuario hizo clic en Aceptar, False si Cancelar o cerró."""
    return bool(_show(parent, title, message, style="warning", confirm=True))


# ──────────────────────────────────────────────
#  Dialogo de Configuracion
# ──────────────────────────────────────────────

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.title("Configuracion")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        ctk.CTkLabel(self, text="Configuracion avanzada",
                     font=("Roboto Medium", 16)).pack(anchor="w", padx=20, pady=(16, 6))
        ctk.CTkFrame(self, height=1, fg_color="#444").pack(fill="x", padx=20)

        ctk.CTkLabel(self, text="Timeout Selenium (segundos):",
                     font=("Roboto", 13), anchor="w").pack(fill="x", padx=20, pady=(12, 2))
        self._timeout_var = tk.StringVar(value=str(config.timeout))
        ctk.CTkEntry(self, textvariable=self._timeout_var,
                     width=120, font=("Roboto", 13)).pack(anchor="w", padx=20)
        ctk.CTkLabel(self,
                     text="(120 = 2 min. Sube si necesitas mas tiempo para el 2FA)",
                     font=("Roboto", 11), text_color="gray",
                     anchor="w").pack(fill="x", padx=20)

        ctk.CTkLabel(self, text="Ruta fallback msedgedriver.exe:",
                     font=("Roboto", 13), anchor="w").pack(fill="x", padx=20, pady=(12, 2))
        dr = ctk.CTkFrame(self, fg_color="transparent")
        dr.pack(fill="x", padx=20)
        self._driver_var = tk.StringVar(value=config.fallback_driver)
        ctk.CTkEntry(dr, textvariable=self._driver_var,
                     font=("Roboto", 12), width=320).pack(side="left")
        ctk.CTkButton(dr, text="...", width=36,
                      command=self._browse_driver).pack(side="left", padx=6)

        ctk.CTkFrame(self, height=1, fg_color="#333").pack(fill="x", padx=20, pady=12)
        self._overwrite_var = ctk.BooleanVar(value=config.overwrite_outputs)
        ctk.CTkCheckBox(
            self, text="Sobreescribir Excel/PDF si ya existen",
            variable=self._overwrite_var, font=("Roboto", 13)
        ).pack(anchor="w", padx=20, pady=(0, 14))

        ctk.CTkFrame(self, height=1, fg_color="#444").pack(fill="x", padx=20)
        br = ctk.CTkFrame(self, fg_color="transparent")
        br.pack(fill="x", padx=20, pady=12)
        ctk.CTkButton(br, text="Cancelar", command=self.destroy,
                      fg_color="#555", hover_color="#666", width=110).pack(side="left")
        ctk.CTkButton(br, text="Guardar", command=self._save,
                      fg_color="#2980b9", hover_color="#2471a3",
                      width=110).pack(side="right")
        self.update_idletasks()
        self._center(parent)

    def _browse_driver(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(
            title="msedgedriver.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if p:
            self._driver_var.set(p)

    def _center(self, parent):
        dw, dh = self.winfo_width(), self.winfo_height()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        except Exception:
            x = (self.winfo_screenwidth() - dw) // 2
            y = (self.winfo_screenheight() - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _save(self):
        from settings import save_settings
        try:
            timeout = int(self._timeout_var.get())
        except ValueError:
            timeout = self.config.timeout
        self.config.timeout = timeout
        self.config.fallback_driver = self._driver_var.get()
        self.config.overwrite_outputs = bool(self._overwrite_var.get())
        save_settings({
            "timeout": timeout,
            "fallback_driver": self.config.fallback_driver,
            "overwrite_outputs": self.config.overwrite_outputs,
        })
        self.grab_release()
        self.destroy()


def show_settings(parent, config):
    dlg = SettingsDialog(parent, config)
    parent.wait_window(dlg)


# ──────────────────────────────────────────────
#  Dialogo de Historial
# ──────────────────────────────────────────────

_EVENT_LABELS = {
    "scan": "Escaneo",
    "scan_old": "Escaneo (antiguos)",
    "process_dry_run": "Fase 1 - Procesar",
    "accept_download": "Fase 2 - Aceptar/Descargar",
    "merge_labels": "Unir PDFs",
    "process_old": "Antiguos",
    "reprocess": "Reproceso",
}


class HistoryDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Historial")
        self.geometry("560x460")
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Ultimas operaciones realizadas",
                     font=("Roboto Medium", 15)).grid(
            row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        scroll.grid_columnconfigure(0, weight=1)

        from history import get_recent
        entries = get_recent(30)
        if not entries:
            ctk.CTkLabel(
                scroll, text="(Sin historial aun)",
                text_color="gray", font=("Roboto", 13)
            ).pack(anchor="w", pady=20)
        else:
            for entry in entries:
                label = _EVENT_LABELS.get(entry.get("event", ""), entry.get("event", "?"))
                ts = entry.get("timestamp", "")
                dates = ", ".join(entry.get("dates", []) or [])
                stats = entry.get("stats", {}) or {}
                parts = []
                if stats.get("total"):
                    parts.append("Total: " + str(stats["total"]))
                if stats.get("ok"):
                    parts.append("OK " + str(stats["ok"]))
                if stats.get("error"):
                    parts.append("Err " + str(stats["error"]))
                stats_str = ("   " + "  .  ".join(parts)) if parts else ""
                card = ctk.CTkFrame(
                    scroll, corner_radius=6, fg_color=("#ececec", "#2b2b2b"))
                card.pack(fill="x", pady=3)
                ctk.CTkLabel(
                    card,
                    text=label + "   " + ts + "\n" + dates + stats_str,
                    font=("Roboto", 12), justify="left", anchor="w",
                ).pack(anchor="w", padx=12, pady=6)

        ctk.CTkButton(
            self, text="Cerrar", command=self.destroy,
            fg_color="#555", hover_color="#666"
        ).grid(row=2, column=0, padx=20, pady=(0, 14), sticky="e")

        self.update_idletasks()
        self._center(parent)

    def _center(self, parent):
        dw, dh = self.winfo_width(), self.winfo_height()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        except Exception:
            x = (self.winfo_screenwidth() - dw) // 2
            y = (self.winfo_screenheight() - dh) // 2
        self.geometry(f"+{x}+{y}")


def show_history(parent):
    dlg = HistoryDialog(parent)
    parent.wait_window(dlg)
