# view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from models import AppConfig
from viewmodel import LiverpoolViewModel


class LiverpoolApp(tk.Tk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.title("Liverpool Orders - Fase 1 (Dry-run)")
        self.geometry("900x600")

        # Estilo dark + azul
        self.configure(bg="#121212")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#121212")
        style.configure("TLabel", background="#121212", foreground="#f5f5f5")
        style.configure(
            "TButton", background="#0d6efd", foreground="#ffffff", padding=6
        )
        style.map("TButton", background=[("active", "#1d7ffd")])
        style.configure(
            "Treeview",
            background="#1e1e1e",
            foreground="#f5f5f5",
            fieldbackground="#1e1e1e",
        )

        self.config_obj = config
        self.vm = LiverpoolViewModel(self.config_obj)
        self.vm.set_log_callback(self.append_log)

        self.selected_dates_vars = {}

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Arriba: config base dir
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Carpeta base:").grid(row=0, column=0, sticky="w")
        self.base_dir_var = tk.StringVar(value=str(self.config_obj.base_dir))
        self.base_dir_entry = ttk.Entry(
            top_frame, textvariable=self.base_dir_var, width=60
        )
        self.base_dir_entry.grid(row=0, column=1, sticky="we", padx=5)
        btn_browse = ttk.Button(
            top_frame, text="Elegir...", command=self.choose_base_dir
        )
        btn_browse.grid(row=0, column=2, padx=5)

        top_frame.columnconfigure(1, weight=1)

        # Botones principales
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        btn_scan = ttk.Button(
            btn_frame,
            text="1) Escanear pedidos en /orders (dry-run)",
            command=self.on_scan_click,
        )
        btn_scan.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        btn_process = ttk.Button(
            btn_frame,
            text="2) Procesar detalles y generar archivos",
            command=self.on_process_click,
        )
        btn_process.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        btn_accept = ttk.Button(
            btn_frame,
            text="3) Aceptar pedidos y descargar guías",
            command=self.on_accept_click,
        )
        
        btn_merge = ttk.Button(
            btn_frame,
            text="4) Unir guías PDF (reintentar)",
            command=self.on_merge_click,
        )
        btn_merge.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        btn_accept.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        # Centro: fechas
        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            mid_frame,
            text="Fechas con pedidos 'Pendiente de aceptación':",
        ).pack(anchor="w")

        self.dates_frame = ttk.Frame(mid_frame)
        self.dates_frame.pack(fill=tk.X, pady=5)

        # Abajo: log
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(log_frame, text="Log:").pack(anchor="w")
        self.log_text = tk.Text(
            log_frame,
            height=15,
            bg="#1e1e1e",
            fg="#f5f5f5",
            insertbackground="#f5f5f5",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def choose_base_dir(self):
        folder = filedialog.askdirectory(
            title="Selecciona carpeta base",
            initialdir=str(self.config_obj.base_dir),
        )
        if folder:
            self.base_dir_var.set(folder)
            self.config_obj.base_dir = Path(folder)

    def append_log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def refresh_dates_checkboxes(self):
        for w in self.dates_frame.winfo_children():
            w.destroy()
        self.selected_dates_vars.clear()

        dates_summary = self.vm.get_dates_summary()
        if not dates_summary:
            ttk.Label(
                self.dates_frame,
                text="(No hay fechas con pendientes por ahora)",
            ).pack(anchor="w")
            return

        for fecha, count in dates_summary:
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(
                self.dates_frame,
                text=f"{fecha}  →  {count} pedidos",
                variable=var,
            )
            cb.pack(anchor="w")
            self.selected_dates_vars[fecha] = var

    def on_scan_click(self):
        try:
            self.append_log("=== Iniciando escaneo ===")
            self.vm.scan_orders()
            self.refresh_dates_checkboxes()
            self.append_log("=== Escaneo terminado ===")
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el escaneo: {e}")

    def on_process_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para procesar."
            )
            return

        self.append_log(
            f"=== Procesando detalles (dry-run) para fechas: {', '.join(selected_dates)} ==="
        )
        try:
            self.vm.process_details_dry_run(selected_dates)
            self.append_log("=== Proceso Fase 1 completado ===")
            messagebox.showinfo(
                "Listo", "Fase 1 completada. Revisa las carpetas por día."
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error procesando detalles: {e}"
            )

    def on_accept_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para aceptar/descargar guías."
            )
            return

        self.append_log(
            f"=== Fase 2: Aceptar + descargar guías para fechas: {', '.join(selected_dates)} ==="
        )
        try:
            self.vm.accept_and_download_labels(selected_dates)
            self.append_log("=== Proceso Fase 2 completado ===")
            messagebox.showinfo(
                "Listo",
                "Fase 2 completada. Revisa la carpeta de cada día (subcarpeta 'guias' y GUIAS_<fecha>.pdf).",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error en Fase 2: {e}")

    def on_merge_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para unir guías."
            )
            return

        self.append_log(
            f"=== Fase 3: Uniendo guías para fechas: {', '.join(selected_dates)} ==="
        )
        try:
            self.vm.merge_labels(selected_dates)
            self.append_log("=== Fase 3 completada ===")
            messagebox.showinfo(
                "Listo",
                "Fase 3 completada. Revisa los PDF GUIAS_<fecha>.pdf y los TXT de faltantes.",
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error uniendo guías: {e}"
            )
