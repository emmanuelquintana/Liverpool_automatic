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
    "check_missing_guides": "Guías Faltantes",
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


# ──────────────────────────────────────────────
#  Diálogo de Catálogo de Modelos
# ──────────────────────────────────────────────

class ModelCatalogDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Catálogo de Modelos")
        self.geometry("840x620")
        self.minsize(700, 500)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        from models_manager import load_catalog, save_catalog
        self._load_catalog_fn = load_catalog
        self._save_catalog_fn = save_catalog
        self.catalog = self._load_catalog_fn()
        self._editing_model = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 8))
        ctk.CTkLabel(
            top_frame,
            text="🏷️ Catálogo de Modelos Registrados",
            font=("Roboto Medium", 17),
        ).pack(side="left")

        # Contenedor central
        mid_container = ctk.CTkFrame(self, fg_color="transparent")
        mid_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        mid_container.grid_columnconfigure(0, weight=3)
        mid_container.grid_columnconfigure(1, weight=2)
        mid_container.grid_rowconfigure(0, weight=1)

        # Izquierda: Lista de modelos
        list_box = ctk.CTkFrame(mid_container, corner_radius=8)
        list_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_box.grid_rowconfigure(1, weight=1)
        list_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            list_box,
            text="Modelos en catálogo:",
            font=("Roboto Medium", 13),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.models_scroll = ctk.CTkScrollableFrame(list_box)
        self.models_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.models_scroll.grid_columnconfigure(0, weight=1)

        # Derecha: Formulario
        self.form_box = ctk.CTkFrame(mid_container, corner_radius=8)
        self.form_box.grid(row=0, column=1, sticky="nsew")
        self.form_box.grid_columnconfigure(0, weight=1)

        self.lbl_form = ctk.CTkLabel(
            self.form_box,
            text="➕ Registrar Nuevo Modelo",
            font=("Roboto Medium", 14),
        )
        self.lbl_form.pack(anchor="w", padx=15, pady=(12, 8))

        ctk.CTkLabel(self.form_box, text="Nombre del Modelo:", font=("Roboto", 12)).pack(anchor="w", padx=15, pady=(4, 2))
        self.entry_name = ctk.CTkEntry(self.form_box, placeholder_text="Ej: BARCELONA")
        self.entry_name.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkLabel(self.form_box, text="Alias / Claves SKU (separados por coma):", font=("Roboto", 12)).pack(anchor="w", padx=15, pady=(4, 2))
        self.entry_aliases = ctk.CTkEntry(self.form_box, placeholder_text="Ej: BCN, BARCELONA, COPO26BCN")
        self.entry_aliases.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkLabel(self.form_box, text="Colores (Formato NOMBRE:CODIGO):", font=("Roboto", 12)).pack(anchor="w", padx=15, pady=(4, 2))
        self.entry_colors = ctk.CTkEntry(self.form_box, placeholder_text="NEGRO:01, MARINO:04, BLANCO:03, VINO:15")
        self.entry_colors.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkLabel(self.form_box, text="Tallas (separadas por coma):", font=("Roboto", 12)).pack(anchor="w", padx=15, pady=(4, 2))
        self.entry_sizes = ctk.CTkEntry(self.form_box, placeholder_text="CH, M, G, XG")
        self.entry_sizes.pack(fill="x", padx=15, pady=(0, 10))

        btn_row = ctk.CTkFrame(self.form_box, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(5, 10))

        self.btn_save_model = ctk.CTkButton(
            btn_row, text="Guardar Modelo", command=self._save_form_model,
            fg_color="#27ae60", hover_color="#1e8449",
        )
        self.btn_save_model.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_clear_form = ctk.CTkButton(
            btn_row, text="Limpiar", command=self._clear_form,
            fg_color="#555", hover_color="#666", width=70,
        )
        self.btn_clear_form.pack(side="right")

        # Bottom row
        bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 15))

        ctk.CTkButton(
            bottom_row, text="Cerrar", command=self.destroy,
            fg_color="#555", hover_color="#666", width=100,
        ).pack(side="right")

        self._refresh_list()
        self.update_idletasks()
        self._center(parent)

    def _refresh_list(self):
        for w in self.models_scroll.winfo_children():
            w.destroy()

        if not self.catalog:
            ctk.CTkLabel(self.models_scroll, text="(No hay modelos registrados)", text_color="gray").pack(pady=20)
            return

        for m_name, m_data in list(self.catalog.items()):
            card = ctk.CTkFrame(self.models_scroll, corner_radius=6, fg_color=("#f0f0f0", "#2b2b2b"))
            card.pack(fill="x", pady=4, padx=2)

            header_card = ctk.CTkFrame(card, fg_color="transparent")
            header_card.pack(fill="x", padx=8, pady=(6, 2))

            ctk.CTkLabel(header_card, text=m_name, font=("Roboto Medium", 13)).pack(side="left")

            btn_del = ctk.CTkButton(
                header_card, text="🗑", width=28, height=24,
                fg_color="#c0392b", hover_color="#96281b",
                command=lambda name=m_name: self._delete_model(name)
            )
            btn_del.pack(side="right", padx=(4, 0))

            btn_edit = ctk.CTkButton(
                header_card, text="✏️", width=28, height=24,
                fg_color="#2980b9", hover_color="#2471a3",
                command=lambda name=m_name: self._load_into_form(name)
            )
            btn_edit.pack(side="right")

            colors_str = ", ".join([f"{c['name']} ({c['code']})" for c in m_data.get("colors", [])])
            sizes_str = ", ".join(m_data.get("sizes", []))
            aliases_str = ", ".join(m_data.get("aliases", []))

            info_text = f"Alias: {aliases_str or '-'}\nColores: {colors_str}\nTallas: {sizes_str}"
            ctk.CTkLabel(
                card, text=info_text, font=("Roboto", 11),
                justify="left", anchor="w", text_color=("gray30", "gray70")
            ).pack(anchor="w", padx=10, pady=(0, 6))

    def _load_into_form(self, model_name: str):
        m_data = self.catalog.get(model_name)
        if not m_data:
            return
        self._editing_model = model_name
        self.lbl_form.configure(text=f"✏️ Editar: {model_name}")
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, model_name)

        self.entry_aliases.delete(0, tk.END)
        self.entry_aliases.insert(0, ", ".join(m_data.get("aliases", [])))

        colors_list = [f"{c['name']}:{c['code']}" for c in m_data.get("colors", [])]
        self.entry_colors.delete(0, tk.END)
        self.entry_colors.insert(0, ", ".join(colors_list))

        self.entry_sizes.delete(0, tk.END)
        self.entry_sizes.insert(0, ", ".join(m_data.get("sizes", [])))

    def _clear_form(self):
        self._editing_model = None
        self.lbl_form.configure(text="➕ Registrar Nuevo Modelo")
        self.entry_name.delete(0, tk.END)
        self.entry_aliases.delete(0, tk.END)
        self.entry_colors.delete(0, tk.END)
        self.entry_sizes.delete(0, tk.END)

    def _save_form_model(self):
        name = self.entry_name.get().strip().upper()
        if not name:
            show_warning(self, "Campo requerido", "Ingresa el nombre del modelo.")
            return

        aliases_raw = self.entry_aliases.get().strip()
        aliases = [a.strip().upper() for a in aliases_raw.split(",") if a.strip()]
        if name not in aliases:
            aliases.insert(0, name)

        colors_raw = self.entry_colors.get().strip()
        colors = []
        if colors_raw:
            for part in colors_raw.split(","):
                part = part.strip()
                if not part:
                    continue
                if ":" in part:
                    c_name, c_code = part.split(":", 1)
                    colors.append({"name": c_name.strip().upper(), "code": c_code.strip()})
                else:
                    colors.append({"name": part.strip().upper(), "code": "01"})
        else:
            colors = [
                {"name": "NEGRO", "code": "01"},
                {"name": "MARINO", "code": "04"},
                {"name": "BLANCO", "code": "03"},
                {"name": "VINO", "code": "15"},
            ]

        sizes_raw = self.entry_sizes.get().strip()
        sizes = [s.strip().upper() for s in sizes_raw.split(",") if s.strip()]
        if not sizes:
            sizes = ["CH", "M", "G", "XG"]

        if self._editing_model and self._editing_model != name:
            self.catalog.pop(self._editing_model, None)

        self.catalog[name] = {
            "aliases": aliases,
            "colors": colors,
            "sizes": sizes,
        }

        self._save_catalog_fn(self.catalog)
        self._clear_form()
        self._refresh_list()
        show_info(self, "Guardado", f"Modelo '{name}' guardado correctamente en el catálogo.")

    def _delete_model(self, model_name: str):
        if show_confirm(self, "Eliminar Modelo", f"¿Deseas eliminar el modelo '{model_name}' del catálogo?"):
            self.catalog.pop(model_name, None)
            self._save_catalog_fn(self.catalog)
            if self._editing_model == model_name:
                self._clear_form()
            self._refresh_list()

    def _center(self, parent):
        dw, dh = self.winfo_width(), self.winfo_height()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        except Exception:
            x = (self.winfo_screenwidth() - dw) // 2
            y = (self.winfo_screenheight() - dh) // 2
        self.geometry(f"+{x}+{y}")


def show_model_catalog(parent):
    dlg = ModelCatalogDialog(parent)
    parent.wait_window(dlg)
