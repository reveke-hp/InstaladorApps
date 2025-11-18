import os
import shutil
import subprocess
import logging
import json
from pathlib import Path

class InstalacionesEspeciales:
    def __init__(self, auth_manager):
        self.auth = auth_manager
        self.logger = logging.getLogger(__name__)
        self.config = self.cargar_configuracion()
    
    def cargar_configuracion(self):
        """Carga la configuración desde special_config.json"""
        try:
            config_path = Path("special_config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning("No se encontró special_config.json, creando uno por defecto")
                config_por_defecto = {
                    "instalaciones_especiales": {}
                }
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_por_defecto, f, indent=4, ensure_ascii=False)
                return config_por_defecto
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {str(e)}")
            return {"instalaciones_especiales": {}}
    
    def procesar_instalacion_especial(self, app_name, ruta_instalador):
        """Detecta y procesa instalaciones especiales basado en la configuración"""
        config_app = self.config["instalaciones_especiales"].get(app_name)
        
        if config_app:
            return self.ejecutar_instalacion_configurada(app_name, config_app)
        
        # También buscar por nombre parcial (case insensitive)
        for nombre_config, config in self.config["instalaciones_especiales"].items():
            if nombre_config.lower() in app_name.lower():
                return self.ejecutar_instalacion_configurada(app_name, config)
        
        # Si no es una instalación especial, retornar None para usar el flujo normal
        return None
    
    def ejecutar_instalacion_configurada(self, app_name, config):
        """Ejecuta una instalación basada en la configuración"""
        try:
            tipo = config.get("tipo", "copia_contenido")
            origen_base = Path(config.get("origen_base", ""))
            destino_base = Path(config.get("destino_base", ""))
            
            if not origen_base or not destino_base:
                return {
                    'exitoso': False,
                    'mensaje': f'Configuración incompleta para {app_name}',
                    'tipo': 'especial'
                }
            
            if not origen_base.exists():
                return {
                    'exitoso': False,
                    'mensaje': f'No se encuentra la ruta de origen: {origen_base}',
                    'tipo': 'especial'
                }
            
            # Crear carpeta destino si no existe
            destino_base.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Carpeta destino creada/verificada: {destino_base}")
            
            # Ejecutar según el tipo
            if tipo == "copia_carpetas":
                resultado = self.copiar_carpetas_especificas(origen_base, destino_base, config)
            elif tipo == "copia_contenido":
                resultado = self.copiar_contenido_completo(origen_base, destino_base)
            else:
                resultado = {
                    'exitoso': False,
                    'mensaje': f'Tipo de instalación no soportado: {tipo}',
                    'tipo': 'especial'
                }
            
            # Ejecutar archivos si están configurados
            if resultado['exitoso'] and config.get("archivos_a_ejecutar"):
                self.ejecutar_archivos_configurados(destino_base, config["archivos_a_ejecutar"])
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error en instalación configurada {app_name}: {str(e)}")
            return {
                'exitoso': False,
                'mensaje': f'Error en instalación {app_name}: {str(e)}',
                'tipo': 'especial'
            }
    
    def copiar_carpetas_especificas(self, origen_base, destino_base, config):
        """Copia solo las carpetas especificadas en la configuración"""
        try:
            carpetas_a_copiar = config.get("carpetas_a_copiar", [])
            
            if not carpetas_a_copiar:
                return {
                    'exitoso': False,
                    'mensaje': 'No hay carpetas configuradas para copiar',
                    'tipo': 'especial'
                }
            
            for carpeta in carpetas_a_copiar:
                origen_carpeta = origen_base / carpeta
                destino_carpeta = destino_base / carpeta
                
                if origen_carpeta.exists():
                    self.logger.info(f"Copiando {carpeta}...")
                    self.copiar_carpeta(origen_carpeta, destino_carpeta)
                else:
                    self.logger.warning(f"No se encontró: {origen_carpeta}")
            
            return {
                'exitoso': True,
                'mensaje': f'Instalación completada - {len(carpetas_a_copiar)} carpetas copiadas',
                'tipo': 'especial'
            }
            
        except Exception as e:
            self.logger.error(f"Error copiando carpetas específicas: {str(e)}")
            raise
    
    def copiar_contenido_completo(self, origen_base, destino_base):
        """Copia todo el contenido de la carpeta origen, SOBREESCRIBIENDO siempre"""
        try:
            self.logger.info(f"Copiando contenido completo de {origen_base}...")
            
            # Verificar que el origen tenga contenido
            if not any(origen_base.iterdir()):
                return {
                    'exitoso': False,
                    'mensaje': 'La carpeta de origen está vacía',
                    'tipo': 'especial'
                }
            
            # Copiar todos los archivos y subcarpetas SOBREESCRIBIENDO
            items_copiados = 0
            for item in origen_base.iterdir():
                destino_item = destino_base / item.name
                
                if item.is_dir():
                    # Para carpetas: eliminar si existe y copiar nueva
                    if destino_item.exists():
                        shutil.rmtree(destino_item)
                    shutil.copytree(item, destino_item)
                    items_copiados += 1
                else:
                    # Para archivos: siempre copiar (sobreescribe)
                    shutil.copy2(item, destino_item)
                    items_copiados += 1
                self.logger.info(f"✓ {'Sobreescrito' if destino_item.exists() else 'Copiado'}: {item.name}")
            
            return {
                'exitoso': True,
                'mensaje': f'Instalación completada - {items_copiados} elementos copiados/sobreescritos',
                'tipo': 'especial'
            }
            
        except Exception as e:
            self.logger.error(f"Error copiando contenido completo: {str(e)}")
            raise
    
    def ejecutar_archivos_configurados(self, base_path, archivos_a_ejecutar):
        """Ejecuta archivos específicos si están configurados"""
        for archivo_relativo in archivos_a_ejecutar:
            archivo_completo = base_path / archivo_relativo
            if archivo_completo.exists():
                try:
                    self.logger.info(f"Ejecutando: {archivo_completo}")
                    subprocess.run([str(archivo_completo)], check=True, timeout=300)
                    self.logger.info(f"✓ Ejecutado: {archivo_completo}")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Timeout en: {archivo_completo}")
                except Exception as e:
                    self.logger.error(f"Error ejecutando {archivo_completo}: {str(e)}")
            else:
                self.logger.warning(f"Archivo no encontrado: {archivo_completo}")
    
    def copiar_carpeta(self, origen, destino):
        """Copia una carpeta completa manteniendo estructura"""
        try:
            if destino.exists():
                shutil.rmtree(destino)
            shutil.copytree(origen, destino)
            self.logger.info(f"✓ Carpeta copiada: {origen.name}")
        except Exception as e:
            self.logger.error(f"Error copiando {origen}: {str(e)}")
            raise