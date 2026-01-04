# view.py
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path

from models import AppConfig
from viewmodel import LiverpoolViewModel

# Configuración global de CustomTkinter
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class LiverpoolApp(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.title("Liverpool Orders - Fase 1 (Dry-run)")
        self.geometry("1000x750")

        self.config_obj = config
        self.vm = LiverpoolViewModel(self.config_obj)
        self.vm.set_log_callback(self.append_log)

        self.selected_dates_vars = {}

        self._build_ui()

    def _build_ui(self):
        # --- Layout Principal ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # El contenido principal se expande

        # 1. Header / Configuración
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.lbl_base_dir = ctk.CTkLabel(
            self.header_frame, text="Carpeta Base:", font=("Roboto Medium", 14)
        )
        self.lbl_base_dir.grid(row=0, column=0, padx=15, pady=15)

        self.base_dir_var = tk.StringVar(value=str(self.config_obj.base_dir))
        self.entry_base_dir = ctk.CTkEntry(
            self.header_frame, textvariable=self.base_dir_var, height=35
        )
        self.entry_base_dir.grid(row=0, column=1, sticky="ew", padx=10)

        self.btn_browse = ctk.CTkButton(
            self.header_frame,
            text="Elegir...",
            command=self.choose_base_dir,
            width=100,
            height=35,
        )
        self.btn_browse.grid(row=0, column=2, padx=15)

        # 2. Panel Central (Botones + Fechas)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(1, weight=1)
        self.center_frame.grid_rowconfigure(0, weight=1)

        # 2.1 Columna Izquierda: Acciones
        self.actions_frame = ctk.CTkFrame(self.center_frame, corner_radius=10)
        self.actions_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.actions_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.actions_frame, text="Acciones", font=("Roboto Medium", 16)
        ).pack(pady=(15, 10))

        # Botones de acción con estilo
        btn_params = {"height": 40, "font": ("Roboto", 13), "corner_radius": 8}

        self.btn_scan = ctk.CTkButton(
            self.actions_frame,
            text="1) Escanear Pedidos (Dry-run)",
            command=self.on_scan_click,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            **btn_params
        )
        self.btn_scan.pack(fill="x", padx=20, pady=10)

        self.btn_process = ctk.CTkButton(
            self.actions_frame,
            text="2) Procesar Detalles",
            command=self.on_process_click,
            fg_color="#3498db",
            hover_color="#2980b9",
            **btn_params
        )
        self.btn_process.pack(fill="x", padx=20, pady=10)

        self.btn_accept = ctk.CTkButton(
            self.actions_frame,
            text="3) Aceptar y Descargar Guías",
            command=self.on_accept_click,
            fg_color="#e67e22",
            hover_color="#d35400",
            **btn_params
        )
        self.btn_accept.pack(fill="x", padx=20, pady=10)

        # Combo 2+3
        self.btn_auto_2_3 = ctk.CTkButton(
            self.actions_frame,
            text="2+3) Auto Procesar y Aceptar",
            command=self.on_auto_process_accept_click,
            fg_color="#D35400",  # Un color distinto, mezcla de azul y naranja
            hover_color="#A04000",
            **btn_params
        )
        self.btn_auto_2_3.pack(fill="x", padx=20, pady=10)

        self.btn_merge = ctk.CTkButton(
            self.actions_frame,
            text="4) Unir Guías PDF",
            command=self.on_merge_click,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            **btn_params
        )
        self.btn_merge.pack(fill="x", padx=20, pady=10)

        # 2.2 Columna Derecha: Fechas
        self.dates_container = ctk.CTkFrame(self.center_frame, corner_radius=10)
        self.dates_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.dates_container.grid_rowconfigure(1, weight=1)
        self.dates_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.dates_container,
            text="Fechas con Pendientes",
            font=("Roboto Medium", 16),
        ).grid(row=0, column=0, pady=(15, 10))

        # Scrollable Frame para las fechas
        self.dates_scroll_frame = ctk.CTkScrollableFrame(
            self.dates_container, label_text="Selecciona fechas"
        )
        self.dates_scroll_frame.grid(
            row=1, column=0, sticky="nsew", padx=15, pady=(0, 15)
        )

        # 3. Log (Abajo)
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.log_frame, text="Registro de Actividad", font=("Roboto Medium", 14)
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(self.log_frame, height=150, font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # 4. Footer / Créditos
        self.footer_label = ctk.CTkLabel(
            self,
            text="Desarrollado por Jose Emmanuel Quintana Torres",
            font=("Roboto", 10),
            text_color="gray",
        )
        self.footer_label.grid(row=3, column=0, pady=(0, 10))

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
        # No es necesario update_idletasks() tan agresivo en ctk, pero mal no hace
        # self.update_idletasks()

    def refresh_dates_checkboxes(self):
        # Limpiar widgets anteriores en el scroll frame
        for widget in self.dates_scroll_frame.winfo_children():
            widget.destroy()
        self.selected_dates_vars.clear()

        dates_summary = self.vm.get_dates_summary()
        if not dates_summary:
            ctk.CTkLabel(
                self.dates_scroll_frame,
                text="(No hay fechas con pendientes)",
                text_color="gray",
            ).pack(anchor="w", pady=5)
            return

        for fecha, count in dates_summary:
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                self.dates_scroll_frame,
                text=f"{fecha}  →  {count} pedidos",
                variable=var,
            )
            cb.pack(anchor="w", pady=5)
            self.selected_dates_vars[fecha] = var

    def on_scan_click(self):
        try:
            self.append_log("=== Iniciando escaneo ===")
            # Ejecutar en un hilo o after para no congelar UI sería ideal,
            # pero mantenemos lógica simple como se pidió.
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
            messagebox.showerror("Error", f"Error procesando detalles: {e}")

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

    def on_auto_process_accept_click(self):
        selected_dates = [
            d for d, var in self.selected_dates_vars.items() if var.get()
        ]
        if not selected_dates:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una fecha para el proceso automático (2+3)."
            )
            return

        self.append_log(
            f"=== Iniciando PROCESO AUTOMÁTICO (2 y then 3) para: {', '.join(selected_dates)} ==="
        )

        # Paso 1: Procesar Detalles
        try:
            self.append_log("--- [Auto] Paso 1: Procesar Detalles (Fase 1) ---")
            self.vm.process_details_dry_run(selected_dates)
        except Exception as e:
            messagebox.showerror("Error Auto", f"Falló Fase 1 en automático: {e}")
            self.append_log(f"!!! Error en Fase 1: {e}")
            return

        # Paso 2: Aceptar y Descargar
        try:
            self.append_log("--- [Auto] Paso 2: Aceptar y Descargar (Fase 2) ---")
            self.vm.accept_and_download_labels(selected_dates)
            
            self.append_log("=== PROCESO AUTOMÁTICO COMPLETADO EXITOSAMENTE ===")
            messagebox.showinfo(
                "Listo",
                "Proceso Automático (2+3) completado.\n\n"
                "1) Se procesaron detalles.\n"
                "2) Se aceptaron y descargaron guías.\n\n"
                "Revisa las carpetas correspondientes."
            )
        except Exception as e:
            messagebox.showerror("Error Auto", f"Falló Fase 2 en automático: {e}")
            self.append_log(f"!!! Error en Fase 2: {e}")

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
            messagebox.showerror("Error", f"Error uniendo guías: {e}")
