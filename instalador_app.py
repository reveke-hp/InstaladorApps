import os
import json
import subprocess
import threading
import tkinter as tk
import ctypes
import sys
import getpass
import time
import socket
import shutil 
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkFont
from apps_manager import filter_aplicaciones, obtener_parametros_instalacion, obtener_parametros_silenciosos, preparar_instalacion_especifica
from auth_credentials import AutenticacionCredenciales
from styles import setup_styles
from pathlib import Path 

class InstaladorModerno:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador MultiApp")
        self.root.geometry("1000x850")
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 1000, 850
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg='#f5f6f8')

        # ✔ PRIMERO: crear autenticación
        self.auth = AutenticacionCredenciales(root)

        # ✔ Mostrar dialogo de autenticación antes de continuar
        if not self.auth.mostrar_dialogo_autenticacion():
            root.quit()
            return

        # Configurar estilos
        self.colors = setup_styles(self.root)

        # Cargar config
        self.cargar_configuracion()

        self.aplicaciones_seleccionadas = set()
        self.cola_instalacion = []
        self.instalando = False
        self.check_vars = {}
        self.checkbox_widgets = {}
        self.search_var = tk.StringVar()
        self.contador_label = None
        self.estado_label = None

        self.crear_interfaz()

        if self.contador_label:
            self.actualizar_contador()

    
    # Nota: la configuración de estilos fue externalizada a `styles.py`.
    
    def cargar_configuracion(self):
        """Carga la configuración desde JSON"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Cargar solo aplicaciones, ignorar perfiles
                self.aplicaciones = data.get('aplicaciones', {})
                if not self.aplicaciones:
                    messagebox.showwarning("Configuración", "No hay aplicaciones configuradas en config.json")
        except FileNotFoundError:
            self.aplicaciones = {}
            messagebox.showwarning("Configuración", "No se encontró config.json")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Error en el formato de config.json")
            self.aplicaciones = {}
    
    def crear_config_por_defecto(self):
        """Crea un archivo de configuración por defecto"""
        self.aplicaciones = {}
        self.guardar_configuracion()
        messagebox.showinfo("Configuración", "Archivo config.json creado")

    def guardar_configuracion(self):
        """Guarda aplicaciones en config.json"""
        try:
            data = {
                'aplicaciones': self.aplicaciones,
                'perfiles': {}  # Perfiles vacío para mantener estructura
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.mostrar_mensaje("Configuración guardada en config.json")
        except Exception as e:
            self.mostrar_mensaje(f"Error guardando config: {e}")
    
    def crear_interfaz(self):
        """Crea la interfaz moderna"""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Header (colocado antes del contenedor para que quede arriba)
        self.crear_header(main_frame)

        # Contenedor centrado para el contenido (mejor presentación en pantallas grandes)
        container = ttk.Frame(main_frame, style='Modern.TFrame')
        container.pack(expand=True)
        container.configure(width=940)
        
        # Contenido principal (centrado)
        content_frame = ttk.Frame(container, style='Modern.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        # Panel izquierdo - Lista de aplicaciones
        self.crear_panel_aplicaciones(content_frame)

        # Panel derecho - Controles
        self.crear_panel_controles(content_frame)
        
        # Footer
        self.crear_footer(main_frame)
    
    def crear_header(self, parent):
        """Crea el encabezado simplificado sin perfiles"""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.pack(fill=tk.X)
        
        # Primera fila: Título e ícono CENTRADO
        title_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 8), expand=True)
        
        # Espacio a la izquierda para centrar
        tk.Label(title_frame, text="", bg=self.colors['bg']).pack(side=tk.LEFT, expand=True)
        
        # Ícono
        icon_label = tk.Label(title_frame, text="⚡", font=('Arial', 28), 
                             bg=self.colors['bg'], fg=self.colors['primary'])
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Texto del título
        title_label = tk.Label(title_frame, 
                              text="Instalador MultiApp",
                              font=('Segoe UI', 22, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['dark'])
        title_label.pack(side=tk.LEFT)
        
        # Espacio a la derecha (sin contador aquí)
        spacer = tk.Label(title_frame, text="", bg=self.colors['bg'])
        spacer.pack(side=tk.LEFT, expand=True)

        # Segunda fila: Información simple centrada
        info_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        info_frame.pack(fill=tk.X, pady=(0, 8), expand=True)
        
        # Espacio izquierdo para centrar
        tk.Label(info_frame, text="", bg=self.colors['bg']).pack(side=tk.LEFT, expand=True)
        
        # Información sobre las aplicaciones
        info_label = tk.Label(info_frame, 
                             text=f"📦 {len(self.aplicaciones)} aplicaciones disponibles",
                             font=('Segoe UI', 10),
                             bg=self.colors['bg'],
                             fg=self.colors['text_secondary'])
        info_label.pack(side=tk.LEFT)
        
        # Espacio derecho para centrar
        tk.Label(info_frame, text="", bg=self.colors['bg']).pack(side=tk.LEFT, expand=True)
    
    def crear_panel_aplicaciones(self, parent):
        """Crea el panel de aplicaciones"""
        # Frame contenedor
        left_frame = ttk.Frame(parent, style='Modern.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        
        # Tarjeta de aplicaciones
        card = tk.Frame(left_frame, bg=self.colors['card_bg'], relief='flat',
                       highlightbackground=self.colors['border'],
                       highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)
        
        # Header de la tarjeta
        card_header = tk.Frame(card, bg=self.colors['card_bg'])
        card_header.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(card_header, text="📦 Aplicaciones Disponibles",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text_primary']).pack(side=tk.LEFT)
        
        # Buscador (entrada) y controles rápidos
        right_controls = tk.Frame(card_header, bg=self.colors['card_bg'])
        right_controls.pack(side=tk.RIGHT)

        search_entry = tk.Entry(right_controls, textvariable=self.search_var,
                    font=('Segoe UI', 9), width=22,
                    relief='solid', bd=1, justify='left')
        search_entry.pack(side=tk.LEFT, padx=(0, 8))
        search_entry.insert(0, '')
        search_entry.bind('<KeyRelease>', lambda e: self.filtrar_aplicaciones())

        # Controles rápidos
        controls_frame = tk.Frame(right_controls, bg=self.colors['card_bg'])
        controls_frame.pack(side=tk.LEFT)
        
        ttk.Button(controls_frame, text="✓ Todo", command=self.seleccionar_todo, style='Secondary.TButton').pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(controls_frame, text="✗ Ninguno", command=self.deseleccionar_todo, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        
        # Contador de selecciones
        counter_frame = tk.Frame(card, bg=self.colors['card_bg'])
        counter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.contador_label = tk.Label(counter_frame, text="0 aplicación(es) seleccionada(s)",
                                       font=('Segoe UI', 9), bg=self.colors['card_bg'],
                                       fg=self.colors['text_secondary'])
        self.contador_label.pack(side=tk.LEFT)
        
        # Lista de aplicaciones con scroll
        self.crear_lista_con_scroll(card)
    
    def crear_lista_con_scroll(self, parent):
        """Crea la lista de aplicaciones con scroll"""
        # Frame para el canvas y scrollbar
        canvas_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 8))
        
        # Canvas y scrollbar (altura fija para mostrar más apps sin cambiar el tamaño de la ventana)
        canvas = tk.Canvas(canvas_frame, bg=self.colors['card_bg'], highlightthickness=0, height=520)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        
        self.apps_container = tk.Frame(canvas, bg=self.colors['card_bg'])
        self.apps_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.apps_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind del mouse wheel
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Cargar aplicaciones
        self.cargar_aplicaciones_modernas()
    
    def cargar_aplicaciones_modernas(self):
        """Carga las aplicaciones en formato moderno"""
        for widget in self.apps_container.winfo_children():
            widget.destroy()
        
        self.check_vars = {}
        self.checkbox_widgets = {}
        filtro = ''
        try:
            filtro = (self.search_var.get() or '').strip().lower()
        except Exception:
            filtro = ''

        for app_name, ruta in filter_aplicaciones(self.aplicaciones, filtro):
            self.crear_tarjeta_aplicacion(app_name, ruta)

        # Si no hay resultados, mostrar mensaje amable
        if not self.apps_container.winfo_children():
            info = tk.Label(self.apps_container, text="No se encontraron aplicaciones",
                            font=('Segoe UI', 10), bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
            info.pack(pady=20)

        # Actualizar contador si existe (por si el filtrado afectó selección visible)
        if self.contador_label:
            self.actualizar_contador()

    def filtrar_aplicaciones(self):
        """Refresca la lista según el contenido del buscador"""
        self.cargar_aplicaciones_modernas()
    
    def crear_tarjeta_aplicacion(self, app_name, ruta):
        """Crea una tarjeta para cada aplicación"""
        card = tk.Frame(self.apps_container, bg=self.colors['card_bg'],
                       relief='flat',
                       highlightbackground=self.colors['border'],
                       highlightthickness=1)
        card.pack(fill=tk.X, pady=3, padx=2)
        
        # Variable para el checkbox
        var = tk.BooleanVar()
        self.check_vars[app_name] = var
        # Inicializar estado del checkbox según selección actual
        try:
            var.set(app_name in self.aplicaciones_seleccionadas)
        except Exception:
            pass
        
        # Checkbox personalizado
        chk_frame = tk.Frame(card, bg=self.colors['card_bg'], width=28, height=28)
        chk_frame.pack(side=tk.LEFT, padx=15, pady=8)
        chk_frame.pack_propagate(False)
        
        chk_canvas = tk.Canvas(chk_frame, bg=self.colors['card_bg'], 
                      highlightthickness=0, width=24, height=24)
        chk_canvas.pack()
        
        # Dibujar checkbox inicial
        checkbox_rect = chk_canvas.create_rectangle(3, 3, 21, 21, 
                               outline=self.colors['border'],
                               width=1, fill='white')
        
        def toggle_check(*args):
            current = var.get()
            self.actualizar_checkbox_visual(chk_canvas, current)
            self.on_app_seleccionada(app_name, var)
            # Si el usuario seleccionó esta app desde el listado filtrado,
            # limpiar el buscador de aplicaciones para facilitar nuevas búsquedas
            try:
                if current and (self.search_var.get() or '').strip():
                    # Guardar selección actual para preservarla después del reload
                    self.aplicaciones_seleccionadas.add(app_name)
                    self.search_var.set('')
                    # Recargar la lista para mostrar todo de nuevo. La carga
                    # respetará self.aplicaciones_seleccionadas y volverá a marcar.
                    self.cargar_aplicaciones_modernas()
            except Exception:
                pass
        
        # Vincular la variable al cambio visual
        var.trace_add('write', toggle_check)

        # Asegurar apariencia inicial correcta
        try:
            self.actualizar_checkbox_visual(chk_canvas, var.get())
        except Exception:
            pass
        
        chk_canvas.bind("<Button-1>", lambda e: var.set(not var.get()))
        
        # Guardar referencia del canvas
        self.checkbox_widgets[app_name] = chk_canvas
        
        # Información de la aplicación
        info_frame = tk.Frame(card, bg=self.colors['card_bg'])
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15), pady=8)
        
        # Nombre de la aplicación
        name_label = tk.Label(info_frame, text=app_name,
                     font=('Segoe UI', 12, 'bold'),
                     bg=self.colors['card_bg'],
                     fg=self.colors['text_primary'],
                     anchor='w')
        name_label.pack(fill=tk.X)
        
        # Ruta (truncada si es muy larga)
        ruta_corta = ruta if len(ruta) < 80 else ruta[:77] + "..."
        path_label = tk.Label(info_frame, text=ruta_corta,
                     font=('Segoe UI', 9),
                     bg=self.colors['card_bg'],
                     fg=self.colors['text_secondary'],
                     anchor='w')
        path_label.pack(fill=tk.X)
        
        # Guardar referencias
        card.app_name = app_name
        card.var = var
    
    def actualizar_checkbox_visual(self, canvas, estado):
        """Actualiza la apariencia visual del checkbox"""
        canvas.delete("all")
        if estado:
            # Checkbox marcado
            canvas.create_rectangle(2, 2, 18, 18, 
                                  outline=self.colors['primary'],
                                  width=2, fill=self.colors['primary'])
            canvas.create_text(10, 10, text="✓", fill='white', font=('Arial', 10, 'bold'))
        else:
            # Checkbox desmarcado
            canvas.create_rectangle(2, 2, 18, 18, 
                                  outline=self.colors['border'],
                                  width=1, fill='white')
    
    def crear_panel_controles(self, parent):
        """Crea el panel de controles derecho"""
        right_frame = tk.Frame(parent, bg=self.colors['bg'], width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        right_frame.pack_propagate(False)
        
        # Tarjeta de acciones
        action_card = tk.Frame(right_frame, bg=self.colors['card_bg'],
                              relief='flat',
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        action_card.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(action_card, text="🚀 Acciones Rápidas",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text_primary'],
                anchor='w').pack(fill=tk.X, padx=20, pady=15)
        
        # Botones de acción
        btn_instalar = ttk.Button(action_card, text="▶ Iniciar Instalación",
                command=self.iniciar_instalacion,
                style='Primary.TButton')
        btn_instalar.pack(fill=tk.X, padx=20, pady=8)

        btn_cola = ttk.Button(action_card, text="📋 Ver Cola de Instalación",
                command=self.mostrar_cola_moderna,
                style='Secondary.TButton')
        btn_cola.pack(fill=tk.X, padx=20, pady=6)

        btn_actualizar = ttk.Button(action_card, text="🔄 Actualizar Lista",
                  command=self.actualizar_lista,
                  style='Secondary.TButton')
        btn_actualizar.pack(fill=tk.X, padx=20, pady=6)
        
        # Información
        info_card = tk.Frame(right_frame, bg=self.colors['card_bg'],
                            relief='flat',
                            highlightbackground=self.colors['border'],
                            highlightthickness=1)
        info_card.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(info_card, text="ℹ️ Información",
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.colors['text_primary'],
                anchor='w').pack(fill=tk.X, padx=20, pady=15)
        
        info_text = tk.Text(info_card, height=10, wrap=tk.WORD,
                           bg=self.colors['card_bg'],
                           fg=self.colors['text_secondary'],
                           relief='flat',
                           font=('Segoe UI', 9),
                           padx=15,
                           pady=10)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        info_text.insert('1.0', "Selecciona las aplicaciones que deseas instalar y haz clic en 'Iniciar Instalación'.\n\nLas aplicaciones se instalarán en el orden seleccionado.")
        info_text.config(state='disabled')
    
    def crear_footer(self, parent):
        footer_frame = tk.Frame(parent, bg=self.colors['bg'])
        footer_frame.pack(fill=tk.X, pady=(20, 0))

        self.progress_bar = ttk.Progressbar(
            footer_frame,
            style='Modern.Horizontal.TProgressbar',
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))
        self.progress_text = tk.Label(
            footer_frame,
            text="0/0 aplicaciones",
            font=('Segoe UI', 9),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.progress_text.pack()
        self.estado_label = tk.Label(
            footer_frame,
            text="Esperando…",
            font=('Segoe UI', 9),
            bg=self.colors['bg'],
            fg=self.colors['text_secondary']
        )
        self.estado_label.pack()
    
    def on_app_seleccionada(self, app_name, var):
        """Maneja la selección/deselección de aplicaciones"""
        if var.get():
            self.aplicaciones_seleccionadas.add(app_name)
        else:
            self.aplicaciones_seleccionadas.discard(app_name)
        
        self.actualizar_contador()
    
    def actualizar_contador(self):
        """Actualiza el contador de seleccionados"""
        if not self.contador_label:
            return
        count = len(self.aplicaciones_seleccionadas)
        self.contador_label.config(text=f"{count} aplicación(es) seleccionada(s)")
    
    def seleccionar_todo(self):
        """Selecciona todas las aplicaciones"""
        for app_name, var in self.check_vars.items():
            var.set(True)
            # Actualizar visualmente cada checkbox
            if app_name in self.checkbox_widgets:
                self.actualizar_checkbox_visual(self.checkbox_widgets[app_name], True)
        
        self.aplicaciones_seleccionadas = set(self.aplicaciones.keys())
        self.actualizar_contador()
    
    def deseleccionar_todo(self):
        """Deselecciona todas las aplicaciones"""
        for app_name, var in self.check_vars.items():
            var.set(False)
            # Actualizar visualmente cada checkbox
            if app_name in self.checkbox_widgets:
                self.actualizar_checkbox_visual(self.checkbox_widgets[app_name], False)
        
        self.aplicaciones_seleccionadas.clear()
        self.actualizar_contador()
    
    def actualizar_lista(self):
        """Actualiza la lista de aplicaciones"""
        self.cargar_configuracion()
        self.aplicaciones_seleccionadas.clear()
        self.cargar_aplicaciones_modernas()
        self.actualizar_contador()
        messagebox.showinfo("Éxito", "Lista de aplicaciones actualizada")
    
    def iniciar_instalacion(self):
        """Inicia el proceso de instalación"""
        if not self.aplicaciones_seleccionadas:
            messagebox.showwarning("Advertencia", "Selecciona al menos una aplicación")
            return
        
        if self.instalando:
            messagebox.showwarning("Advertencia", "Ya hay una instalación en progreso")
            return
        
        confirmacion = messagebox.askyesno(
            "Confirmar Instalación Silenciosa", 
            f"¿Instalar {len(self.aplicaciones_seleccionadas)} aplicación(es) en modo silencioso?\n\n"
            f"Las aplicaciones se instalarán automáticamente sin interacción del usuario."
        )
        
        if confirmacion:
            self.cola_instalacion = list(self.aplicaciones_seleccionadas)
            self.instalando = True
            self.progress_bar['maximum'] = len(self.cola_instalacion)
            self.progress_bar['value'] = 0
            
            # Iniciar instalación silenciosa en hilo separado
            thread = threading.Thread(target=self.ejecutar_cola_instalacion_silenciosa)
            thread.daemon = True
            thread.start()
    
    def ejecutar_cola_instalacion(self):
        """Este método se mantiene por compatibilidad, llama al método silencioso"""
        self.ejecutar_cola_instalacion_silenciosa()

    def tiene_permisos_escritura(self):
        """Verifica si tenemos permisos de escritura"""
        try:
            temp_file = os.path.join(os.environ['TEMP'], 'test_permisos.tmp')
            with open(temp_file, 'w') as f:
                f.write('test')
            os.remove(temp_file)
            return True
        except:
            return False

    def mostrar_error_detallado(self, titulo, mensaje):
        """Muestra errores detallados"""
        print(f"ERROR: {titulo} - {mensaje}")
        self.root.after(0, lambda: messagebox.showerror(titulo, mensaje))
    
    def actualizar_estado(self, mensaje):
        self.root.after(0, lambda: self.estado_label.config(text=mensaje))
    
    def actualizar_progreso(self, valor):
        self.root.after(0, lambda: self.progress_bar.config(value=valor))
        total = len(self.cola_instalacion)
        self.root.after(0, lambda: self.progress_text.config(text=f"{valor}/{total} aplicaciones"))
    
    def mostrar_mensaje(self, mensaje):
        print(f"INFO: {mensaje}")
    
    def mostrar_error(self, mensaje):
        self.root.after(0, lambda: messagebox.showerror("Error", mensaje))
    
    def mostrar_cola_moderna(self):
        """Muestra la cola de instalación moderna"""
        if not self.aplicaciones_seleccionadas:
            messagebox.showinfo("Cola Vacía", "No hay aplicaciones seleccionadas para instalar")
            return
        
        mensaje = "🎯 Aplicaciones en cola de instalación:\n\n"
        for i, app_name in enumerate(self.aplicaciones_seleccionadas, 1):
            mensaje += f"{i}. {app_name}\n"
            mensaje += f"   📍 {self.aplicaciones[app_name]}\n\n"
        
        messagebox.showinfo("Cola de Instalación", mensaje)
    
    def es_administrador():
        """Verifica si el programa se ejecuta como administrador"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def ejecutar_como_administrador():
        """Reinicia el programa con permisos de administrador"""
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
    
    def preparar_instalador_local(self, ruta_red):
        """Copia el instalador de la red al disco local para evitar problemas de red"""
        try:
            # Verificar si ya está en local
            if not ruta_red.startswith('\\\\'):
                return ruta_red
                
            # DEBUG: Mostrar información de la ruta
            self.mostrar_mensaje(f"[DEBUG] Ruta original: {ruta_red}")
            self.mostrar_mensaje(f"[DEBUG] ¿Existe en red?: {os.path.exists(ruta_red)}")
            
            # Si no existe en la red, buscar alternativas
            if not os.path.exists(ruta_red):
                nombre_archivo = os.path.basename(ruta_red)
                self.mostrar_mensaje(f"[DEBUG] Archivo no encontrado, buscando alternativas para: {nombre_archivo}")
                
                # Intentar rutas alternativas comunes
                rutas_alternativas = [
                    f"\\\\10.99.8.108\\aplicaciones\\{nombre_archivo}",
                    f"\\\\10.99.8.108\\d\\{nombre_archivo}",
                    f"\\\\10.99.8.108\\aplicaciones\\Polichequeos\\{nombre_archivo}",
                    f"\\\\10.99.8.108\\aplicaciones\\Polichequeos\\instalador\\{nombre_archivo}",
                    f"\\\\10.99.8.108\\aplicaciones\\Polichequeos\\ultima_version\\{nombre_archivo}",
                ]
                
                for ruta_alt in rutas_alternativas:
                    if os.path.exists(ruta_alt):
                        self.mostrar_mensaje(f"[DEBUG] ✅ Encontrado en ubicación alternativa: {ruta_alt}")
                        ruta_red = ruta_alt
                        break
                else:
                    # Si ninguna ruta alternativa funciona
                    self.mostrar_mensaje(f"[DEBUG] ❌ No se encontró el archivo en ninguna ubicación alternativa")
                    return ruta_red  # Devolver la original para manejar el error después
                    
            # Crear directorio temporal
            temp_dir = os.path.join(os.environ['TEMP'], 'instaladores_temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            nombre_archivo = os.path.basename(ruta_red)
            ruta_local = os.path.join(temp_dir, nombre_archivo)
            
            # Verificar si ya existe y es reciente (menos de 1 hora)
            if os.path.exists(ruta_local):
                tiempo_modificacion = os.path.getmtime(ruta_local)
                tiempo_actual = time.time()
                if (tiempo_actual - tiempo_modificacion) < 3600:  # 1 hora
                    self.mostrar_mensaje(f"📁 Usando copia local existente: {nombre_archivo}")
                    return ruta_local
            
            # Intentar copiar desde la red
            self.mostrar_mensaje(f"📥 Copiando {nombre_archivo} a local...")
            
            # Primero intentar acceso directo
            try:
                import shutil
                shutil.copy2(ruta_red, ruta_local)
                self.mostrar_mensaje(f"✅ Copiado exitosamente a: {ruta_local}")
                return ruta_local
            except PermissionError:
                self.mostrar_mensaje("🔐 Error de permisos, intentando mapear unidad de red...")
                ruta_mapeada = self.mapear_unidad_red(ruta_red)
                if ruta_mapeada and ruta_mapeada != ruta_red:
                    shutil.copy2(ruta_mapeada, ruta_local)
                    self.mostrar_mensaje(f"✅ Copiado via unidad mapeada: {ruta_local}")
                    return ruta_local
                else:
                    raise Exception("No se pudo acceder al archivo en la red")
            except FileNotFoundError:
                self.mostrar_mensaje(f"❌ Archivo no encontrado: {ruta_red}")
                raise Exception(f"El archivo {nombre_archivo} no existe en la ruta especificada")
            except Exception as e:
                self.mostrar_mensaje(f"❌ Error copiando archivo: {e}")
                raise
                        
        except Exception as e:
            self.mostrar_mensaje(f"❌ Error en preparar_instalador_local: {e}")
            # Intentar usar la ruta original
            return ruta_red
        
    def ejecutar_cola_instalacion_silenciosa(self):
        """Ejecuta la instalación manejando problemas de red con credenciales"""
        total = len(self.cola_instalacion)
        exitosos = 0
        fallidos = 0
        
        for i, app_name in enumerate(self.cola_instalacion):
            ruta_original = self.aplicaciones[app_name]
            
            self.actualizar_estado(f"🔧 Preparando {app_name}... ({i+1}/{total})")
            self.actualizar_progreso(i)
            
            try:
                # FLUJO NORMAL - SIN instalaciones especiales
                ruta_instalador = self.preparar_instalador_local(ruta_original)
                
                if not os.path.exists(ruta_instalador):
                    self.mostrar_mensaje(f"❌ {app_name} - Archivo no accesible: {ruta_instalador}")
                    fallidos += 1
                    continue
                
                # Obtener parámetros silenciosos
                config = preparar_instalacion_especifica(app_name, ruta_instalador)
                parametros = config['parametros']
                
                self.mostrar_mensaje(f"⚙️ Instalando: {os.path.basename(ruta_instalador)}")
                self.mostrar_mensaje(f"📁 Ruta: {ruta_instalador}")
                self.mostrar_mensaje(f"📋 Parámetros: {' '.join(parametros[1:]) if len(parametros) > 1 else 'ninguno'}")
                
                # Construir argumentos
                args_list = parametros[1:] if len(parametros) > 1 else []
                args_str = ' '.join([f'"{arg}"' for arg in args_list])
                
                self.mostrar_mensaje(f"📋 Ejecutando instalador sin credenciales (probando)...")
                
                # Intenta primero sin credenciales (usando el usuario actual)
                proceso = subprocess.Popen(
                    f'"{ruta_instalador}" {args_str}',
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                try:
                    stdout, stderr = proceso.communicate(timeout=config['timeout'])
                    codigo_salida = proceso.returncode
                    
                    stdout_str = stdout.decode('latin-1', errors='ignore') if stdout else ""
                    stderr_str = stderr.decode('latin-1', errors='ignore') if stderr else ""
                    
                    if stdout_str.strip():
                        self.mostrar_mensaje(f"OUTPUT: {stdout_str[:300]}")
                    if stderr_str.strip():
                        self.mostrar_mensaje(f"ERROR: {stderr_str[:300]}")
                    
                    # Códigos de éxito comunes
                    codigos_exito = [0, 3010, 1641, 2]
                    
                    if codigo_salida in codigos_exito:
                        self.mostrar_mensaje(f"✅ {app_name} instalado exitosamente (código: {codigo_salida})")
                        exitosos += 1
                    else:
                        # Si falla sin credenciales, intenta con credenciales
                        self.mostrar_mensaje(f"⚠️ Intento sin credenciales falló (código {codigo_salida}), intentando con credenciales...")
                        exitosos, fallidos = self._ejecutar_con_credenciales(app_name, ruta_instalador, args_str, config, exitosos, fallidos)
                        
                except subprocess.TimeoutExpired:
                    proceso.kill()
                    self.mostrar_mensaje(f"⏰ {app_name} - Timeout")
                    fallidos += 1
                    
            except Exception as e:
                self.mostrar_mensaje(f"❌ {app_name} - Error: {str(e)}")
                import traceback
                self.mostrar_mensaje(f"Traceback: {traceback.format_exc()[:300]}")
                fallidos += 1
            
            time.sleep(2)
        
        # Limpiar archivos temporales
        self.limpiar_temporales()
        
        # Mostrar resumen
        self.actualizar_progreso(total)
        self.instalando = False
        self.mostrar_resumen_instalacion(exitosos, fallidos, total)

    def _ejecutar_con_credenciales(self, app_name, ruta_instalador, args_str, config, exitosos, fallidos):
        """Ejecuta la instalación FORZANDO modo completamente silencioso"""
        try:
            # Usar credenciales de ADMIN
            usuario_admin = self.auth.credenciales_admin['usuario']
            password_admin = self.auth.credenciales_admin['password']
            
            # Extraer usuario sin dominio
            if '\\' in usuario_admin:
                usuario_solo = usuario_admin.split('\\')[1]
            else:
                usuario_solo = usuario_admin

            password_escaped = password_admin.replace('"', '`"').replace('$', '`$').replace("'", "`'")
            ruta_escaped = ruta_instalador.replace('"', '`"')

            # SCRIPT POWERSHELL QUE FUERZA INSTALACIÓN EN SEGUNDO PLANO
            script_ps = f'''
    # Configuración para ejecución completamente silenciosa
    $securePassword = ConvertTo-SecureString "{password_escaped}" -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential("{usuario_solo}", $securePassword)

    try {{
        Write-Host "🚀 Iniciando instalación COMPLETAMENTE SILENCIOSA de {app_name}..."
        
        # Crear proceso con configuración ultra-silenciosa
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "{ruta_escaped}"
        $processInfo.Arguments = "{' '.join(config['parametros'][1:])}"  # Todos los parámetros silenciosos
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false  # IMPORTANTE: No usar shell
        $processInfo.CreateNoWindow = $true    # NO crear ventana
        $processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
        
        # Iniciar proceso con credenciales de admin
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        
        # EJECUTAR SIN ESPERAR (para evitar bloqueos)
        $process.Start() | Out-Null
        
        # Esperar de forma asíncrona con timeout
        $timeout = {config['timeout'] * 1000}
        $startTime = Get-Date
        $completed = $false
        
        while (-not $completed) {{
            if ($process.HasExited) {{
                $completed = $true
                Write-Host "✅ Proceso completado. Código: $($process.ExitCode)"
                exit $process.ExitCode
            }}
            
            $elapsed = (Get-Date) - $startTime
            if ($elapsed.TotalMilliseconds -gt $timeout) {{
                # Timeout - matar proceso y todos sus hijos
                Write-Host "⏰ Timeout alcanzado, terminando proceso..."
                try {{
                    # Matar proceso padre
                    $process.Kill()
                    # Buscar y matar procesos hijos relacionados
                    Get-WmiObject Win32_Process | Where-Object {{ 
                        $_.ParentProcessId -eq $process.Id -or 
                        $_.Name -like "*setup*" -or 
                        $_.Name -like "*install*" 
                    }} | ForEach-Object {{ 
                        try {{ $_.Terminate() }} catch {{ }}
                    }}
                }} catch {{ }}
                exit 1
            }}
            
            Start-Sleep -Seconds 5
        }}
    }}
    catch {{
        Write-Host "❌ Error crítico: $($_.Exception.Message)"
        exit 1
    }}
    '''

            # Ejecutar el script PowerShell
            proceso = subprocess.Popen(
            config['parametros'],  # Usar la lista completa de parámetros
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.HIGH_PRIORITY_CLASS  # Flags combinados
        )

            # Esperar con timeout extendido
            stdout, stderr = proceso.communicate(timeout=config['timeout'] + 60)
            codigo_salida = proceso.returncode

            # Logs para debugging
            stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""

            if stdout_str.strip():
                self.mostrar_mensaje(f"📄 {app_name} OUTPUT: {stdout_str}")
            if stderr_str.strip():
                self.mostrar_mensaje(f"📄 {app_name} ERROR: {stderr_str}")

            # Códigos de éxito expandidos
            codigos_exito = [0, 3010, 1641, 2, 1605, 1618, 8192, 9999]

            if codigo_salida in codigos_exito:
                self.mostrar_mensaje(f"✅ {app_name} instalado COMPLETAMENTE EN SILENCIO")
                exitosos += 1
            else:
                self.mostrar_mensaje(f"❌ {app_name} - Falló en modo silencioso (código: {codigo_salida})")
                fallidos += 1

        except subprocess.TimeoutExpired:
            self.mostrar_mensaje(f"⏰ {app_name} - Timeout en modo silencioso")
            fallidos += 1
        except Exception as e:
            self.mostrar_mensaje(f"❌ {app_name} - Error en modo silencioso: {str(e)}")
            fallidos += 1

        return exitosos, fallidos

    def mostrar_resumen_instalacion(self, exitosos, fallidos, total):
        """Muestra el resumen final de la instalación"""
        resumen = f"Proceso completado:\n✅ {exitosos} exitosas\n❌ {fallidos} fallidas\n📊 Total: {total}"
        self.mostrar_mensaje(resumen)
        # Limpiar estado de la instalación
        self.actualizar_estado("Listo para instalar")
        self.root.after(0, lambda: messagebox.showinfo("Resumen de Instalación", resumen))
    
    def limpiar_temporales(self):
        """Limpia archivos temporales y desconecta unidades de red"""
        try:
            # Desconectar unidad T: si existe
            subprocess.run('net use T: /delete /y', shell=True, 
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    
    def mapear_unidad_red(self, ruta_completa):
        """Mapea automáticamente la unidad de red usando credenciales guardadas"""
        try:
            # Extraer información de la ruta de red
            if ruta_completa.startswith('\\\\'):
                partes = ruta_completa.split('\\')
                servidor = partes[2]
                recurso = '\\'.join(partes[3:])
                
                # Unidad temporal a usar
                unidad = 'T:'
                
                # Primero desconectar si ya existe
                subprocess.run(f'net use {unidad} /delete /y', 
                            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Intentar mapear con credenciales de dominio
                usuario_dominio = self.auth.credenciales_dominio['usuario']
                password_dominio = self.auth.credenciales_dominio['password']
                
                comando = f'net use {unidad} "\\\\{servidor}\\aplicaciones" /user:{usuario_dominio} {password_dominio} /persistent:no'
                resultado = subprocess.run(comando, shell=True, 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                
                if resultado.returncode == 0:
                    self.mostrar_mensaje("✅ Unidad de red mapeada con credenciales de dominio")
                    nueva_ruta = f"{unidad}\\{recurso}"
                    return nueva_ruta
                else:
                    error_output = resultado.stderr.decode('latin-1', errors='ignore')
                    self.mostrar_mensaje(f"❌ Error mapeando red: {error_output}")
                    return ruta_completa
                    
            return ruta_completa
            
        except Exception as e:
            self.mostrar_mensaje(f"⚠️ Error mapeando red: {e}")
            return ruta_completa

    def pedir_credenciales_red(self, servidor, unidad, recurso):
        """Este método ya no se usa - las credenciales se obtienen en la autenticación inicial"""
        pass

def main():
    root = tk.Tk()
    app = InstaladorModerno(root)
    root.mainloop()

if __name__ == "__main__":
    main()