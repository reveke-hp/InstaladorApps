import os
import subprocess

def filter_aplicaciones(aplicaciones, filtro):
    """Devuelve una lista de tuplas (nombre, ruta) filtradas por `filtro` (insensible a mayúsculas)."""
    if not aplicaciones:
        return []
    filtro = (filtro or '').strip().lower()
    resultado = []
    for nombre, ruta in aplicaciones.items():
        if not filtro:
            resultado.append((nombre, ruta))
        else:
            if filtro in nombre.lower() or filtro in (ruta or '').lower():
                resultado.append((nombre, ruta))
    return resultado

def obtener_parametros_silenciosos(ruta_instalador):
    """Devuelve parámetros ultra-silenciosos forzados"""
    nombre_archivo = os.path.basename(ruta_instalador).lower()
    
    # PARÁMETROS MÁS AGRESIVOS PARA FORZAR SILENCIO
    parametros_ultra_silenciosos = {
        # Navegadores
        'chrome': ['--silent', '--install', '--force', '--do-not-launch-chrome'],
        'googlechrome': ['--silent', '--install', '--force', '--do-not-launch-chrome'],
        'firefox': ['-ms', '-ma'],
        'brave': ['--silent', '--install', '--do-not-launch-brave'],
        'opera': ['/silent', '/install', '/launchopera=0'],
        
        # Suite Adobe
        'adobereader': ['/sAll', '/rs', '/rps', '/msi', '/quiet', '/norestart', '/suppressmsg'],
        'acrord': ['/sAll', '/rs', '/rps', '/msi', '/quiet', '/norestart', '/suppressmsg'],
        'acrobat': ['/sAll', '/rs', '/rps', '/msi', '/quiet', '/norestart', '/suppressmsg'],
        
        # Compresores
        'winrar': ['/S', '/D=C:\\Program Files\\WinRAR'],
        'rar': ['/S', '/D=C:\\Program Files\\WinRAR'],
        '7z': ['/S', '/D=C:\\Program Files\\7-Zip'],
        '7zip': ['/S', '/D=C:\\Program Files\\7-Zip'],
        
        # Multimedia
        'vlc': ['/S', '/quiet', '/norestart', '/no-run'],
        'codec': ['/S', '/quick', '/silent'],
        
        # Utilidades
        'notepad++': ['/S', '/D=C:\\Program Files\\Notepad++'],
        'python': ['/quiet', 'InstallAllUsers=1', 'PrependPath=1', 'Include_test=0', 'AssociateFiles=0', 'Shortcuts=0'],
        'java': ['INSTALL_SILENT=1', 'STATIC=0', 'WEB_JAVA=0', 'WEB_JAVA_SECURITY_LEVEL=H', 'AUTO_UPDATE=0'],
        
        # Comunicación
        'zoom': ['/quiet', '/norestart', '/nogoogle'],
        'teams': ['-s', '--disable-auto-start'],
        'discord': ['--silent', '--do-not-run'],
        
        # Office
        'office': ['/quiet', '/norestart', '/config', 'config.xml'],
        '365': ['/quiet', '/norestart', '/config', 'config.xml'],
        
        # Aplicaciones específicas
        'polichequeos': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
        'biocom': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
        'tablero': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
        'ergo': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
        'trii': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
        'vnc': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
        'openvpn': ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-'],
    }
    
    # Buscar parámetros específicos
    for clave, parametros in parametros_ultra_silenciosos.items():
        if clave in nombre_archivo:
            return [ruta_instalador] + parametros
    
    # PARÁMETROS POR DEFECTO SUPER AGRESIVOS
    parametros_por_defecto = [
        '/VERYSILENT',           # Muy silencioso
        '/SUPPRESSMSGBOXES',     # Suprimir todos los mensajes
        '/NORESTART',            # No reiniciar
        '/SP-',                  # No mostrar "este programa es confiable"
        '/NOCANCEL',             # No permitir cancelar
        '/CLOSEAPPLICATIONS',    # Cerrar aplicaciones si es necesario
        '/RESTARTAPPLICATIONS',  # Reiniciar aplicaciones después
        '/LOG',                  # Log para debugging
        '/ALLUSERS',             # Instalar para todos los usuarios
    ]
    
    return [ruta_instalador] + parametros_por_defecto

def preparar_instalacion_especifica(app_name, ruta):
    """Prepara la configuración de instalación forzando modo silencioso"""
    parametros = obtener_parametros_silenciosos(ruta)
    
    # Timeout más largo para instalaciones silenciosas
    timeout = 600  # 10 minutos
    
    return {
        'parametros': parametros,
        'timeout': timeout,
        'flags': subprocess.CREATE_NO_WINDOW  # Flag para NO crear ventana
    }

# Funciones de compatibilidad (mantener por si acaso)
def obtener_parametros_instalacion(ruta_instalador):
    """Determina parámetros básicos de instalación según el nombre del archivo."""
    return obtener_parametros_silenciosos(ruta_instalador)