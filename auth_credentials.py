import subprocess
import ctypes
import socket
import tkinter as tk
from tkinter import ttk, messagebox
import getpass


class AutenticacionCredenciales:
    """Maneja la autenticación de credenciales de dominio y administrador
    (Extraída desde `instalador_app.py` para modularidad)."""
    def __init__(self, root):
        self.root = root
        self.credenciales_dominio = None
        self.credenciales_admin = None
        self.hostname = socket.gethostname()
        self.colores = {
            'bg': '#f1f5f9',
            'card_bg': '#ffffff',
            'primary': '#007bff',
            'primary_light': '#007bff',
            'border': '#e2e8f0',
            'text_primary': '#334155',
            'text_secondary': '#64748b'
        }

    def validar_credenciales_admin(self, usuario, password):
        """Valida que las credenciales de admin sean correctas"""
        try:
            # Intenta usar las credenciales para ejecutar un comando simple
            script_test = (
                f"$cred = New-Object System.Management.Automation.PSCredential("
                f"'{usuario}', "
                f"(ConvertTo-SecureString '{password.replace(chr(39), chr(39)+chr(39))}' -AsPlainText -Force));"
                f"$proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','echo test' "
                f"-Credential $cred -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput NUL;"
                f"exit $proc.ExitCode"
            )

            proceso = subprocess.Popen(
                ['powershell.exe', '-NoProfile', '-Command', script_test],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            stdout, stderr = proceso.communicate(timeout=5)
            return proceso.returncode == 0
        except:
            return False

    def _has_stored_credential_for_server(self, server_ip='10.99.8.108', share_path='\\\\10.99.8.108\\aplicaciones'):
        """Comprueba si en Credential Manager hay una entrada relacionada con el servidor
        y si esa entrada permite acceder al share indicado (Test-Path).
        Devuelve True si existe credencial almacenada y la ruta es accesible."""
        try:
            # Listar credenciales guardadas
            proc = subprocess.run(['cmdkey', '/list'], capture_output=True, text=True)
            out = (proc.stdout or '') + (proc.stderr or '')
            # DEBUG: mostrar salida de cmdkey para diagnóstico
            print(f"[DEBUG][auth] cmdkey output:\n{out}")
            # Buscamos específicamente si hay una credencial para el dominio ua\
            # porque la política requiere credenciales del dominio 'ua\<usuario>'
            has_ua = 'ua\\' in out.lower() or 'ua\\' in out
            has_server = server_ip in out or share_path in out
            if (has_ua or has_server):
                # Probar acceso al share usando PowerShell Test-Path
                p = subprocess.run([
                    'powershell.exe', '-NoProfile', '-Command',
                    f"Test-Path '{share_path}'"
                ], capture_output=True, text=True)
                stdout = (p.stdout or '').strip().lower()
                # DEBUG: mostrar resultado de Test-Path
                print(f"[DEBUG][auth] Test-Path '{share_path}' -> {stdout}")
                if 'true' in stdout:
                    return True
        except Exception:
            pass
        return False

    def _get_current_whoami(self):
        try:
            p = subprocess.run(['whoami'], capture_output=True, text=True)
            return (p.stdout or '').strip()
        except Exception:
            # Fallback a getpass
            user = getpass.getuser()
            try:
                hostname = socket.gethostname()
                return f"{hostname}\\{user}"
            except Exception:
                return user

    def _is_user_in_local_administrators(self):
        """Comprueba si el usuario actual pertenece al grupo de Administradores locales."""
        # Primero intentar la verificación rápida y fiable
        try:
            if bool(ctypes.windll.shell32.IsUserAnAdmin()):
                return True
        except Exception:
            # Si falla, continuamos con fallback textual
            pass

        try:
            who = self._get_current_whoami()
            # Obtener solo el nombre de cuenta (parte después de la barra invertida)
            if '\\' in who:
                account = who.split('\\', 1)[1]
            else:
                account = who

            # Listar miembros del grupo Administrators (nombre en inglés puede diferir en sistemas localizados)
            p = subprocess.run(['net', 'localgroup', 'Administrators'], capture_output=True, text=True)
            out = (p.stdout or '').lower()
            # Verificamos si aparece el nombre de cuenta completo o la parte simple
            if account.lower() in out or who.lower() in out:
                return True
        except Exception:
            pass

        return False

    def mostrar_dialogo_autenticacion(self):
        """Muestra el diálogo de autenticación al iniciar la app"""
        auth_window = tk.Toplevel(self.root)
        auth_window.title("Autenticación Requerida")
        auth_window.configure(bg=self.colores['bg'])
        auth_window.resizable(False, False)

        # Size and center on screen
        width, height = 520, 380
        auth_window.update_idletasks()
        sw = auth_window.winfo_screenwidth()
        sh = auth_window.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        auth_window.geometry(f"{width}x{height}+{x}+{y}")

        auth_window.transient(self.root)
        auth_window.grab_set()

        # Pre-checks: credencial ua\ en Credential Manager + acceso al share
        has_ua_cred = False
        try:
            has_ua_cred = self._has_stored_credential_for_server()
        except Exception:
            has_ua_cred = False

        # Comprobar pertenencia al grupo Administrators (local)
        try:
            is_local_admin = self._is_user_in_local_administrators()
        except Exception:
            # Fallback a IsUserAnAdmin (elevado)
            try:
                is_local_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
            except Exception:
                is_local_admin = False

        # Si ya existe credencial del dominio (ua\...) y el usuario local es admin,
        # podemos continuar sin pedir credenciales.
        # DEBUG: imprimir valores detectados antes de decidir
        print(f"[DEBUG][auth] has_ua_cred={has_ua_cred}, is_local_admin={is_local_admin}, whoami={self._get_current_whoami()}")
        if has_ua_cred and is_local_admin:
            self.credenciales_dominio = None
            # Usamos el usuario local actual sin contraseña (ejecución con usuario existente)
            self.credenciales_admin = {
                'usuario': self._get_current_whoami(),
                'password': None
            }
            return True

        # Header (centered)
        header_frame = tk.Frame(auth_window, bg=self.colores['primary'])
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="🔐 Credenciales de Acceso",
                 font=('Segoe UI', 14, 'bold'),
                 bg=self.colores['primary'],
                 fg='white').pack(pady=12)

        # Content (center everything)
        content_frame = tk.Frame(auth_window, bg=self.colores['bg'])
        content_frame.pack(expand=True)

        # Decidir qué campos mostrar
        show_domain = not has_ua_cred
        show_admin = not is_local_admin

        # --- Dominio (mostrar solo si no hay credencial almacenada) ---
        if show_domain:
            tk.Label(content_frame, text="Credenciales de Dominio",
                     font=('Segoe UI', 11, 'bold'),
                     bg=self.colores['bg'],
                     fg=self.colores['text_primary']).pack(pady=(6, 6))

            usuario_dominio_var = tk.StringVar(value='ua\\adm')
            usuario_dominio_entry = tk.Entry(content_frame, textvariable=usuario_dominio_var,
                                             font=('Segoe UI', 10), width=36, justify='center')
            usuario_dominio_entry.pack(pady=(0, 6))

            password_dominio_var = tk.StringVar()
            password_dominio_entry = tk.Entry(content_frame, textvariable=password_dominio_var,
                                              show='*', font=('Segoe UI', 10), width=36, justify='center')
            password_dominio_entry.pack(pady=(0, 8))

        # --- Separator visual ---
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=8)

        # --- Admin local ---
        # Siempre creamos la variable con el usuario actual, pero solo mostramos
        # los campos visuales si es necesario (show_admin == True).
        usuario_admin_var = tk.StringVar(value=self._get_current_whoami())
        if show_admin:
            tk.Label(content_frame, text="Credenciales de Administrador Local",
                     font=('Segoe UI', 11, 'bold'),
                     bg=self.colores['bg'],
                     fg=self.colores['text_primary']).pack(pady=(6, 6))

            usuario_admin_entry = tk.Entry(content_frame, textvariable=usuario_admin_var,
                                           font=('Segoe UI', 10), width=36, justify='center')
            usuario_admin_entry.pack(pady=(0, 6))

            password_admin_var = tk.StringVar()
            password_admin_entry = tk.Entry(content_frame, textvariable=password_admin_var,
                                             show='*', font=('Segoe UI', 10), width=36, justify='center')
            password_admin_entry.pack(pady=(0, 10))
        else:
            # No mostramos ningún control de admin (usuario local es admin)
            password_admin_var = tk.StringVar(value='')

        estado_label = tk.Label(content_frame, text="",
                                font=('Segoe UI', 9),
                                bg=self.colores['bg'],
                                fg='#f59e0b')
        estado_label.pack(pady=(0, 6))

        def conectar():
            # Dominio: si está visible, recoger y validar campos
            if show_domain:
                usuario_dominio = usuario_dominio_var.get()
                pwd_dominio = password_dominio_var.get()
                if not usuario_dominio or not pwd_dominio:
                    messagebox.showwarning("Advertencia", "Usuario y contraseña de dominio son requeridos")
                    return
                self.credenciales_dominio = {
                    'usuario': usuario_dominio,
                    'password': pwd_dominio
                }
            else:
                # Usar credencial almacenada del sistema para el dominio
                self.credenciales_dominio = None

            # Admin local: si está visible, validar contraseña; si no, asumimos usuario local admin
            usuario_admin = usuario_admin_var.get()
            if show_admin:
                pwd_admin = password_admin_var.get()
                if not usuario_admin or not pwd_admin:
                    messagebox.showwarning("Advertencia", "Usuario y contraseña de administrador son requeridos")
                    return

                # Validar credenciales de admin
                estado_label.config(text="⏳ Validando credenciales...", fg='#f59e0b')
                auth_window.update()

                if not self.validar_credenciales_admin(usuario_admin, pwd_admin):
                    estado_label.config(text="❌ Error: Credenciales de admin inválidas", fg='#ef4444')
                    messagebox.showerror("Error de Validación",
                                         "Las credenciales de administrador no son válidas o el usuario no existe.\n\n"
                                         "Verifica:\n"
                                         "- El nombre del equipo es correcto\n"
                                         "- La contraseña es correcta\n"
                                         "- El usuario tiene permisos de administrador")
                    return

                self.credenciales_admin = {
                    'usuario': usuario_admin,
                    'password': pwd_admin
                }
            else:
                # Usuario local ya es administrador: no pedimos contraseña
                self.credenciales_admin = {
                    'usuario': usuario_admin,
                    'password': None
                }

            auth_window.destroy()

        def cancelar():
            self.root.quit()

        # Buttons centered
        btn_frame = tk.Frame(content_frame, bg=self.colores['bg'])
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="Conectar", command=conectar,
                 font=('Segoe UI', 10, 'bold'),
                 bg=self.colores['primary'],
                 fg='white',
                 padx=20,
                 pady=6,
                 relief='flat',
                 cursor='hand2').pack(side=tk.LEFT, padx=8)

        tk.Button(btn_frame, text="Cancelar", command=cancelar,
                 font=('Segoe UI', 10),
                 bg=self.colores['border'],
                 fg=self.colores['text_primary'],
                 padx=20,
                 pady=6,
                 relief='flat',
                 cursor='hand2').pack(side=tk.LEFT, padx=8)

        # Esperar respuesta
        self.root.wait_window(auth_window)

        return self.credenciales_dominio and self.credenciales_admin
