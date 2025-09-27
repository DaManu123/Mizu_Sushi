import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import datetime
import json
import os
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False
    print("PIL no disponible. La imagen de fondo no se cargará.")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False
    print("ReportLab no disponible. La exportación PDF no estará disponible.")

# --- Configuración Inicial y Estilos ---
# Cambia esta línea para probar los diferentes roles: "cliente", "cajero", "admin"
ROL_ACTUAL = "cliente"

# Esquemas de colores para diferentes temas
TEMAS = {
    "Claro": {
        "COLOR_FONDO": "#F5F5DC",           # Beige claro (arroz)
        "COLOR_TITULO": "#D32F2F",          # Rojo atún
        "COLOR_TEXTO": "#212121",           # Negro texto
        "COLOR_BOTON_FONDO": "#424242",     # Gris oscuro
        "COLOR_BOTON_TEXTO": "#FFFFFF",     # Blanco
        "COLOR_SECUNDARIO": "#4CAF50",      # Verde
        "COLOR_ALERTA": "#FF5722",          # Naranja rojizo
        "COLOR_INFO": "#2196F3",            # Azul
        "TRANSPARENCIA_FONDO": 0.15,        # 15% opacidad
        
        # Colores específicos para componentes TTK
        "COLOR_ENTRY_FONDO": "#FFFFFF",     # Blanco para entradas
        "COLOR_ENTRY_TEXTO": "#212121",     # Negro para texto de entradas
        "COLOR_TABLA_FONDO": "#FFFFFF",     # Blanco para filas de tabla
        "COLOR_TABLA_TEXTO": "#212121",     # Negro para texto de tabla
        "COLOR_TABLA_HEADER": "#2E7D32",    # Verde oscuro para encabezados
        "COLOR_TABLA_HEADER_TEXTO": "#FFFFFF", # Blanco para texto de encabezados
        "COLOR_TABLA_SELECCION": "#FFCDD2", # Rosa claro para selección
        "COLOR_FRAME_BORDER": "#CCCCCC",    # Gris claro para bordes
        "COLOR_SUBTITULO": "#2E7D32"        # Verde para subtítulos
    },
    "Oscuro": {
        "COLOR_FONDO": "#2B2B2B",           # Gris oscuro más suave
        "COLOR_TITULO": "#FF8A80",          # Rojo coral claro
        "COLOR_TEXTO": "#E8E8E8",           # Gris muy claro
        "COLOR_BOTON_FONDO": "#404040",     # Gris medio
        "COLOR_BOTON_TEXTO": "#FFFFFF",     # Blanco
        "COLOR_SECUNDARIO": "#81C784",      # Verde claro
        "COLOR_ALERTA": "#FFAB91",          # Naranja suave
        "COLOR_INFO": "#64B5F6",            # Azul claro
        "TRANSPARENCIA_FONDO": 0.30,        # 30% opacidad para mejor contraste
        
        # Colores específicos para componentes TTK
        "COLOR_ENTRY_FONDO": "#3C3C3C",     # Gris medio para entradas
        "COLOR_ENTRY_TEXTO": "#E8E8E8",     # Gris claro para texto de entradas
        "COLOR_TABLA_FONDO": "#353535",     # Gris medio para filas de tabla
        "COLOR_TABLA_TEXTO": "#E8E8E8",     # Gris claro para texto de tabla
        "COLOR_TABLA_HEADER": "#4A4A4A",    # Gris más oscuro para encabezados
        "COLOR_TABLA_HEADER_TEXTO": "#FFFFFF", # Blanco para texto de encabezados
        "COLOR_TABLA_SELECCION": "#5C5C5C", # Gris medio para selección
        "COLOR_FRAME_BORDER": "#555555",    # Gris medio para bordes
        "COLOR_SUBTITULO": "#81C784"        # Verde claro para subtítulos
    },
    "Automatico": {}  # Se llena dinámicamente según la hora
}

# Variables globales del tema actual
TEMA_ACTUAL = "Claro"

# Clase principal de la aplicación
class SushiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Inicializar variables de tema y colores PRIMERO
        self.tema_actual = tk.StringVar(value="Claro")
        self.aplicar_tema("Claro")  # Inicializar todos los colores
        
        self.title("Mizu Sushi Bar 🍣")
        self.geometry("900x750")  # Tamaño inicial más grande
        self.minsize(800, 600)    # Tamaño mínimo
        self.configure(bg=self.color_fondo_ventana)
        
        # Hacer la ventana redimensionable
        self.resizable(True, True)
        
        # Variables para grid responsive
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.rol_usuario = tk.StringVar(value=ROL_ACTUAL)
        self.fondo_imagen = None
        
        # Estructura de datos para ofertas
        self.ofertas = [
            {
                "id": "OFF001",
                "nombre": "2x1 en California Rolls",
                "descripcion": "Lleva 2 California Rolls por el precio de 1",
                "tipo": "2x1",
                "productos_aplicables": ["California Roll"],
                "descuento": 50,  # 50% descuento = 2x1
                "activa": True,
                "fecha_inicio": "2025-09-26",
                "fecha_fin": "2025-10-15"
            },
            {
                "id": "OFF002", 
                "nombre": "Combo Sushi Lovers",
                "descripcion": "15% descuento en pedidos de 3 o más rolls",
                "tipo": "combo",
                "productos_aplicables": ["California Roll", "Philadelphia Roll", "Salmon Roll"],
                "descuento": 15,
                "cantidad_minima": 3,
                "activa": True,
                "fecha_inicio": "2025-09-20",
                "fecha_fin": "2025-10-31"
            },
            {
                "id": "OFF003",
                "nombre": "Viernes de Descuento",
                "descripcion": "20% de descuento todos los viernes",
                "tipo": "descuento_dia",
                "productos_aplicables": ["todos"],
                "descuento": 20,
                "dia_semana": "viernes",
                "activa": True,
                "fecha_inicio": "2025-09-01",
                "fecha_fin": "2025-12-31"
            }
        ]
        
        # Sistema de ventas para reportes avanzados
        self.ventas = [
            {
                "id": "VTA001",
                "fecha": "2025-09-25 14:30:00",
                "productos": [
                    {"nombre": "California Roll", "cantidad": 2, "precio_unitario": 120, "subtotal": 240}
                ],
                "oferta_aplicada": "OFF001",
                "descuento_aplicado": 120,  # 50% de 240
                "total_sin_descuento": 240,
                "total_final": 120,
                "metodo_pago": "efectivo",
                "cajero": "Ana Gomez"
            },
            {
                "id": "VTA002",
                "fecha": "2025-09-25 16:45:00",
                "productos": [
                    {"nombre": "Philadelphia Roll", "cantidad": 1, "precio_unitario": 150, "subtotal": 150},
                    {"nombre": "Salmon Roll", "cantidad": 2, "precio_unitario": 180, "subtotal": 360}
                ],
                "oferta_aplicada": None,
                "descuento_aplicado": 0,
                "total_sin_descuento": 510,
                "total_final": 510,
                "metodo_pago": "tarjeta",
                "cajero": "Carlos Ruiz"
            },
            {
                "id": "VTA003",
                "fecha": "2025-09-26 12:15:00",
                "productos": [
                    {"nombre": "California Roll", "cantidad": 3, "precio_unitario": 120, "subtotal": 360},
                    {"nombre": "Tuna Roll", "cantidad": 1, "precio_unitario": 200, "subtotal": 200}
                ],
                "oferta_aplicada": "OFF002",
                "descuento_aplicado": 84,  # 15% de 560
                "total_sin_descuento": 560,
                "total_final": 476,
                "metodo_pago": "efectivo",
                "cajero": "Ana Gomez"
            },
            {
                "id": "VTA004",
                "fecha": "2025-09-26 18:20:00",
                "productos": [
                    {"nombre": "Veggie Roll", "cantidad": 2, "precio_unitario": 100, "subtotal": 200},
                    {"nombre": "Philadelphia Roll", "cantidad": 1, "precio_unitario": 150, "subtotal": 150}
                ],
                "oferta_aplicada": None,
                "descuento_aplicado": 0,
                "total_sin_descuento": 350,
                "total_final": 350,
                "metodo_pago": "tarjeta",
                "cajero": "Maria Lopez"
            }
        ]
        
        self.cargar_imagen_fondo()
        self.configurar_estilos()
        
        # Inicializar tema por defecto
        self.aplicar_tema("Claro")
        
        # Inicializar timer para tema automático
        self.verificar_tema_automatico()
        
        # Atajos de teclado para cambio rápido de roles
        self.bind('<F1>', lambda e: self.cambiar_rol_directo("cliente"))
        self.bind('<F2>', lambda e: self.cambiar_rol_directo("cajero"))
        self.bind('<F3>', lambda e: self.cambiar_rol_directo("admin"))
        self.bind('<Control-r>', lambda e: self.mostrar_selector_roles())
        
        # Atajos de teclado para cambio rápido de temas (para pruebas)
        self.bind('<F9>', lambda e: self.aplicar_tema("Claro"))
        self.bind('<F10>', lambda e: self.aplicar_tema("Oscuro"))
        self.bind('<F11>', lambda e: self.aplicar_tema("Automatico"))
        
        # Configurar evento de redimensionamiento para botones responsivos
        self.bind('<Configure>', self.on_window_resize)
        
        self.mostrar_login()
    
    def cambiar_rol_directo(self, rol):
        """Cambia el rol directamente y actualiza la vista"""
        self.rol_usuario.set(rol)
        # Mostrar notificación temporal
        self.mostrar_notificacion_rol(rol)
        self.mostrar_menu_principal()
    
    def mostrar_notificacion_rol(self, rol):
        """Muestra una notificación temporal del cambio de rol"""
        notificacion = tk.Toplevel(self)
        notificacion.title("Rol Cambiado")
        notificacion.geometry("300x100")
        notificacion.configure(bg="#4CAF50")
        notificacion.resizable(False, False)
        
        # Posicionar en la esquina superior derecha
        notificacion.geometry("+{}+{}".format(self.winfo_x() + 500, self.winfo_y() + 50))
        notificacion.overrideredirect(True)  # Sin bordes de ventana
        
        # Contenido de la notificación
        tk.Label(notificacion, text=f"✅ Rol cambiado a:", 
                font=("Helvetica", 10, "bold"), bg="#4CAF50", fg="white").pack(pady=(15, 5))
        tk.Label(notificacion, text=f"{rol.upper()}", 
                font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white").pack()
        
        # Cerrar automáticamente después de 2 segundos
        notificacion.after(2000, notificacion.destroy)
    
    def calcular_tamaños_responsivos(self):
        """Calcula tamaños responsivos basados en el tamaño actual de la ventana"""
        width = self.winfo_width() if self.winfo_width() > 1 else 900
        height = self.winfo_height() if self.winfo_height() > 1 else 750
        
        # Categorizar el tamaño de ventana
        if width >= 1200:
            # Ventana grande
            return {
                'boton_width': 35,
                'boton_font_size': 12,
                'boton_padx': 25,
                'boton_pady': 12,
                'boton_gestion_width': 18,
                'boton_gestion_padx': 15,
                'boton_gestion_pady': 8,
                'boton_gestion_font': 11,
                'espaciado_botones': 8
            }
        elif width >= 1000:
            # Ventana mediana
            return {
                'boton_width': 30,
                'boton_font_size': 11,
                'boton_padx': 20,
                'boton_pady': 10,
                'boton_gestion_width': 16,
                'boton_gestion_padx': 12,
                'boton_gestion_pady': 6,
                'boton_gestion_font': 10,
                'espaciado_botones': 6
            }
        elif width >= 800:
            # Ventana normal
            return {
                'boton_width': 28,
                'boton_font_size': 11,
                'boton_padx': 18,
                'boton_pady': 8,
                'boton_gestion_width': 14,
                'boton_gestion_padx': 10,
                'boton_gestion_pady': 5,
                'boton_gestion_font': 10,
                'espaciado_botones': 5
            }
        else:
            # Ventana pequeña
            return {
                'boton_width': 25,
                'boton_font_size': 10,
                'boton_padx': 15,
                'boton_pady': 6,
                'boton_gestion_width': 12,
                'boton_gestion_padx': 8,
                'boton_gestion_pady': 4,
                'boton_gestion_font': 9,
                'espaciado_botones': 4
            }
    
    def on_window_resize(self, event):
        """Maneja eventos de redimensionamiento de ventana para ajustar botones"""
        # Solo procesar eventos de la ventana principal, no de widgets internos
        if event.widget == self:
            # Pequeña pausa para evitar múltiples llamadas rápidas
            if hasattr(self, '_resize_after_id'):
                self.after_cancel(self._resize_after_id)
            self._resize_after_id = self.after(100, self._ajustar_interfaz_responsiva)
    
    def _ajustar_interfaz_responsiva(self):
        """Reajusta la interfaz cuando cambia el tamaño de la ventana"""
        try:
            # Solo recargar si estamos en el menú principal para evitar conflictos
            current_view = getattr(self, '_current_view', None)
            if current_view == 'menu_principal':
                self.mostrar_menu_principal()
        except:
            # Silenciar errores para evitar problemas durante redimensionamiento
            pass
    
    def obtener_tema_automatico(self):
        """Determina el tema según la hora del día"""
        import datetime
        hora_actual = datetime.datetime.now().hour
        
        # 6:00 AM - 6:00 PM = Claro, 6:00 PM - 6:00 AM = Oscuro  
        if 6 <= hora_actual < 18:
            return "Claro"
        else:
            return "Oscuro"
    
    def aplicar_tema(self, nombre_tema):
        """Aplica un tema específico a la aplicación"""
        global TEMA_ACTUAL
        
        # Determinar el tema a aplicar
        if nombre_tema == "Automatico":
            tema_efectivo = self.obtener_tema_automatico()
        else:
            tema_efectivo = nombre_tema
        
        # Aplicar todos los colores del tema
        tema_colores = TEMAS[tema_efectivo]
        self.color_fondo_ventana = tema_colores["COLOR_FONDO"]
        self.color_titulo = tema_colores["COLOR_TITULO"] 
        self.color_texto = tema_colores["COLOR_TEXTO"]
        self.color_boton_fondo = tema_colores["COLOR_BOTON_FONDO"]
        self.color_boton_texto = tema_colores["COLOR_BOTON_TEXTO"]
        
        # Aplicar colores específicos de componentes
        self.color_entry_fondo = tema_colores["COLOR_ENTRY_FONDO"]
        self.color_entry_texto = tema_colores["COLOR_ENTRY_TEXTO"]
        self.color_tabla_fondo = tema_colores["COLOR_TABLA_FONDO"]
        self.color_tabla_texto = tema_colores["COLOR_TABLA_TEXTO"]
        self.color_tabla_header = tema_colores["COLOR_TABLA_HEADER"]
        self.color_tabla_header_TEXTO = tema_colores["COLOR_TABLA_HEADER_TEXTO"]
        self.color_tabla_seleccion = tema_colores["COLOR_TABLA_SELECCION"]
        self.color_subtitulo = tema_colores["COLOR_SUBTITULO"]
        
        TEMA_ACTUAL = nombre_tema
        
        # Actualizar la variable de tema actual
        self.tema_actual.set(nombre_tema)
        
        # Actualizar el color de fondo de la ventana principal
        self.configure(bg=self.color_fondo_ventana)
        
        # Reconfigurar estilos con nuevos colores
        self.configurar_estilos()
        
        # Actualizar fondo con nueva transparencia si es necesario
        if hasattr(self, 'imagen_original') and self.imagen_original:
            self.actualizar_imagen_fondo_con_tema(tema_colores.get("TRANSPARENCIA_FONDO", 0.15))
        
        # Refrescar la pantalla actual para mostrar los cambios
        self.after(100, self.refrescar_pantalla_actual)
    
    def refrescar_pantalla_actual(self):
        """Refresca la pantalla actual aplicando los nuevos colores del tema"""
        try:
            # Actualizar el color de fondo de todos los widgets recursivamente
            self._actualizar_colores_recursivo(self)
        except Exception as e:
            print(f"Error al refrescar pantalla: {e}")
    
    def _actualizar_colores_recursivo(self, widget):
        """Actualiza los colores de un widget y sus hijos recursivamente"""
        try:
            # Si el widget tiene configuración de fondo y usa self.color_fondo_ventana, actualizarlo
            if hasattr(widget, 'configure'):
                try:
                    # Verificar si usa el color de fondo del tema
                    current_bg = widget.cget('bg')
                    if current_bg in ['#F5F5DC', '#2B2B2B', '#1E1E1E']:  # Colores de tema anteriores
                        widget.configure(bg=self.color_fondo_ventana)
                    
                    # Actualizar colores de texto si usa colores de tema
                    if hasattr(widget, 'cget') and 'fg' in widget.keys():
                        current_fg = widget.cget('fg')
                        # Actualizar algunos colores específicos conocidos
                        if current_fg in ['#212121', '#E0E0E0', '#E8E8E8']:
                            widget.configure(fg=self.color_texto)
                        elif current_fg in ['#D32F2F', '#FF6B6B', '#FF8A80']:
                            widget.configure(fg=self.color_titulo)
                except:
                    pass
            
            # Continuar recursivamente con los hijos
            for child in widget.winfo_children():
                self._actualizar_colores_recursivo(child)
        except:
            pass
    
    def actualizar_imagen_fondo_con_tema(self, transparencia):
        """Actualiza la imagen de fondo con la transparencia del tema actual"""
        if self.imagen_original:
            try:
                width = self.winfo_width() if self.winfo_width() > 1 else 900
                height = self.winfo_height() if self.winfo_height() > 1 else 750
                
                self.fondo_imagen_anterior = self.fondo_imagen
                
                img = self.imagen_original.resize((width, height), Image.Resampling.LANCZOS)
                img = img.convert("RGBA")
                alpha = img.split()[-1]
                alpha = alpha.point(lambda p: p * transparencia)
                img.putalpha(alpha)
                self.fondo_imagen = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error al actualizar imagen de fondo con tema: {e}")
    
    def obtener_colores_tema(self, nombre_tema):
        """Obtiene los colores de un tema específico para preview"""
        if nombre_tema == "Automatico":
            tema_efectivo = self.obtener_tema_automatico()
        else:
            tema_efectivo = nombre_tema
        return TEMAS[tema_efectivo]
    
    def verificar_tema_automatico(self):
        """Verifica y actualiza el tema automático cada 30 minutos"""
        if hasattr(self, 'tema_actual') and self.tema_actual.get() == "Automatico":
            tema_necesario = self.obtener_tema_automatico()
            # Obtener el tema que está aplicado actualmente
            tema_aplicado_actual = "Claro" if TEMA_ACTUAL in ["Claro", "Automatico"] and self.color_fondo_ventana == TEMAS["Claro"]["COLOR_FONDO"] else "Oscuro"
            
            # Solo cambiar si es necesario
            if tema_necesario != tema_aplicado_actual:
                self.aplicar_tema("Automatico")
                print(f"Tema automático actualizado a: {tema_necesario}")
        
        # Programar la próxima verificación en 30 minutos (1800000 ms)
        self.after(1800000, self.verificar_tema_automatico)

    def mostrar_selector_roles(self):
        """Ventana modal para seleccionar rol rápidamente"""
        ventana_roles = tk.Toplevel(self)
        ventana_roles.title("Seleccionar Rol")
        ventana_roles.geometry("400x300")
        ventana_roles.configure(bg=self.color_fondo_ventana)
        ventana_roles.resizable(False, False)
        
        # Centrar la ventana
        ventana_roles.transient(self)
        ventana_roles.grab_set()
        
        # Título
        tk.Label(ventana_roles, text="🔄 Seleccionar Rol", 
                font=("Helvetica", 18, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=20)
        
        tk.Label(ventana_roles, text="Selecciona el rol con el que quieres acceder:", 
                font=("Helvetica", 12), bg=self.color_fondo_ventana, fg=self.color_texto).pack(pady=(0, 30))
        
        # Frame para botones de roles
        botones_frame = tk.Frame(ventana_roles, bg=self.color_fondo_ventana)
        botones_frame.pack(pady=20)
        
        def seleccionar_y_cerrar(rol):
            self.rol_usuario.set(rol)
            ventana_roles.destroy()
            self.mostrar_menu_principal()
        
        # Botones de roles con descripciones
        roles_info = [
            ("cliente", "👤 CLIENTE", "#4CAF50", "Ver menú, hacer pedidos, ofertas"),
            ("cajero", "💰 CAJERO", "#FF9800", "Registrar pedidos, cobrar, facturar"),
            ("admin", "⚙️ ADMINISTRADOR", "#9C27B0", "Gestión completa del sistema")
        ]
        
        for rol, texto, color, descripcion in roles_info:
            frame_rol = tk.Frame(botones_frame, bg=self.color_fondo_ventana)
            frame_rol.pack(pady=8)
            
            tk.Button(frame_rol, text=texto, 
                     command=lambda r=rol: seleccionar_y_cerrar(r),
                     bg=color, fg="white", font=("Helvetica", 12, "bold"),
                     relief="raised", bd=2, padx=20, pady=8, width=20).pack()
            
            tk.Label(frame_rol, text=descripcion, 
                    font=("Helvetica", 9), bg=self.color_fondo_ventana, fg="#666666").pack()
        
        # Botón cancelar
        tk.Button(ventana_roles, text="❌ Cancelar", command=ventana_roles.destroy,
                 bg="#9E9E9E", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=6).pack(pady=20)

    def cargar_imagen_fondo(self):
        """Carga la imagen de fondo adaptable al tamaño de ventana"""
        if PIL_DISPONIBLE:
            try:
                # Guardar imagen original para redimensionar dinámicamente
                self.imagen_original = Image.open("fondo_interfaz.png")
                self.actualizar_imagen_fondo()
                # Vincular evento de redimensionamiento
                self.bind('<Configure>', self.on_window_resize)
            except Exception as e:
                print(f"Error al cargar imagen de fondo: {e}")
                self.fondo_imagen = None
                self.imagen_original = None
        else:
            self.fondo_imagen = None
            self.imagen_original = None
    
    def on_window_resize(self, event):
        """Maneja el redimensionamiento de la ventana"""
        # Solo actualizar si el evento es de la ventana principal y tiene tamaño válido
        if event.widget == self and event.width > 100 and event.height > 100:
            self.after_idle(self.actualizar_imagen_fondo)
            # Refrescar la pantalla actual después de actualizar el fondo
            self.after(100, self.refrescar_fondo_pantalla_actual)
    
    def refrescar_fondo_pantalla_actual(self):
        """Refresca el fondo en la pantalla actual"""
        try:
            # Buscar todos los labels con imagen de fondo y actualizarlos
            for widget in self.winfo_children():
                self._actualizar_fondo_recursivo(widget)
        except Exception as e:
            print(f"Error al refrescar fondo: {e}")
    
    def _actualizar_fondo_recursivo(self, widget):
        """Actualiza el fondo recursivamente en todos los widgets"""
        try:
            # Si es un frame principal con fondo_label, actualizarlo
            if hasattr(widget, 'fondo_label') and self.fondo_imagen:
                widget.fondo_label.configure(image=self.fondo_imagen)
                widget.fondo_label.image = self.fondo_imagen
                widget.fondo_label.lower()
            
            # Continuar recursivamente con los hijos
            for child in widget.winfo_children():
                self._actualizar_fondo_recursivo(child)
        except Exception as e:
            pass
    
    def actualizar_imagen_fondo(self):
        """Actualiza la imagen de fondo según el tamaño actual de la ventana"""
        if self.imagen_original:
            try:
                # Obtener tamaño actual de la ventana
                width = self.winfo_width() if self.winfo_width() > 1 else 900
                height = self.winfo_height() if self.winfo_height() > 1 else 750
                
                # Guardar referencia anterior para comparación
                self.fondo_imagen_anterior = self.fondo_imagen
                
                # Obtener transparencia según el tema actual
                if hasattr(self, 'tema_actual'):
                    tema_efectivo = self.tema_actual.get()
                    if tema_efectivo == "Automatico":
                        tema_efectivo = self.obtener_tema_automatico()
                    transparencia = TEMAS[tema_efectivo].get("TRANSPARENCIA_FONDO", 0.15)
                else:
                    transparencia = 0.15
                
                # Redimensionar imagen
                img = self.imagen_original.resize((width, height), Image.Resampling.LANCZOS)
                img = img.convert("RGBA")
                # Hacer la imagen más transparente para que sea un fondo sutil
                alpha = img.split()[-1]
                alpha = alpha.point(lambda p: p * transparencia)
                img.putalpha(alpha)
                self.fondo_imagen = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error al actualizar imagen de fondo: {e}")

    def configurar_fondo(self, parent):
        """Configura el fondo con imagen para cualquier widget parent"""
        if self.fondo_imagen:
            # Crear label para la imagen de fondo
            fondo_label = tk.Label(parent, image=self.fondo_imagen, bg=self.color_fondo_ventana)
            fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
            # Asegurar que esté en el fondo
            fondo_label.lower()
            return fondo_label
        return None

    def configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Estilos generales con colores dinámicos del tema actual
        style.configure("TFrame", 
                       background=self.color_fondo_ventana, 
                       relief="flat", 
                       borderwidth=0)
        
        style.configure("TLabel", 
                       background=self.color_fondo_ventana, 
                       foreground=self.color_texto, 
                       font=("Helvetica", 11))
        
        style.configure("Titulo.TLabel", 
                       background=self.color_fondo_ventana, 
                       foreground=self.color_titulo, 
                       font=("Impact", 32, "bold"))
        
        style.configure("Subtitulo.TLabel", 
                       background=self.color_fondo_ventana, 
                       foreground=self.color_subtitulo, 
                       font=("Helvetica", 13, "bold"))

        # Botones con colores dinámicos
        style.configure(
            "TButton",
            background=self.color_boton_fondo,
            foreground=self.color_boton_texto,
            font=("Helvetica", 12, "bold"),
            padding=(15, 8),
            borderwidth=1,
            relief="raised"
        )
        style.map("TButton", 
                 background=[("active", self.color_subtitulo), ("pressed", self.color_subtitulo)],
                 relief=[("pressed", "sunken"), ("active", "raised")])

        # Entradas con colores dinámicos del tema
        style.configure("TEntry", 
                       fieldbackground=self.color_entry_fondo, 
                       foreground=self.color_entry_texto, 
                       font=("Helvetica", 11),
                       borderwidth=2,
                       relief="solid",
                       insertcolor=self.color_texto)  # Color del cursor

        # Tablas con colores dinámicos completos
        style.configure("Treeview",
                        rowheight=30,
                        background=self.color_tabla_fondo,
                        fieldbackground=self.color_tabla_fondo, 
                        foreground=self.color_tabla_texto,
                        font=("Helvetica", 10),
                        borderwidth=2,
                        relief="solid"
                        )
        
        # Configurar selección y focus de tabla
        style.map("Treeview", 
                 background=[("selected", self.color_tabla_seleccion)],
                 foreground=[("selected", self.color_tabla_texto)])
        
        # Encabezados de tabla con colores dinámicos
        style.configure("Treeview.Heading",
                        background=self.color_tabla_header,
                        foreground=self.color_tabla_header_TEXTO,
                        font=("Helvetica", 11, "bold"),
                        relief="raised",
                        borderwidth=1
                        )
        
        # Hover effect en encabezados
        style.map("Treeview.Heading",
                 background=[("active", self.color_subtitulo)])

        # Radiobuttons y Checkbuttons con colores dinámicos
        style.configure("TRadiobutton", 
                       background=self.color_fondo_ventana, 
                       foreground=self.color_texto, 
                       font=("Helvetica", 11),
                       focuscolor=self.color_subtitulo)
        
        style.configure("TCheckbutton", 
                       background=self.color_fondo_ventana, 
                       foreground=self.color_texto, 
                       font=("Helvetica", 11),
                       focuscolor=self.color_subtitulo)
        
        # Scrollbars con colores del tema
        style.configure("Vertical.TScrollbar",
                       background=self.color_tabla_header,
                       troughcolor=self.color_fondo_ventana,
                       arrowcolor=self.color_tabla_header_TEXTO,
                       borderwidth=1)
        
        # Combobox con colores del tema
        style.configure("TCombobox",
                       fieldbackground=self.color_entry_fondo,
                       background=self.color_boton_fondo,
                       foreground=self.color_entry_texto,
                       arrowcolor=self.color_texto,
                       borderwidth=2,
                       relief="solid")
        
        # Progressbar con colores del tema
        style.configure("TProgressbar",
                       background=self.color_subtitulo,
                       troughcolor=self.color_fondo_ventana,
                       borderwidth=1,
                       relief="solid")

    def limpiar_ventana(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Actualizar el fondo antes de configurarlo
        self.actualizar_imagen_fondo()
        
        # Configurar fondo con imagen primero
        self.configurar_fondo(self)

        # Crear frame principal con fondo transparente para mantener la imagen visible
        main_frame = tk.Frame(self, bg=self.color_fondo_ventana, highlightthickness=0)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Configurar grid para responsividad
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Configurar fondo también en el frame principal si es necesario
        if self.fondo_imagen:
            fondo_label = tk.Label(main_frame, image=self.fondo_imagen, bg=self.color_fondo_ventana)
            fondo_label.place(x=-20, y=-20, relwidth=1.05, relheight=1.05)
            # Asegurar que el fondo esté en el fondo
            fondo_label.lower()
            # Guardar referencia para poder actualizarlo después
            main_frame.fondo_label = fondo_label

        return main_frame

    # --- 1. Pantalla de Inicio de Sesión ---
    def mostrar_login(self):
        frame = self.limpiar_ventana()

        # Frame principal centrado con fondo semi-opaco más sutil
        login_container = tk.Frame(frame, bg=self.color_fondo_ventana, relief="flat", bd=1, highlightthickness=0)
        login_container.place(relx=0.5, rely=0.5, anchor="center")

        # Frame interno con fondo más transparente
        login_frame = tk.Frame(login_container, bg=self.color_fondo_ventana)
        login_frame.pack(padx=40, pady=30)

        # Título con estilo mejorado
        titulo_label = tk.Label(login_frame, text="🍣 MIZU SUSHI BAR 🍣", 
                               font=("Impact", 28, "bold"), 
                               bg=self.color_fondo_ventana, fg=self.color_titulo)
        titulo_label.pack(pady=(0, 20))

        # --- SELECTOR RÁPIDO DE ROLES ---
        roles_frame = tk.Frame(login_frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        roles_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(roles_frame, text="🚀 ACCESO RÁPIDO - Selecciona tu rol:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg="#2E7D32").pack(pady=(10, 5))
        
        botones_roles_frame = tk.Frame(roles_frame, bg=self.color_fondo_ventana)
        botones_roles_frame.pack(pady=(5, 15))
        
        def cambiar_rol_y_acceder(nuevo_rol):
            self.rol_usuario.set(nuevo_rol)
            self.mostrar_menu_principal()
        
        # Botones de acceso rápido
        tk.Button(botones_roles_frame, text="👤 CLIENTE", 
                 command=lambda: cambiar_rol_y_acceder("cliente"),
                 bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=12).pack(side="left", padx=5)
        
        tk.Button(botones_roles_frame, text="💰 CAJERO", 
                 command=lambda: cambiar_rol_y_acceder("cajero"),
                 bg="#FF9800", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=12).pack(side="left", padx=5)
        
        tk.Button(botones_roles_frame, text="⚙️ ADMIN", 
                 command=lambda: cambiar_rol_y_acceder("admin"),
                 bg="#9C27B0", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=12).pack(side="left", padx=5)
        
        # Separador visual
        tk.Label(login_frame, text="━━━ O ingresa manualmente ━━━", 
                font=("Helvetica", 10), bg=self.color_fondo_ventana, fg="#666666").pack(pady=15)

        # Campos de entrada con mejor estilo y fondo más claro
        tk.Label(login_frame, text="Usuario (nombre de usuario / correo)", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).pack(pady=(10, 5))
        entry_usuario = tk.Entry(login_frame, width=35, font=("Helvetica", 11), 
                                relief="solid", bd=2, bg="#FFFFFF", fg=self.color_texto)
        entry_usuario.pack(pady=(0, 15))

        tk.Label(login_frame, text="Contraseña", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).pack(pady=(5, 5))
        entry_password = tk.Entry(login_frame, show="*", width=35, font=("Helvetica", 11),
                                 relief="solid", bd=2, bg="#FFFFFF", fg=self.color_texto)
        entry_password.pack(pady=(0, 20))

        # Botones con mejor estilo y semi-transparencia
        tk.Button(login_frame, text="🔓 Iniciar Sesión", command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, font=("Helvetica", 12, "bold"),
                 relief="raised", bd=2, padx=20, pady=8, activebackground="#555555").pack(pady=5)
        tk.Button(login_frame, text="❌ Salir", command=self.quit,
                 bg="#D32F2F", fg="white", font=("Helvetica", 12, "bold"),
                 relief="raised", bd=2, padx=20, pady=8, activebackground="#B71C1C").pack(pady=5)
        
        # Información de atajos de teclado
        tk.Label(login_frame, text="━━━ Atajos de Teclado ━━━", 
                font=("Helvetica", 9), bg=self.color_fondo_ventana, fg="#888888").pack(pady=(20, 5))
        
        atajos_frame = tk.Frame(login_frame, bg=self.color_fondo_ventana)
        atajos_frame.pack()
        
        atajos_texto = """F1: Cliente  |  F2: Cajero  |  F3: Admin
F9: Tema Claro  |  F10: Tema Oscuro  |  F11: Automático
Ctrl+R: Selector de Roles"""
        
        tk.Label(atajos_frame, text=atajos_texto, 
                font=("Courier", 8), bg=self.color_fondo_ventana, fg="#666666", 
                justify="center").pack()

    # --- 2. Menú Principal (dependiendo del rol) ---
    def mostrar_menu_principal(self):
        self._current_view = 'menu_principal'  # Rastrear vista actual para responsive
        frame = self.limpiar_ventana()
        rol = self.rol_usuario.get().capitalize()

        # Título con fondo de color
        titulo_frame = tk.Frame(frame, bg=self.color_titulo, relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 30))
        tk.Label(titulo_frame, text=f"🍣 Menú Principal ({rol}) 🍣", 
                font=("Impact", 24, "bold"), bg=self.color_titulo, fg="white", 
                pady=15).pack()

        # Contenedor para botones con fondo semi-transparente más sutil
        menu_container = tk.Frame(frame, bg=self.color_fondo_ventana, relief="flat", bd=0, highlightthickness=0)
        menu_container.pack(pady=20, padx=50)

        botones_frame = tk.Frame(menu_container, bg=self.color_fondo_ventana)
        botones_frame.pack(padx=30, pady=30)

        # Obtener tamaños responsivos
        tamaños = self.calcular_tamaños_responsivos()

        def crear_boton_menu(texto, comando, color_bg=self.color_boton_fondo):
            return tk.Button(botones_frame, text=texto, command=comando,
                           bg=color_bg, fg=self.color_boton_texto, 
                           font=("Helvetica", tamaños['boton_font_size'], "bold"),
                           relief="raised", bd=2, 
                           padx=tamaños['boton_padx'], pady=tamaños['boton_pady'],
                           width=tamaños['boton_width'])

        if self.rol_usuario.get() == "cliente":
            crear_boton_menu("🍣 Menú de Sushi", self.mostrar_menu_sushi).pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("🎁 Ofertas Especiales", self.mostrar_ofertas_cliente, "#FF6F00").pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("🛒 Carrito de Compras", self.mostrar_carrito).pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("📦 Realizar Pedido", self.mostrar_realizar_pedido).pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("📜 Historial de Pedidos", self.mostrar_historial).pack(pady=tamaños['espaciado_botones'])

        elif self.rol_usuario.get() == "cajero":
            crear_boton_menu("📝 Registrar Pedido", self.mostrar_registrar_pedido).pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("👀 Ver Pedidos Activos", self.mostrar_pedidos_activos).pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("💳 Cobrar / Facturar", self.mostrar_cobrar).pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("❌ Cancelar Pedido", self.mostrar_cancelar_pedido, "#FF5722").pack(pady=tamaños['espaciado_botones'])

        elif self.rol_usuario.get() == "admin":
            crear_boton_menu("📦 Gestión de Productos", self.mostrar_gestion_productos, "#FF9800").pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("🎁 Gestión de Ofertas", self.mostrar_gestion_ofertas, "#E91E63").pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("👤 Gestión de Usuarios", self.mostrar_gestion_usuarios, "#FF9800").pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("📊 Reportes de Ventas", self.mostrar_reportes, "#3F51B5").pack(pady=tamaños['espaciado_botones'])
            crear_boton_menu("⚙️ Configuración del Sistema", self.mostrar_configuracion, "#673AB7").pack(pady=tamaños['espaciado_botones'])

        # Botón de cerrar sesión separado
        tk.Frame(botones_frame, height=20, bg=self.color_fondo_ventana).pack()  # Espaciador
        
        # --- CAMBIO RÁPIDO DE ROL ---
        cambio_rol_frame = tk.Frame(botones_frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        cambio_rol_frame.pack(fill="x", pady=10)
        
        tk.Label(cambio_rol_frame, text="🔄 Cambiar Rol Rápidamente:", 
                font=("Helvetica", 10, "bold"), bg=self.color_fondo_ventana, fg="#1976D2").pack(pady=(8, 5))
        
        roles_rapidos_frame = tk.Frame(cambio_rol_frame, bg=self.color_fondo_ventana)
        roles_rapidos_frame.pack(pady=(0, 10))
        
        def cambiar_rol_rapido(nuevo_rol):
            self.rol_usuario.set(nuevo_rol)
            self.mostrar_menu_principal()
        
        # Mostrar solo los roles que NO son el actual
        rol_actual = self.rol_usuario.get()
        
        if rol_actual != "cliente":
            tk.Button(roles_rapidos_frame, text="👤 Cliente", 
                     command=lambda: cambiar_rol_rapido("cliente"),
                     bg="#4CAF50", fg="white", font=("Helvetica", 9, "bold"),
                     relief="raised", bd=1, padx=10, pady=4).pack(side="left", padx=3)
        
        if rol_actual != "cajero":
            tk.Button(roles_rapidos_frame, text="💰 Cajero", 
                     command=lambda: cambiar_rol_rapido("cajero"),
                     bg="#FF9800", fg="white", font=("Helvetica", 9, "bold"),
                     relief="raised", bd=1, padx=10, pady=4).pack(side="left", padx=3)
        
        if rol_actual != "admin":
            tk.Button(roles_rapidos_frame, text="⚙️ Admin", 
                     command=lambda: cambiar_rol_rapido("admin"),
                     bg="#9C27B0", fg="white", font=("Helvetica", 9, "bold"),
                     relief="raised", bd=1, padx=10, pady=4).pack(side="left", padx=3)
        
        # Espaciador
        tk.Frame(botones_frame, height=15, bg=self.color_fondo_ventana).pack()
        crear_boton_menu("🔒 Cerrar Sesión", self.mostrar_login, "#9E9E9E").pack(pady=10)

    # --- Vistas Cliente ---
    def mostrar_menu_sushi(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Nuestro Menú 🍣", style="Titulo.TLabel").pack(pady=(0, 20))
        
        # Mostrar ofertas activas en el menú
        ofertas_activas = [o for o in self.ofertas if o.get('activa', False)]
        if ofertas_activas:
            ofertas_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
            ofertas_frame.pack(fill="x", padx=20, pady=(0, 20))
            
            tk.Label(ofertas_frame, text="🎁 ¡OFERTAS ESPECIALES! 🎁", 
                    font=("Helvetica", 14, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=10)
            
            # Mostrar solo las ofertas más relevantes (máximo 2)
            for oferta in ofertas_activas[:2]:
                oferta_text = f"• {oferta['nombre']}: {oferta['descripcion']}"
                tk.Label(ofertas_frame, text=oferta_text, 
                        font=("Helvetica", 10), bg=self.color_fondo_ventana, fg=self.color_titulo,
                        wraplength=700, justify="left").pack(anchor="w", padx=20, pady=2)
            
            if len(ofertas_activas) > 2:
                tk.Label(ofertas_frame, text="Ver más ofertas en la sección Ofertas Especiales", 
                        font=("Helvetica", 9, "italic"), bg=self.color_fondo_ventana, fg=self.color_texto).pack(pady=(5, 10))
        
        # Menú principal con precios
        menu_items = [
            ("California Roll", "Kanikama, palta, pepino", "$120"),
            ("Philadelphia Roll", "Salmón, queso Philadelphia, palta", "$150"), 
            ("Salmon Roll", "Salmón fresco, pepino, wasabi", "$180"),
            ("Tuna Roll", "Atún rojo, palta, sésamo", "$200"),
            ("Veggie Roll", "Palta, pepino, zanahoria, lechuga", "$100")
        ]
        
        self._crear_tabla(frame, ("Nombre", "Descripción", "Precio"), menu_items)
        
        # Botones de acción
        btn_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)
        
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(btn_frame, text="🛒 Agregar al Carrito", 
                 bg="#4CAF50", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="left", padx=10)
        tk.Button(btn_frame, text="🎁 Ver Ofertas", command=self.mostrar_ofertas_cliente,
                 bg="#FF6F00", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="left", padx=10)
        
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    def mostrar_carrito(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Carrito de Compras 🛒", style="Titulo.TLabel").pack(pady=(0, 20))
        self._crear_tabla(frame, ("Producto", "Cantidad", "Subtotal"), [("California Roll", "2", "$240")])
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    def mostrar_realizar_pedido(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Confirmar Pedido 📦", style="Titulo.TLabel").pack(pady=(0, 20))
        ttk.Label(frame, text="Revisa tu pedido antes de confirmar.").pack()
        ttk.Label(frame, text="Total: $240.00", style="Subtitulo.TLabel").pack(pady=10)
        btn_frame = ttk.Frame(frame);
        btn_frame.pack(pady=10)
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(btn_frame, text="✅ Confirmar", width=tamaños['boton_width']//2).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", width=tamaños['boton_width']//2).pack(side="left", padx=5)
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    def mostrar_ofertas_cliente(self):
        """Vista de ofertas especiales para clientes"""
        frame = self.limpiar_ventana()
        
        # Título principal con animación visual
        titulo_frame = tk.Frame(frame, bg="#FF6F00", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="🎁 ¡OFERTAS ESPECIALES! 🎁", 
                font=("Impact", 24, "bold"), bg="#FF6F00", fg="white", 
                pady=15).pack()
        
        # Frame scrollable para ofertas
        canvas = tk.Canvas(frame, bg=self.color_fondo_ventana, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.color_fondo_ventana)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mostrar ofertas activas
        ofertas_activas = [oferta for oferta in self.ofertas if oferta.get('activa', False)]
        
        for i, oferta in enumerate(ofertas_activas):
            self._crear_tarjeta_oferta(scrollable_frame, oferta, i)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scrollbar.pack(side="right", fill="y")
        
        # Botón regresar
        btn_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(btn_frame, text="⬅️ Regresar", command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack()

    def _crear_tarjeta_oferta(self, parent, oferta, index):
        """Crea una tarjeta visual para mostrar una oferta"""
        # Colores alternos para las tarjetas
        colores_tarjeta = ["#FFEB3B", "#4CAF50", "#2196F3", "#FF5722"]
        color_tarjeta = colores_tarjeta[index % len(colores_tarjeta)]
        
        # Frame principal de la tarjeta
        tarjeta_frame = tk.Frame(parent, bg=color_tarjeta, relief="raised", bd=3)
        tarjeta_frame.pack(fill="x", pady=10, padx=20)
        
        # Frame interno con padding
        contenido_frame = tk.Frame(tarjeta_frame, bg=color_tarjeta)
        contenido_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título de la oferta
        tk.Label(contenido_frame, text=f"🔥 {oferta['nombre']}", 
                font=("Helvetica", 16, "bold"), bg=color_tarjeta, fg="white" if color_tarjeta in ["#4CAF50", "#2196F3", "#FF5722"] else "black").pack(anchor="w")
        
        # Descripción
        tk.Label(contenido_frame, text=oferta['descripcion'], 
                font=("Helvetica", 12), bg=color_tarjeta, fg="white" if color_tarjeta in ["#4CAF50", "#2196F3", "#FF5722"] else "black",
                wraplength=600, justify="left").pack(anchor="w", pady=(5, 10))
        
        # Frame para detalles
        detalles_frame = tk.Frame(contenido_frame, bg=color_tarjeta)
        detalles_frame.pack(fill="x")
        
        # Información adicional según tipo
        if oferta['tipo'] == '2x1':
            tk.Label(detalles_frame, text="💫 Tipo: 2x1", 
                    font=("Helvetica", 10, "bold"), bg=color_tarjeta, 
                    fg="white" if color_tarjeta in ["#4CAF50", "#2196F3", "#FF5722"] else "black").pack(side="left")
        elif oferta['tipo'] == 'combo':
            tk.Label(detalles_frame, text=f"🍽️ Combo: {oferta['descuento']}% OFF", 
                    font=("Helvetica", 10, "bold"), bg=color_tarjeta,
                    fg="white" if color_tarjeta in ["#4CAF50", "#2196F3", "#FF5722"] else "black").pack(side="left")
        elif oferta['tipo'] == 'descuento_dia':
            tk.Label(detalles_frame, text=f"📅 {oferta['descuento']}% OFF los {oferta['dia_semana']}s", 
                    font=("Helvetica", 10, "bold"), bg=color_tarjeta,
                    fg="white" if color_tarjeta in ["#4CAF50", "#2196F3", "#FF5722"] else "black").pack(side="left")
        
        # Fecha de validez
        tk.Label(detalles_frame, text=f"⏰ Válida hasta: {oferta['fecha_fin']}", 
                font=("Helvetica", 10), bg=color_tarjeta,
                fg="white" if color_tarjeta in ["#4CAF50", "#2196F3", "#FF5722"] else "black").pack(side="right")

    def mostrar_historial(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Historial de Pedidos 📜", style="Titulo.TLabel").pack(pady=(0, 20))
        self._crear_tabla(frame, ("ID Pedido", "Fecha", "Total", "Estado"),
                          [("#1024", "2025-09-08", "$480", "Entregado")])
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    # --- Vistas Cajero ---
    def mostrar_registrar_pedido(self):
        self.mostrar_menu_sushi()
        for widget in self.winfo_children()[0].winfo_children():
            if isinstance(widget, ttk.Button) and widget['text'] == '⬅️ Regresar':
                widget.configure(command=self.mostrar_menu_principal)

    def mostrar_pedidos_activos(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Pedidos Activos 👀", style="Titulo.TLabel").pack(pady=(0, 20))
        self._crear_tabla(frame, ("ID Pedido", "Mesa", "Total", "Estado"), [("#1025", "5", "$600", "En preparación")])
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    def mostrar_cobrar(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Cobrar / Facturar 💳", style="Titulo.TLabel").pack(pady=(0, 20))
        ttk.Label(frame, text="ID del Pedido:", style="Subtitulo.TLabel").pack(pady=(10, 2))
        ttk.Entry(frame, width=30).pack()
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(frame, text="✅ Confirmar Pago", width=tamaños['boton_width']).pack(pady=10)
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    def mostrar_cancelar_pedido(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Cancelar Pedido ❌", style="Titulo.TLabel").pack(pady=(0, 20))
        ttk.Label(frame, text="ID del Pedido a cancelar:", style="Subtitulo.TLabel").pack(pady=(10, 2))
        ttk.Entry(frame, width=30).pack()
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(frame, text="⚠️ Confirmar Cancelación", width=tamaños['boton_width']).pack(pady=10)
        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=20)

    # --- Vistas Admin ---
    def mostrar_gestion_productos(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Gestión de Productos 📦", style="Titulo.TLabel").pack(pady=(0, 20))
        self._crear_tabla(frame, ("ID", "Nombre", "Precio"), [("SUS01", "California Roll", "$120")])

        btn_frame = ttk.Frame(frame);
        btn_frame.pack(pady=20)
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(btn_frame, text="➕ Agregar", width=tamaños['boton_width']//3,
                   command=lambda: self.mostrar_formulario_producto("Agregar Producto")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Editar", width=tamaños['boton_width']//3,
                   command=lambda: self.mostrar_formulario_producto("Editar Producto")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", width=tamaños['boton_width']//3).pack(side="left", padx=5)

        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=10)

    def mostrar_gestion_ofertas(self):
        """Vista de gestión de ofertas para administradores"""
        frame = self.limpiar_ventana()
        
        # Título más compacto
        titulo_frame = tk.Frame(frame, bg="#E91E63", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 15))
        tk.Label(titulo_frame, text="🎁 Gestión de Ofertas 🎁", 
                font=("Impact", 20, "bold"), bg="#E91E63", fg="white", 
                pady=10).pack()

        # Frame para la tabla de ofertas más compacto
        tabla_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=15, pady=(0, 10))
        
        # Crear tabla de ofertas con altura reducida para pantallas pequeñas
        columns = ("ID", "Nombre", "Tipo", "Descuento", "Estado", "Fecha Fin")
        tree = ttk.Treeview(tabla_frame, columns=columns, show="headings", height=6)
        
        # Configurar columnas más compactas
        for col in columns:
            tree.heading(col, text=col)
            if col == "Nombre":
                tree.column(col, width=180, anchor="w")
            elif col == "Descuento":
                tree.column(col, width=70, anchor="center")
            elif col == "Estado":
                tree.column(col, width=70, anchor="center")
            elif col == "ID":
                tree.column(col, width=60, anchor="center")
            else:
                tree.column(col, width=90, anchor="center")
        
        # Llenar tabla con ofertas
        for oferta in self.ofertas:
            estado = "✅ Activa" if oferta.get('activa', False) else "❌ Inactiva"
            descuento = f"{oferta['descuento']}%" if oferta['tipo'] != '2x1' else "50% (2x1)"
            tree.insert("", "end", values=(
                oferta['id'], 
                oferta['nombre'], 
                oferta['tipo'].replace('_', ' ').title(), 
                descuento,
                estado,
                oferta['fecha_fin']
            ))
        
        # Scrollbar para la tabla
        scrollbar_tabla = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_tabla.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar_tabla.pack(side="right", fill="y")
        
        # Frame para botones de gestión más compacto
        botones_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        botones_frame.pack(pady=10)
        
        tamaños = self.calcular_tamaños_responsivos()
        
        def crear_boton_gestion(texto, comando, color_bg="#4CAF50"):
            return tk.Button(botones_frame, text=texto, command=comando,
                           bg=color_bg, fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                           relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady'], 
                           width=tamaños['boton_gestion_width'])
        
        # Reorganizar botones en 2 filas más compactas
        fila1 = tk.Frame(botones_frame, bg=self.color_fondo_ventana)
        fila1.pack(pady=2)
        crear_boton_gestion("➕ Nueva", lambda: self.mostrar_formulario_oferta("nueva"), "#4CAF50").pack(side="left", padx=tamaños['espaciado_botones']//2)
        crear_boton_gestion("✏️ Editar", lambda: self.editar_oferta_seleccionada(tree), "#FF9800").pack(side="left", padx=tamaños['espaciado_botones']//2)
        crear_boton_gestion("🗑️ Eliminar", lambda: self.eliminar_oferta_seleccionada(tree), "#F44336").pack(side="left", padx=tamaños['espaciado_botones']//2)
        
        # Segunda fila de botones más compacta
        fila2 = tk.Frame(botones_frame, bg=self.color_fondo_ventana)
        fila2.pack(pady=2)
        crear_boton_gestion("✅ Activar", lambda: self.toggle_oferta_estado(tree, True), "#2196F3").pack(side="left", padx=tamaños['espaciado_botones']//2)
        crear_boton_gestion("❌ Desactivar", lambda: self.toggle_oferta_estado(tree, False), "#9E9E9E").pack(side="left", padx=tamaños['espaciado_botones']//2)
        crear_boton_gestion("📊 Estadísticas", self.mostrar_estadisticas_ofertas, "#673AB7").pack(side="left", padx=tamaños['espaciado_botones']//2)
        
        # Botón regresar más compacto
        tk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(pady=10)

    def mostrar_formulario_oferta(self, modo, oferta_id=None):
        """Formulario para crear/editar ofertas"""
        frame = self.limpiar_ventana()
        
        titulo = "Nueva Oferta 🎁" if modo == "nueva" else "Editar Oferta ✏️"
        ttk.Label(frame, text=titulo, style="Titulo.TLabel").pack(pady=(0, 30))
        
        # Frame principal del formulario
        form_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        form_frame.pack(pady=20, padx=50)
        
        form_inner = tk.Frame(form_frame, bg=self.color_fondo_ventana)
        form_inner.pack(padx=30, pady=30)
        
        # Variables del formulario
        vars_form = {}
        
        # Nombre de la oferta
        tk.Label(form_inner, text="Nombre de la Oferta:", font=("Helvetica", 12, "bold"), 
                bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=(10, 2))
        vars_form['nombre'] = tk.StringVar()
        tk.Entry(form_inner, textvariable=vars_form['nombre'], width=50, 
                font=("Helvetica", 11), relief="solid", bd=2).pack(pady=(0, 10))
        
        # Descripción
        tk.Label(form_inner, text="Descripción:", font=("Helvetica", 12, "bold"), 
                bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=(10, 2))
        vars_form['descripcion'] = tk.StringVar()
        tk.Entry(form_inner, textvariable=vars_form['descripcion'], width=50, 
                font=("Helvetica", 11), relief="solid", bd=2).pack(pady=(0, 10))
        
        # Tipo de oferta
        tk.Label(form_inner, text="Tipo de Oferta:", font=("Helvetica", 12, "bold"), 
                bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=(10, 2))
        vars_form['tipo'] = tk.StringVar(value="descuento")
        tipos_frame = tk.Frame(form_inner, bg=self.color_fondo_ventana)
        tipos_frame.pack(anchor="w", pady=(0, 10))
        
        tk.Radiobutton(tipos_frame, text="2x1", variable=vars_form['tipo'], value="2x1", 
                      bg=self.color_fondo_ventana, fg=self.color_texto, font=("Helvetica", 10)).pack(side="left", padx=(0, 15))
        tk.Radiobutton(tipos_frame, text="Descuento %", variable=vars_form['tipo'], value="descuento", 
                      bg=self.color_fondo_ventana, fg=self.color_texto, font=("Helvetica", 10)).pack(side="left", padx=(0, 15))
        tk.Radiobutton(tipos_frame, text="Combo", variable=vars_form['tipo'], value="combo", 
                      bg=self.color_fondo_ventana, fg=self.color_texto, font=("Helvetica", 10)).pack(side="left", padx=(0, 15))
        
        # Porcentaje de descuento
        tk.Label(form_inner, text="Porcentaje de Descuento (%):", font=("Helvetica", 12, "bold"), 
                bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=(10, 2))
        vars_form['descuento'] = tk.StringVar()
        tk.Entry(form_inner, textvariable=vars_form['descuento'], width=20, 
                font=("Helvetica", 11), relief="solid", bd=2).pack(anchor="w", pady=(0, 10))
        
        # Fecha de fin
        tk.Label(form_inner, text="Fecha de Fin (YYYY-MM-DD):", font=("Helvetica", 12, "bold"), 
                bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=(10, 2))
        vars_form['fecha_fin'] = tk.StringVar()
        tk.Entry(form_inner, textvariable=vars_form['fecha_fin'], width=30, 
                font=("Helvetica", 11), relief="solid", bd=2).pack(anchor="w", pady=(0, 20))
        
        # Si es edición, cargar datos
        if modo == "editar" and oferta_id:
            oferta = next((o for o in self.ofertas if o['id'] == oferta_id), None)
            if oferta:
                vars_form['nombre'].set(oferta['nombre'])
                vars_form['descripcion'].set(oferta['descripcion'])
                vars_form['tipo'].set(oferta['tipo'])
                vars_form['descuento'].set(str(oferta['descuento']))
                vars_form['fecha_fin'].set(oferta['fecha_fin'])
        
        # Botones del formulario
        btn_frame = tk.Frame(form_inner, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)
        
        def guardar_oferta():
            try:
                # Validar campos
                if not all([vars_form['nombre'].get(), vars_form['descripcion'].get(), vars_form['fecha_fin'].get()]):
                    messagebox.showerror("Error", "Todos los campos son obligatorios")
                    return
                
                if vars_form['tipo'].get() != "2x1" and not vars_form['descuento'].get().isdigit():
                    messagebox.showerror("Error", "El descuento debe ser un número")
                    return
                
                # Crear nueva oferta o actualizar existente
                nueva_oferta = {
                    "id": oferta_id if modo == "editar" else f"OFF{len(self.ofertas)+1:03d}",
                    "nombre": vars_form['nombre'].get(),
                    "descripcion": vars_form['descripcion'].get(),
                    "tipo": vars_form['tipo'].get(),
                    "productos_aplicables": ["todos"],
                    "descuento": 50 if vars_form['tipo'].get() == "2x1" else int(vars_form['descuento'].get()),
                    "activa": True,
                    "fecha_inicio": "2025-09-26",
                    "fecha_fin": vars_form['fecha_fin'].get()
                }
                
                if modo == "nueva":
                    self.ofertas.append(nueva_oferta)
                    messagebox.showinfo("Éxito", "Oferta creada exitosamente")
                else:
                    # Actualizar oferta existente
                    for i, oferta in enumerate(self.ofertas):
                        if oferta['id'] == oferta_id:
                            self.ofertas[i] = nueva_oferta
                            break
                    messagebox.showinfo("Éxito", "Oferta actualizada exitosamente")
                
                self.mostrar_gestion_ofertas()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar oferta: {str(e)}")
        
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(btn_frame, text="💾 Guardar", command=guardar_oferta,
                 bg="#4CAF50", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ Cancelar", command=self.mostrar_gestion_ofertas,
                 bg="#F44336", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="left", padx=5)

    def editar_oferta_seleccionada(self, tree):
        """Editar la oferta seleccionada en la tabla"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una oferta para editar")
            return
        
        item = tree.item(selection[0])
        oferta_id = item['values'][0]
        self.mostrar_formulario_oferta("editar", oferta_id)
    
    def eliminar_oferta_seleccionada(self, tree):
        """Eliminar la oferta seleccionada"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una oferta para eliminar")
            return
        
        item = tree.item(selection[0])
        oferta_id = item['values'][0]
        oferta_nombre = item['values'][1]
        
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar la oferta '{oferta_nombre}'?"):
            self.ofertas = [o for o in self.ofertas if o['id'] != oferta_id]
            messagebox.showinfo("Éxito", "Oferta eliminada exitosamente")
            self.mostrar_gestion_ofertas()
    
    def toggle_oferta_estado(self, tree, nuevo_estado):
        """Activar o desactivar una oferta"""
        selection = tree.selection()
        if not selection:
            accion = "activar" if nuevo_estado else "desactivar"
            messagebox.showwarning("Advertencia", f"Selecciona una oferta para {accion}")
            return
        
        item = tree.item(selection[0])
        oferta_id = item['values'][0]
        
        for oferta in self.ofertas:
            if oferta['id'] == oferta_id:
                oferta['activa'] = nuevo_estado
                estado_texto = "activada" if nuevo_estado else "desactivada"
                messagebox.showinfo("Éxito", f"Oferta {estado_texto} exitosamente")
                self.mostrar_gestion_ofertas()
                return
    
    def mostrar_estadisticas_ofertas(self):
        """Mostrar estadísticas básicas de ofertas"""
        total_ofertas = len(self.ofertas)
        ofertas_activas = len([o for o in self.ofertas if o.get('activa', False)])
        ofertas_inactivas = total_ofertas - ofertas_activas
        
        tipos_count = {}
        for oferta in self.ofertas:
            tipo = oferta['tipo']
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
        
        estadisticas = f"""📊 ESTADÍSTICAS DE OFERTAS
        
📈 Resumen General:
• Total de ofertas: {total_ofertas}
• Ofertas activas: {ofertas_activas}
• Ofertas inactivas: {ofertas_inactivas}

🎯 Por Tipo:"""
        
        for tipo, count in tipos_count.items():
            tipo_texto = tipo.replace('_', ' ').title()
            estadisticas += f"\n• {tipo_texto}: {count}"
        
        messagebox.showinfo("Estadísticas de Ofertas", estadisticas)

    def mostrar_gestion_usuarios(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Gestión de Usuarios 👤", style="Titulo.TLabel").pack(pady=(0, 20))
        self._crear_tabla(frame, ("ID", "Nombre", "Rol"), [("USR01", "Ana Gomez", "cajero")])

        btn_frame = ttk.Frame(frame);
        btn_frame.pack(pady=20)
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(btn_frame, text="➕ Agregar", width=tamaños['boton_width']//3).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Editar", width=tamaños['boton_width']//3).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", width=tamaños['boton_width']//3).pack(side="left", padx=5)

        ttk.Button(frame, text="⬅️ Regresar", command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=10)

    # --- 3. Formularios Internos (Ejemplo para Productos) ---
    def mostrar_formulario_producto(self, titulo):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text=titulo, style="Titulo.TLabel").pack(pady=(0, 20))

        ttk.Label(frame, text="Nombre del Producto:", style="Subtitulo.TLabel").pack(anchor="w", padx=100)
        ttk.Entry(frame, width=40).pack(pady=(0, 10))

        ttk.Label(frame, text="Descripción:", style="Subtitulo.TLabel").pack(anchor="w", padx=100)
        ttk.Entry(frame, width=40).pack(pady=(0, 10))

        ttk.Label(frame, text="Precio:", style="Subtitulo.TLabel").pack(anchor="w", padx=100)
        ttk.Entry(frame, width=40).pack(pady=(0, 20))

        btn_frame = ttk.Frame(frame);
        btn_frame.pack(pady=10)
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(btn_frame, text="💾 Guardar", width=tamaños['boton_width']//2).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", width=tamaños['boton_width']//2).pack(side="left", padx=5)

        ttk.Button(frame, text="⬅️ Atrás", command=self.mostrar_gestion_productos, width=tamaños['boton_width']).pack(pady=20)

    def mostrar_reportes(self):
        """Sistema avanzado de reportes de ventas - VERSIÓN COMPLETAMENTE REDISEÑADA"""
        frame = self.limpiar_ventana()
        
        # ============================================================
        # ESTRUCTURA PRINCIPAL - DISEÑO LIMPIO Y GARANTIZADO
        # ============================================================
        
        # Contenedor principal con márgenes adecuados
        main_container = tk.Frame(frame, bg=self.color_fondo_ventana)
        main_container.pack(expand=True, fill="both", padx=20, pady=15)
        
        # ============================================================
        # SECCIÓN 1: TÍTULO Y BOTÓN DE NAVEGACIÓN (SIEMPRE VISIBLE)
        # ============================================================
        
        # Frame para título
        header_frame = tk.Frame(main_container, bg="#1565C0", relief="raised", bd=3)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(header_frame,
                              text="📊 REPORTES DE VENTAS AVANZADOS 📊",
                              font=("Arial", 18, "bold"),
                              bg="#1565C0", fg="white",
                              pady=15)
        title_label.pack()
        
        # Frame para botón de regresar - SIEMPRE VISIBLE
        navigation_frame = tk.Frame(main_container, bg="#4CAF50", relief="raised", bd=3)
        navigation_frame.pack(fill="x", pady=(0, 15))
        
        back_button = tk.Button(navigation_frame,
                               text="⬅️ REGRESAR AL MENÚ PRINCIPAL",
                               command=self.mostrar_menu_principal,
                               bg="white", fg="#4CAF50",
                               font=("Arial", 14, "bold"),
                               relief="raised", bd=2,
                               padx=30, pady=10)
        back_button.pack(pady=10)
        
        # ============================================================
        # SECCIÓN 2: PANEL DE FILTROS COMPACTO
        # ============================================================
        
        filters_container = tk.Frame(main_container, bg="#F5F5F5", relief="groove", bd=2)
        filters_container.pack(fill="x", pady=(0, 15))
        
        # Título de filtros
        tk.Label(filters_container,
                text="🔍 Filtros de Búsqueda y Control",
                font=("Arial", 12, "bold"),
                bg="#F5F5F5", fg="#333").pack(pady=10)
        
        # Contenedor de controles en línea
        controls_frame = tk.Frame(filters_container, bg="#F5F5F5")
        controls_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Fila de filtros
        filter_row = tk.Frame(controls_frame, bg="#F5F5F5")
        filter_row.pack(fill="x", pady=5)
        
        # Filtros de fecha
        tk.Label(filter_row, text="Desde:", bg="#F5F5F5", fg="#333", font=("Arial", 10)).pack(side="left")
        self.fecha_inicio = tk.Entry(filter_row, width=12, font=("Arial", 10))
        self.fecha_inicio.pack(side="left", padx=(5, 15))
        self.fecha_inicio.insert(0, "2025-09-25")
        
        tk.Label(filter_row, text="Hasta:", bg="#F5F5F5", fg="#333", font=("Arial", 10)).pack(side="left")
        self.fecha_fin = tk.Entry(filter_row, width=12, font=("Arial", 10))
        self.fecha_fin.pack(side="left", padx=(5, 15))
        self.fecha_fin.insert(0, "2025-09-27")
        
        # Filtro de producto
        tk.Label(filter_row, text="Producto:", bg="#F5F5F5", fg="#333", font=("Arial", 10)).pack(side="left")
        self.filtro_producto = tk.Entry(filter_row, width=18, font=("Arial", 10))
        self.filtro_producto.pack(side="left", padx=(5, 0))
        
        # Botones de acción
        buttons_row = tk.Frame(controls_frame, bg="#F5F5F5")
        buttons_row.pack(fill="x", pady=(10, 0))
        
        tk.Button(buttons_row, text="🔍 Aplicar Filtros",
                 command=self.aplicar_filtros_reportes,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=6).pack(side="left", padx=(0, 10))
        
        tk.Button(buttons_row, text="� Exportar PDF",
                 command=self.exportar_reporte_pdf,
                 bg="#FF5722", fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=6).pack(side="left", padx=(0, 10))
        
        tk.Button(buttons_row, text="� Limpiar",
                 command=self.limpiar_filtros_reportes,
                 bg="#9E9E9E", fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=6).pack(side="left")
        
        # ============================================================
        # SECCIÓN 3: SISTEMA DE PESTAÑAS (ÁREA PRINCIPAL)
        # ============================================================
        
        # Contenedor para el notebook
        notebook_container = tk.Frame(main_container, bg=self.color_fondo_ventana)
        notebook_container.pack(expand=True, fill="both")
        
        # Crear el notebook
        self.reports_notebook = ttk.Notebook(notebook_container)
        self.reports_notebook.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Configurar estilo del notebook
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[18, 10])
        
        # ============================================================
        # CREAR TODAS LAS PESTAÑAS
        # ============================================================
        
        # Pestaña 1: Resumen General de Ventas
        tab_resumen = ttk.Frame(self.reports_notebook)
        self.reports_notebook.add(tab_resumen, text="� Resumen General")
        self._crear_tab_resumen_ventas(tab_resumen)
        
        # Pestaña 2: Análisis por Productos
        tab_productos = ttk.Frame(self.reports_notebook)
        self.reports_notebook.add(tab_productos, text="🍣 Análisis por Productos")
        self._crear_tab_productos(tab_productos)
        
        # Pestaña 3: Tendencias Temporales
        tab_tendencias = ttk.Frame(self.reports_notebook)
        self.reports_notebook.add(tab_tendencias, text="📈 Tendencias Temporales")
        self._crear_tab_temporal(tab_tendencias)
        
        # Pestaña 4: Análisis de Ofertas
        tab_ofertas = ttk.Frame(self.reports_notebook)
        self.reports_notebook.add(tab_ofertas, text="🎁 Ofertas y Descuentos")
        self._crear_tab_ofertas(tab_ofertas)
        
        # Pestaña 5: Gestión de Datos (funciones avanzadas)
        tab_gestion = ttk.Frame(self.reports_notebook)
        self.reports_notebook.add(tab_gestion, text="⚙️ Gestión de Datos")
        self._crear_tab_gestion_datos(tab_gestion)
        
        # ============================================================
        # SECCIÓN 4: BARRA DE ESTADO
        # ============================================================
        
        status_frame = tk.Frame(main_container, bg="#E8F5E8", relief="sunken", bd=1)
        status_frame.pack(fill="x", pady=(10, 0))
        
        self.status_label = tk.Label(status_frame,
                                   text="✅ Sistema de reportes iniciado correctamente - Selecciona una pestaña para comenzar",
                                   bg="#E8F5E8", fg="#2E7D32",
                                   font=("Arial", 9),
                                   pady=8)
        self.status_label.pack()
    
    def _crear_tab_resumen_ventas(self, parent):
        """Crea la pestaña de resumen general de ventas"""
        # Frame principal con mejor espaciado
        main_frame = tk.Frame(parent, bg=self.color_fondo_ventana)
        main_frame.pack(expand=True, fill="both", padx=20, pady=15)
        
        # Calcular métricas generales
        total_ventas = len(self.ventas)
        ingresos_totales = sum(venta['total_final'] for venta in self.ventas)
        descuentos_totales = sum(venta['descuento_aplicado'] for venta in self.ventas)
        
        # Frame para métricas principales con LabelFrame
        metricas_frame = tk.LabelFrame(main_frame, text="📊 Métricas Principales", 
                                     font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, 
                                     fg=self.color_titulo, relief="ridge", bd=2, padx=15, pady=15)
        metricas_frame.pack(fill="x", pady=(0, 20))
        
        # Métricas en tarjetas
        metricas = [
            ("Total Ventas", str(total_ventas), "#4CAF50"),
            ("Ingresos", f"${ingresos_totales:,.2f}", "#2196F3"),
            ("Descuentos", f"${descuentos_totales:,.2f}", "#FF9800"),
            ("Promedio", f"${ingresos_totales/total_ventas:,.2f}" if total_ventas > 0 else "$0.00", "#9C27B0")
        ]
        
        for i, (titulo, valor, color) in enumerate(metricas):
            col = i % 2
            row = i // 2
            
            metrica_frame = tk.Frame(metricas_frame, bg=color, relief="raised", bd=3)
            metrica_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew", ipadx=20, ipady=15)
            metricas_frame.grid_columnconfigure(col, weight=1)
            
            tk.Label(metrica_frame, text=titulo, font=("Helvetica", 12, "bold"), 
                    bg=color, fg="white").pack()
            tk.Label(metrica_frame, text=valor, font=("Helvetica", 16, "bold"), 
                    bg=color, fg="white").pack()
        
        # Tabla detallada de ventas con LabelFrame
        tabla_frame = tk.LabelFrame(main_frame, text="📋 Detalle de Ventas Recientes", 
                                  font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, 
                                  fg=self.color_titulo, relief="ridge", bd=2, padx=15, pady=15)
        tabla_frame.pack(expand=True, fill="both")
        
        # Frame para botones de control de la tabla
        control_frame = tk.Frame(tabla_frame, bg=self.color_fondo_ventana)
        control_frame.pack(fill="x", pady=(0, 10))
        
        tk.Button(control_frame, text="🔄 Actualizar Lista", 
                 command=lambda: self.actualizar_tabla_ventas(tree),
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                 padx=15, pady=5).pack(side="left", padx=5)
        
        tk.Button(control_frame, text="📊 Ver Detalles", 
                 command=lambda: self.ver_detalle_venta_seleccionada(tree),
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                 padx=15, pady=5).pack(side="left", padx=5)
        
        # Crear tabla con scroll
        tabla_container = tk.Frame(tabla_frame, bg=self.color_fondo_ventana)
        tabla_container.pack(expand=True, fill="both")
        
        tree = ttk.Treeview(tabla_container, columns=("ID", "Fecha", "Productos", "Oferta", "Descuento", "Total"), show="headings", height=10)
        
        # Configurar columnas
        columnas_info = [
            ("ID", 80),
            ("Fecha", 130),
            ("Productos", 200),
            ("Oferta", 120),
            ("Descuento", 100),
            ("Total", 100)
        ]
        
        for col, ancho in columnas_info:
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center" if col in ["ID", "Descuento", "Total"] else "w")
        
        # Llenar tabla con datos de ventas
        for venta in sorted(self.ventas, key=lambda x: x['fecha'], reverse=True):
            fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            productos_texto = ", ".join([f"{p['nombre']} x{p['cantidad']}" for p in venta['productos']])
            if len(productos_texto) > 30:
                productos_texto = productos_texto[:27] + "..."
            
            oferta_texto = venta['oferta_aplicada'] if venta['oferta_aplicada'] else "Sin oferta"
            descuento_texto = f"${venta['descuento_aplicado']:.2f}"
            total_texto = f"${venta['total_final']:.2f}"
            
            tree.insert("", "end", values=(
                venta['id'], fecha_formateada, productos_texto, 
                oferta_texto, descuento_texto, total_texto
            ))
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tabla_container, orient="vertical", command=tree.yview)
        scrollbar_h = ttk.Scrollbar(tabla_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
    
    def _crear_tab_productos(self, parent):
        """Crea la pestaña de análisis por producto"""
        # Analizar ventas por producto
        productos_stats = {}
        for venta in self.ventas:
            for producto in venta['productos']:
                nombre = producto['nombre']
                if nombre not in productos_stats:
                    productos_stats[nombre] = {
                        'cantidad_vendida': 0,
                        'ingresos': 0,
                        'ventas': 0
                    }
                productos_stats[nombre]['cantidad_vendida'] += producto['cantidad']
                productos_stats[nombre]['ingresos'] += producto['subtotal']
                productos_stats[nombre]['ventas'] += 1
        
        # Ordenar por ingresos
        productos_ordenados = sorted(productos_stats.items(), 
                                   key=lambda x: x[1]['ingresos'], reverse=True)
        
        # Frame principal
        main_frame = tk.Frame(parent, bg=self.color_fondo_ventana)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Título
        tk.Label(main_frame, text="🍣 Análisis de Productos", 
                font=("Helvetica", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(0,15))
        
        # Tabla de productos
        tree_productos = ttk.Treeview(main_frame, 
                                     columns=("Producto", "Cantidad", "Ventas", "Ingresos", "Promedio"), 
                                     show="headings", height=12)
        
        columnas = [
            ("Producto", 150),
            ("Cantidad", 100),
            ("Ventas", 80),
            ("Ingresos", 120),
            ("Promedio", 120)
        ]
        
        for col, ancho in columnas:
            tree_productos.heading(col, text=col)
            tree_productos.column(col, width=ancho, anchor="center" if col != "Producto" else "w")
        
        # Llenar datos
        for producto, stats in productos_ordenados:
            promedio = stats['ingresos'] / stats['ventas'] if stats['ventas'] > 0 else 0
            tree_productos.insert("", "end", values=(
                producto,
                stats['cantidad_vendida'],
                stats['ventas'],
                f"${stats['ingresos']:.2f}",
                f"${promedio:.2f}"
            ))
        
        tree_productos.pack(expand=True, fill="both", pady=10)
        
        # Scrollbar para productos
        scrollbar_productos = ttk.Scrollbar(main_frame, orient="vertical", command=tree_productos.yview)
        tree_productos.configure(yscrollcommand=scrollbar_productos.set)
        scrollbar_productos.pack(side="right", fill="y")
    
    def _crear_tab_temporal(self, parent):
        """Crea la pestaña de análisis temporal"""
        main_frame = tk.Frame(parent, bg=self.color_fondo_ventana)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        tk.Label(main_frame, text="📅 Análisis Temporal de Ventas", 
                font=("Helvetica", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(0,15))
        
        # Análisis por día
        ventas_por_dia = {}
        for venta in self.ventas:
            fecha = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
            dia = fecha.strftime('%Y-%m-%d')
            if dia not in ventas_por_dia:
                ventas_por_dia[dia] = {'ventas': 0, 'ingresos': 0}
            ventas_por_dia[dia]['ventas'] += 1
            ventas_por_dia[dia]['ingresos'] += venta['total_final']
        
        # Tabla temporal
        tree_temporal = ttk.Treeview(main_frame, 
                                   columns=("Fecha", "Ventas", "Ingresos", "Promedio"), 
                                   show="headings", height=10)
        
        for col in ["Fecha", "Ventas", "Ingresos", "Promedio"]:
            tree_temporal.heading(col, text=col)
            tree_temporal.column(col, width=120, anchor="center")
        
        # Llenar datos temporales
        for dia in sorted(ventas_por_dia.keys(), reverse=True):
            stats = ventas_por_dia[dia]
            fecha_formateada = datetime.datetime.strptime(dia, '%Y-%m-%d').strftime('%d/%m/%Y')
            promedio = stats['ingresos'] / stats['ventas'] if stats['ventas'] > 0 else 0
            
            tree_temporal.insert("", "end", values=(
                fecha_formateada,
                stats['ventas'],
                f"${stats['ingresos']:.2f}",
                f"${promedio:.2f}"
            ))
        
        tree_temporal.pack(expand=True, fill="both")
    
    def _crear_tab_ofertas(self, parent):
        """Crea la pestaña de análisis de ofertas y descuentos"""
        main_frame = tk.Frame(parent, bg=self.color_fondo_ventana)
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        tk.Label(main_frame, text="🎁 Análisis de Ofertas y Descuentos", 
                font=("Helvetica", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(0,15))
        
        # Análisis de ofertas
        ofertas_stats = {}
        ventas_sin_oferta = 0
        
        for venta in self.ventas:
            if venta['oferta_aplicada']:
                oferta_id = venta['oferta_aplicada']
                if oferta_id not in ofertas_stats:
                    ofertas_stats[oferta_id] = {
                        'usos': 0,
                        'descuento_total': 0,
                        'ahorro_cliente': 0
                    }
                ofertas_stats[oferta_id]['usos'] += 1
                ofertas_stats[oferta_id]['descuento_total'] += venta['descuento_aplicado']
                ofertas_stats[oferta_id]['ahorro_cliente'] += venta['descuento_aplicado']
            else:
                ventas_sin_oferta += 1
        
        # Frame para estadísticas de ofertas
        stats_frame = tk.Frame(main_frame, bg=self.color_fondo_ventana)
        stats_frame.pack(fill="x", pady=(0,20))
        
        total_descuentos = sum(venta['descuento_aplicado'] for venta in self.ventas)
        porcentaje_con_oferta = (len(self.ventas) - ventas_sin_oferta) / len(self.ventas) * 100 if self.ventas else 0
        
        tk.Label(stats_frame, text=f"💰 Total en descuentos otorgados: ${total_descuentos:.2f}", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg="#E91E63").pack(anchor="w")
        tk.Label(stats_frame, text=f"📊 Porcentaje de ventas con oferta: {porcentaje_con_oferta:.1f}%", 
                font=("Helvetica", 12), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w")
        tk.Label(stats_frame, text=f"🛍️ Ventas sin oferta: {ventas_sin_oferta}", 
                font=("Helvetica", 12), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w")
        
        # Tabla de ofertas
        tree_ofertas = ttk.Treeview(main_frame, 
                                  columns=("Oferta", "Nombre", "Usos", "Descuento_Total", "Promedio"), 
                                  show="headings", height=8)
        
        columnas_ofertas = [
            ("Oferta", 100),
            ("Nombre", 200),
            ("Usos", 80),
            ("Descuento_Total", 120),
            ("Promedio", 120)
        ]
        
        for col, ancho in columnas_ofertas:
            tree_ofertas.heading(col, text=col.replace("_", " "))
            tree_ofertas.column(col, width=ancho, anchor="center" if col != "Nombre" else "w")
        
        # Llenar datos de ofertas
        for oferta_id, stats in ofertas_stats.items():
            # Buscar el nombre de la oferta
            nombre_oferta = "Oferta no encontrada"
            for oferta in self.ofertas:
                if oferta['id'] == oferta_id:
                    nombre_oferta = oferta['nombre']
                    break
            
            promedio_descuento = stats['descuento_total'] / stats['usos'] if stats['usos'] > 0 else 0
            
            tree_ofertas.insert("", "end", values=(
                oferta_id,
                nombre_oferta,
                stats['usos'],
                f"${stats['descuento_total']:.2f}",
                f"${promedio_descuento:.2f}"
            ))
        
        tree_ofertas.pack(expand=True, fill="both")
    
    def _crear_tab_gestion_datos(self, parent):
        """Crea la pestaña de gestión de datos con funciones avanzadas"""
        # Frame principal con scroll
        canvas = tk.Canvas(parent, bg=self.color_fondo_ventana, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.color_fondo_ventana)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Título principal
        tk.Label(scrollable_frame, text="⚙️ GESTIÓN DE DATOS Y HERRAMIENTAS AVANZADAS", 
                font=("Helvetica", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(20, 30))
        
        # Sección 1: Respaldo y Restauración
        backup_frame = tk.LabelFrame(scrollable_frame, text="💾 Respaldo y Restauración de Datos", 
                                   font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, 
                                   fg=self.color_titulo, relief="ridge", bd=2, padx=20, pady=15)
        backup_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        info_backup = tk.Label(backup_frame, 
                             text="Protege tus datos creando copias de seguridad de ventas, ofertas y configuraciones.\nRecomendamos realizar respaldos periódicos.",
                             font=("Helvetica", 11), bg=self.color_fondo_ventana, fg=self.color_texto, 
                             wraplength=500, justify="left")
        info_backup.pack(pady=(0, 15), anchor="w")
        
        botones_backup_frame = tk.Frame(backup_frame, bg=self.color_fondo_ventana)
        botones_backup_frame.pack(fill="x")
        
        tk.Button(botones_backup_frame, text="💾 Crear Respaldo Completo", 
                 command=self.backup_datos_reportes, bg="#4CAF50", fg="white", 
                 font=("Helvetica", 11, "bold"), relief="raised", bd=2, 
                 padx=25, pady=10, cursor="hand2").pack(side="left", padx=(0, 15))
        
        tk.Button(botones_backup_frame, text="📁 Restaurar desde Archivo", 
                 command=self.restaurar_datos_reportes, bg="#FF9800", fg="white", 
                 font=("Helvetica", 11, "bold"), relief="raised", bd=2, 
                 padx=25, pady=10, cursor="hand2").pack(side="left")
        
        # Sección 2: Análisis Comparativo
        analisis_frame = tk.LabelFrame(scrollable_frame, text="📈 Análisis Comparativo de Períodos", 
                                     font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, 
                                     fg=self.color_titulo, relief="ridge", bd=2, padx=20, pady=15)
        analisis_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        info_analisis = tk.Label(analisis_frame, 
                               text="Compara el rendimiento entre diferentes períodos de tiempo.\nAnaliza tendencias, crecimiento y patrones de ventas.",
                               font=("Helvetica", 11), bg=self.color_fondo_ventana, fg=self.color_texto,
                               wraplength=500, justify="left")
        info_analisis.pack(pady=(0, 15), anchor="w")
        
        tk.Button(analisis_frame, text="📊 Generar Análisis Comparativo", 
                 command=self.generar_analisis_comparativo, bg="#2196F3", fg="white", 
                 font=("Helvetica", 11, "bold"), relief="raised", bd=2, 
                 padx=25, pady=10, cursor="hand2").pack(anchor="w")
        
        # Sección 3: Alertas Inteligentes
        alertas_frame = tk.LabelFrame(scrollable_frame, text="🚨 Sistema de Alertas Inteligentes", 
                                    font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, 
                                    fg=self.color_titulo, relief="ridge", bd=2, padx=20, pady=15)
        alertas_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        info_alertas = tk.Label(alertas_frame, 
                              text="Recibe alertas automáticas sobre el rendimiento de tu negocio.\nIdentifica oportunidades y problemas potenciales.",
                              font=("Helvetica", 11), bg=self.color_fondo_ventana, fg=self.color_texto,
                              wraplength=500, justify="left")
        info_alertas.pack(pady=(0, 15), anchor="w")
        
        tk.Button(alertas_frame, text="🚨 Ver Alertas Inteligentes", 
                 command=self.mostrar_alertas_inteligentes, bg="#9C27B0", fg="white", 
                 font=("Helvetica", 11, "bold"), relief="raised", bd=2, 
                 padx=25, pady=10, cursor="hand2").pack(anchor="w")
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def aplicar_filtros_reportes(self):
        """Aplica los filtros seleccionados a los reportes"""
        try:
            fecha_inicio = self.fecha_inicio.get()
            fecha_fin = self.fecha_fin.get()
            producto_filtro = self.filtro_producto.get()
            pago_filtro = self.filtro_pago.get()
            
            # Validar fechas
            try:
                fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
                fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
                if fecha_inicio_dt > fecha_fin_dt:
                    messagebox.showwarning("Error de Fechas", "La fecha de inicio debe ser anterior a la fecha de fin")
                    return
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
                return
            
            # Filtrar ventas
            ventas_filtradas = []
            for venta in self.ventas:
                fecha_venta = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
                fecha_venta_solo = fecha_venta.date()
                
                # Filtro por fecha
                if not (fecha_inicio_dt.date() <= fecha_venta_solo <= fecha_fin_dt.date()):
                    continue
                
                # Filtro por producto
                if producto_filtro != "Todos":
                    productos_en_venta = [p['nombre'] for p in venta['productos']]
                    if producto_filtro not in productos_en_venta:
                        continue
                
                # Filtro por método de pago
                if pago_filtro != "Todos" and venta.get('metodo_pago') != pago_filtro:
                    continue
                
                ventas_filtradas.append(venta)
            
            # Mostrar resultados
            if ventas_filtradas:
                self.mostrar_resultados_filtrados(ventas_filtradas, fecha_inicio, fecha_fin, producto_filtro, pago_filtro)
            else:
                messagebox.showinfo("Sin Resultados", "No se encontraron ventas que coincidan con los filtros aplicados")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar filtros: {str(e)}")
    
    def mostrar_resultados_filtrados(self, ventas_filtradas, fecha_inicio, fecha_fin, producto_filtro, pago_filtro):
        """Muestra los resultados filtrados en una nueva ventana"""
        ventana_resultados = tk.Toplevel(self)
        ventana_resultados.title("Resultados Filtrados")
        ventana_resultados.geometry("1000x600")
        ventana_resultados.configure(bg=self.color_fondo_ventana)
        
        # Título
        titulo_frame = tk.Frame(ventana_resultados, bg="#673AB7", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="📊 RESULTADOS FILTRADOS", 
                font=("Impact", 18, "bold"), bg="#673AB7", fg="white", 
                pady=10).pack()
        
        # Mostrar filtros aplicados
        filtros_frame = tk.Frame(ventana_resultados, bg=self.color_fondo_ventana)
        filtros_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(filtros_frame, text=f"📅 Período: {fecha_inicio} - {fecha_fin}", 
                font=("Helvetica", 10, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w")
        tk.Label(filtros_frame, text=f"🍣 Producto: {producto_filtro} | 💳 Método de Pago: {pago_filtro}", 
                font=("Helvetica", 10), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w")
        
        # Métricas filtradas
        total_ventas = len(ventas_filtradas)
        ingresos_totales = sum(v['total_final'] for v in ventas_filtradas)
        descuentos_totales = sum(v['descuento_aplicado'] for v in ventas_filtradas)
        
        metricas_frame = tk.Frame(ventana_resultados, bg=self.color_fondo_ventana)
        metricas_frame.pack(fill="x", padx=20, pady=10)
        
        metricas_texto = f"📈 {total_ventas} ventas | 💰 ${ingresos_totales:.2f} ingresos | 🎁 ${descuentos_totales:.2f} descuentos"
        tk.Label(metricas_frame, text=metricas_texto, font=("Helvetica", 12, "bold"), 
                bg=self.color_fondo_ventana, fg="#4CAF50").pack()
        
        # Tabla de resultados
        tabla_frame = tk.Frame(ventana_resultados, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        tree = ttk.Treeview(tabla_frame, columns=("ID", "Fecha", "Productos", "Oferta", "Descuento", "Total", "Pago"), 
                           show="headings", height=15)
        
        columnas = [("ID", 80), ("Fecha", 130), ("Productos", 180), ("Oferta", 120), 
                   ("Descuento", 100), ("Total", 100), ("Pago", 80)]
        
        for col, ancho in columnas:
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center" if col in ["ID", "Descuento", "Total", "Pago"] else "w")
        
        # Llenar tabla
        for venta in sorted(ventas_filtradas, key=lambda x: x['fecha'], reverse=True):
            fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            productos_texto = ", ".join([f"{p['nombre']} x{p['cantidad']}" for p in venta['productos']])
            if len(productos_texto) > 25:
                productos_texto = productos_texto[:22] + "..."
            
            tree.insert("", "end", values=(
                venta['id'], fecha_formateada, productos_texto,
                venta['oferta_aplicada'] or "Sin oferta",
                f"${venta['descuento_aplicado']:.2f}",
                f"${venta['total_final']:.2f}",
                venta.get('metodo_pago', 'N/A')
            ))
        
        # Scrollbars
        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botones
        botones_frame = tk.Frame(ventana_resultados, bg=self.color_fondo_ventana)
        botones_frame.pack(pady=20)
        
        tamaños = self.calcular_tamaños_responsivos()
        if REPORTLAB_DISPONIBLE:
            tk.Button(botones_frame, text="📄 Exportar Filtrados PDF", 
                     command=lambda: self.exportar_filtrados_pdf(ventas_filtradas),
                     bg="#FF9800", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                     relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], 
                     pady=tamaños['boton_gestion_pady']).pack(side="left", padx=10)
        
        tk.Button(botones_frame, text="❌ Cerrar", command=ventana_resultados.destroy,
                 bg="#F44336", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], 
                 pady=tamaños['boton_gestion_pady']).pack(side="left", padx=10)
    
    def actualizar_graficos_reportes(self):
        """Actualiza los gráficos y recalcula estadísticas"""
        try:
            # Recargar la vista de reportes para actualizar datos
            self.mostrar_reportes()
            messagebox.showinfo("Actualizado", "Los gráficos y estadísticas han sido actualizados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar gráficos: {str(e)}")
    
    def limpiar_filtros_reportes(self):
        """Limpia todos los filtros y resetea los valores por defecto"""
        try:
            # Resetear campos de fecha
            self.fecha_inicio.delete(0, tk.END)
            self.fecha_inicio.insert(0, "2025-09-25")
            
            self.fecha_fin.delete(0, tk.END)
            self.fecha_fin.insert(0, "2025-09-27")
            
            # Resetear campo de producto
            self.filtro_producto.delete(0, tk.END)
            
            # Actualizar mensaje de estado
            if hasattr(self, 'status_label'):
                self.status_label.config(text="🔄 Filtros limpiados - Listos para nueva búsqueda", fg="#FF9800")
                
            messagebox.showinfo("Filtros Limpiados", "Todos los filtros han sido limpiados y resetados a valores por defecto")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al limpiar filtros: {str(e)}")
    
    def actualizar_tabla_ventas(self, tree):
        """Actualiza la tabla de ventas con los datos más recientes"""
        try:
            # Limpiar tabla actual
            for item in tree.get_children():
                tree.delete(item)
            
            # Recargar datos de ventas
            for venta in sorted(self.ventas, key=lambda x: x['fecha'], reverse=True):
                fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                productos_texto = ", ".join([f"{p['nombre']} x{p['cantidad']}" for p in venta['productos']])
                if len(productos_texto) > 30:
                    productos_texto = productos_texto[:27] + "..."
                
                oferta_texto = venta['oferta_aplicada'] if venta['oferta_aplicada'] else "Sin oferta"
                descuento_texto = f"${venta['descuento_aplicado']:.2f}"
                total_texto = f"${venta['total_final']:.2f}"
                
                tree.insert("", "end", values=(
                    venta['id'], fecha_formateada, productos_texto, 
                    oferta_texto, descuento_texto, total_texto
                ))
            
            # Actualizar mensaje de estado
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"✅ Lista actualizada - {len(self.ventas)} ventas cargadas", fg="#4CAF50")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar tabla: {str(e)}")
    
    def ver_detalle_venta_seleccionada(self, tree):
        """Muestra los detalles de la venta seleccionada en la tabla"""
        try:
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Selección", "Por favor selecciona una venta de la lista")
                return
            
            item = tree.item(seleccion[0])
            venta_id = item['values'][0]
            
            # Buscar la venta por ID
            venta_detalle = None
            for venta in self.ventas:
                if venta['id'] == venta_id:
                    venta_detalle = venta
                    break
            
            if not venta_detalle:
                messagebox.showerror("Error", "No se pudo encontrar la venta seleccionada")
                return
            
            # Crear ventana de detalles
            ventana_detalle = tk.Toplevel(self)
            ventana_detalle.title(f"Detalle de Venta #{venta_id}")
            ventana_detalle.geometry("600x500")
            ventana_detalle.configure(bg=self.color_fondo_ventana)
            
            # Título
            titulo_frame = tk.Frame(ventana_detalle, bg="#3F51B5", relief="raised", bd=2)
            titulo_frame.pack(fill="x", pady=(0, 20))
            tk.Label(titulo_frame, text=f"🧾 DETALLE DE VENTA #{venta_id}", 
                    font=("Arial", 16, "bold"), bg="#3F51B5", fg="white", 
                    pady=10).pack()
            
            # Información general
            info_frame = tk.LabelFrame(ventana_detalle, text="Información General", 
                                     font=("Arial", 12, "bold"), bg=self.color_fondo_ventana)
            info_frame.pack(fill="x", padx=20, pady=10)
            
            fecha_formateada = datetime.datetime.strptime(venta_detalle['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
            tk.Label(info_frame, text=f"📅 Fecha: {fecha_formateada}", 
                    font=("Arial", 11), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=2)
            tk.Label(info_frame, text=f"💳 Método de Pago: {venta_detalle.get('metodo_pago', 'No especificado')}", 
                    font=("Arial", 11), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", pady=2)
            
            # Productos
            productos_frame = tk.LabelFrame(ventana_detalle, text="Productos Vendidos", 
                                          font=("Arial", 12, "bold"), bg=self.color_fondo_ventana)
            productos_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Lista de productos
            for i, producto in enumerate(venta_detalle['productos'], 1):
                producto_frame = tk.Frame(productos_frame, bg="#F5F5F5", relief="raised", bd=1)
                producto_frame.pack(fill="x", pady=2, padx=5)
                
                tk.Label(producto_frame, text=f"{i}. {producto['nombre']}", 
                        font=("Arial", 11, "bold"), bg="#F5F5F5").pack(side="left", padx=5)
                tk.Label(producto_frame, text=f"Cantidad: {producto['cantidad']}", 
                        font=("Arial", 10), bg="#F5F5F5").pack(side="left", padx=10)
                tk.Label(producto_frame, text=f"Precio: ${producto['precio']:.2f}", 
                        font=("Arial", 10), bg="#F5F5F5").pack(side="right", padx=5)
            
            # Resumen financiero
            resumen_frame = tk.LabelFrame(ventana_detalle, text="Resumen Financiero", 
                                        font=("Arial", 12, "bold"), bg=self.color_fondo_ventana)
            resumen_frame.pack(fill="x", padx=20, pady=10)
            
            subtotal = sum(p['precio'] * p['cantidad'] for p in venta_detalle['productos'])
            tk.Label(resumen_frame, text=f"Subtotal: ${subtotal:.2f}", 
                    font=("Arial", 11), bg=self.color_fondo_ventana).pack(anchor="w", pady=2)
            tk.Label(resumen_frame, text=f"Descuento Aplicado: ${venta_detalle['descuento_aplicado']:.2f}", 
                    font=("Arial", 11), bg=self.color_fondo_ventana, fg="#FF5722").pack(anchor="w", pady=2)
            tk.Label(resumen_frame, text=f"TOTAL FINAL: ${venta_detalle['total_final']:.2f}", 
                    font=("Arial", 12, "bold"), bg=self.color_fondo_ventana, fg="#4CAF50").pack(anchor="w", pady=5)
            
            if venta_detalle['oferta_aplicada']:
                tk.Label(resumen_frame, text=f"🎁 Oferta: {venta_detalle['oferta_aplicada']}", 
                        font=("Arial", 10), bg=self.color_fondo_ventana, fg="#9C27B0").pack(anchor="w", pady=2)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar detalles: {str(e)}")
    
    def exportar_reporte_pdf(self):
        """Exporta el reporte completo de ventas a PDF"""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showerror("Error", "ReportLab no está disponible. Por favor instale: pip install reportlab")
            return
        
        try:
            # Seleccionar ubicación del archivo
            archivo_pdf = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Guardar Reporte de Ventas",
                initialfile=f"reporte_ventas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not archivo_pdf:
                return
                
            # Crear el documento PDF
            doc = SimpleDocTemplate(archivo_pdf, pagesize=A4)
            elementos = []
            estilos = getSampleStyleSheet()
            
            # Estilo personalizado para el título
            titulo_style = ParagraphStyle(
                'TituloPersonalizado',
                parent=estilos['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1,  # Centrado
                textColor=colors.darkblue
            )
            
            # Título del reporte
            titulo = Paragraph("🍣 MIZU SUSHI BAR - REPORTE DE VENTAS 🍣", titulo_style)
            elementos.append(titulo)
            elementos.append(Spacer(1, 20))
            
            # Información general
            fecha_generacion = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            info_general = Paragraph(f"<b>Fecha de generación:</b> {fecha_generacion}<br/>"
                                   f"<b>Período analizado:</b> {self.fecha_inicio.get()} - {self.fecha_fin.get()}", 
                                   estilos['Normal'])
            elementos.append(info_general)
            elementos.append(Spacer(1, 20))
            
            # Métricas principales
            total_ventas = len(self.ventas)
            ingresos_totales = sum(venta['total_final'] for venta in self.ventas)
            descuentos_totales = sum(venta['descuento_aplicado'] for venta in self.ventas)
            promedio_venta = ingresos_totales / total_ventas if total_ventas > 0 else 0
            
            metricas_texto = f"""
            <b>📊 MÉTRICAS PRINCIPALES</b><br/>
            • Total de ventas realizadas: {total_ventas}<br/>
            • Ingresos totales: ${ingresos_totales:,.2f}<br/>
            • Total en descuentos otorgados: ${descuentos_totales:,.2f}<br/>
            • Promedio por venta: ${promedio_venta:,.2f}<br/>
            • Tasa de conversión con ofertas: {((total_ventas - sum(1 for v in self.ventas if not v['oferta_aplicada'])) / total_ventas * 100) if total_ventas > 0 else 0:.1f}%
            """
            
            metricas = Paragraph(metricas_texto, estilos['Normal'])
            elementos.append(metricas)
            elementos.append(Spacer(1, 30))
            
            # Tabla detallada de ventas
            elementos.append(Paragraph("<b>📋 DETALLE DE VENTAS</b>", estilos['Heading2']))
            elementos.append(Spacer(1, 12))
            
            # Datos de la tabla
            datos_tabla = [['ID Venta', 'Fecha/Hora', 'Productos', 'Oferta', 'Descuento', 'Total', 'Método Pago']]
            
            for venta in sorted(self.ventas, key=lambda x: x['fecha'], reverse=True):
                fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')
                productos_texto = ", ".join([f"{p['nombre']} x{p['cantidad']}" for p in venta['productos']])
                if len(productos_texto) > 40:
                    productos_texto = productos_texto[:37] + "..."
                
                datos_tabla.append([
                    venta['id'],
                    fecha_formateada,
                    productos_texto,
                    venta['oferta_aplicada'] or "Sin oferta",
                    f"${venta['descuento_aplicado']:.2f}",
                    f"${venta['total_final']:.2f}",
                    venta.get('metodo_pago', 'N/A')
                ])
            
            # Crear y estilizar tabla
            tabla = Table(datos_tabla, repeatRows=1)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elementos.append(tabla)
            elementos.append(Spacer(1, 30))
            
            # Análisis por productos
            productos_stats = {}
            for venta in self.ventas:
                for producto in venta['productos']:
                    nombre = producto['nombre']
                    if nombre not in productos_stats:
                        productos_stats[nombre] = {'cantidad': 0, 'ingresos': 0}
                    productos_stats[nombre]['cantidad'] += producto['cantidad']
                    productos_stats[nombre]['ingresos'] += producto['subtotal']
            
            elementos.append(Paragraph("<b>🍣 ANÁLISIS POR PRODUCTO</b>", estilos['Heading2']))
            elementos.append(Spacer(1, 12))
            
            productos_ordenados = sorted(productos_stats.items(), key=lambda x: x[1]['ingresos'], reverse=True)
            datos_productos = [['Producto', 'Cantidad Vendida', 'Ingresos Generados', '% del Total']]
            
            for producto, stats in productos_ordenados:
                porcentaje = (stats['ingresos'] / ingresos_totales * 100) if ingresos_totales > 0 else 0
                datos_productos.append([
                    producto,
                    str(stats['cantidad']),
                    f"${stats['ingresos']:,.2f}",
                    f"{porcentaje:.1f}%"
                ])
            
            tabla_productos = Table(datos_productos, repeatRows=1)
            tabla_productos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elementos.append(tabla_productos)
            elementos.append(Spacer(1, 20))
            
            # Pie de página
            pie_pagina = Paragraph(
                f"<i>Reporte generado automáticamente por Mizu Sushi Bar System v1.0<br/>"
                f"© 2025 - Todos los derechos reservados</i>", 
                estilos['Normal']
            )
            elementos.append(pie_pagina)
            
            # Generar PDF
            doc.build(elementos)
            
            # Confirmar éxito
            messagebox.showinfo("Éxito", f"Reporte PDF generado exitosamente:\n{archivo_pdf}")
            
            # Preguntar si desea abrir el archivo
            if messagebox.askyesno("Abrir PDF", "¿Desea abrir el reporte generado?"):
                try:
                    os.startfile(archivo_pdf)  # Windows
                except:
                    try:
                        os.system(f"open {archivo_pdf}")  # macOS
                    except:
                        os.system(f"xdg-open {archivo_pdf}")  # Linux
                        
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")
    
    def exportar_filtrados_pdf(self, ventas_filtradas):
        """Exporta las ventas filtradas a PDF"""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showerror("Error", "ReportLab no está disponible.")
            return
        
        try:
            archivo_pdf = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Guardar Reporte Filtrado",
                initialfile=f"reporte_filtrado_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not archivo_pdf:
                return
            
            # Similar al reporte completo pero solo con ventas filtradas
            doc = SimpleDocTemplate(archivo_pdf, pagesize=A4)
            elementos = []
            estilos = getSampleStyleSheet()
            
            titulo_style = ParagraphStyle('TituloFiltrado', parent=estilos['Heading1'],
                                        fontSize=20, spaceAfter=20, alignment=1, textColor=colors.purple)
            
            titulo = Paragraph("🍣 REPORTE DE VENTAS FILTRADO 🍣", titulo_style)
            elementos.append(titulo)
            elementos.append(Spacer(1, 15))
            
            # Información del filtro
            info_filtro = Paragraph(f"<b>Filtros aplicados:</b><br/>"
                                  f"• Período: {self.fecha_inicio.get()} - {self.fecha_fin.get()}<br/>"
                                  f"• Producto: {self.filtro_producto.get()}<br/>"
                                  f"• Método de pago: {self.filtro_pago.get()}<br/>"
                                  f"• Resultados encontrados: {len(ventas_filtradas)} ventas", 
                                  estilos['Normal'])
            elementos.append(info_filtro)
            elementos.append(Spacer(1, 20))
            
            # Métricas filtradas
            ingresos_filtrados = sum(v['total_final'] for v in ventas_filtradas)
            descuentos_filtrados = sum(v['descuento_aplicado'] for v in ventas_filtradas)
            
            metricas_filtro = Paragraph(f"<b>📊 RESUMEN:</b><br/>"
                                      f"Ingresos totales: ${ingresos_filtrados:,.2f}<br/>"
                                      f"Descuentos aplicados: ${descuentos_filtrados:,.2f}<br/>"
                                      f"Promedio por venta: ${(ingresos_filtrados/len(ventas_filtradas)) if ventas_filtradas else 0:.2f}", 
                                      estilos['Normal'])
            elementos.append(metricas_filtro)
            elementos.append(Spacer(1, 20))
            
            # Tabla de resultados filtrados
            datos_filtrados = [['ID', 'Fecha/Hora', 'Productos', 'Total', 'Método Pago']]
            
            for venta in sorted(ventas_filtradas, key=lambda x: x['fecha'], reverse=True):
                fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')
                productos_texto = ", ".join([f"{p['nombre']} x{p['cantidad']}" for p in venta['productos']])
                if len(productos_texto) > 45:
                    productos_texto = productos_texto[:42] + "..."
                
                datos_filtrados.append([
                    venta['id'],
                    fecha_formateada,
                    productos_texto,
                    f"${venta['total_final']:.2f}",
                    venta.get('metodo_pago', 'N/A')
                ])
            
            tabla_filtrada = Table(datos_filtrados, repeatRows=1)
            tabla_filtrada.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elementos.append(tabla_filtrada)
            
            doc.build(elementos)
            messagebox.showinfo("Éxito", f"Reporte filtrado generado: {archivo_pdf}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF filtrado: {str(e)}")
    
    def backup_datos_reportes(self):
        """Crea backup de los datos de ventas y configuración"""
        try:
            fecha_backup = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            archivo_backup = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Guardar Backup de Datos",
                initialfile=f"backup_sushi_datos_{fecha_backup}.json"
            )
            
            if not archivo_backup:
                return
            
            # Datos a respaldar
            datos_backup = {
                "fecha_backup": datetime.datetime.now().isoformat(),
                "version_sistema": "1.0",
                "ventas": self.ventas,
                "ofertas": self.ofertas,
                "configuracion": {
                    "tema_actual": self.tema_actual.get(),
                    "rol_usuario": self.rol_usuario.get()
                }
            }
            
            # Guardar en archivo JSON
            with open(archivo_backup, 'w', encoding='utf-8') as f:
                json.dump(datos_backup, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Backup Exitoso", 
                              f"Backup guardado exitosamente:\n{archivo_backup}\n\n"
                              f"Datos incluidos:\n"
                              f"• {len(self.ventas)} ventas\n"
                              f"• {len(self.ofertas)} ofertas\n"
                              f"• Configuración del sistema")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear backup: {str(e)}")
    
    def restaurar_datos_reportes(self):
        """Restaura datos desde un archivo de backup"""
        try:
            archivo_backup = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json")],
                title="Seleccionar Archivo de Backup"
            )
            
            if not archivo_backup:
                return
            
            # Confirmar restauración
            if not messagebox.askyesno("Confirmar Restauración", 
                                     "¿Está seguro de que desea restaurar los datos?\n"
                                     "Esto reemplazará todos los datos actuales."):
                return
            
            # Leer archivo de backup
            with open(archivo_backup, 'r', encoding='utf-8') as f:
                datos_backup = json.load(f)
            
            # Validar estructura del backup
            if not all(key in datos_backup for key in ['ventas', 'ofertas', 'configuracion']):
                messagebox.showerror("Error", "El archivo de backup no tiene el formato correcto")
                return
            
            # Restaurar datos
            self.ventas = datos_backup['ventas']
            self.ofertas = datos_backup['ofertas']
            
            if 'configuracion' in datos_backup:
                config = datos_backup['configuracion']
                if 'tema_actual' in config:
                    self.tema_actual.set(config['tema_actual'])
                    self.aplicar_tema(config['tema_actual'])
            
            messagebox.showinfo("Restauración Exitosa", 
                              f"Datos restaurados exitosamente:\n"
                              f"• {len(self.ventas)} ventas\n"
                              f"• {len(self.ofertas)} ofertas\n"
                              f"• Configuración del sistema")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al restaurar backup: {str(e)}")
    
    def generar_analisis_comparativo(self):
        """Genera análisis comparativo entre períodos"""
        ventana_comparativo = tk.Toplevel(self)
        ventana_comparativo.title("Análisis Comparativo")
        ventana_comparativo.geometry("800x600")
        ventana_comparativo.configure(bg=self.color_fondo_ventana)
        
        # Título
        titulo_frame = tk.Frame(ventana_comparativo, bg="#9C27B0", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="📊 ANÁLISIS COMPARATIVO DE PERÍODOS", 
                font=("Impact", 16, "bold"), bg="#9C27B0", fg="white", 
                pady=10).pack()
        
        # Frame para selección de períodos
        periodos_frame = tk.Frame(ventana_comparativo, bg=self.color_fondo_ventana)
        periodos_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(periodos_frame, text="Seleccione los períodos a comparar:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(anchor="w")
        
        # Período 1
        periodo1_frame = tk.Frame(periodos_frame, bg=self.color_fondo_ventana)
        periodo1_frame.pack(fill="x", pady=5)
        tk.Label(periodo1_frame, text="Período 1 - Desde:", bg=self.color_fondo_ventana).pack(side="left")
        fecha1_inicio = tk.Entry(periodo1_frame, width=12)
        fecha1_inicio.pack(side="left", padx=5)
        fecha1_inicio.insert(0, "2025-09-25")
        tk.Label(periodo1_frame, text="Hasta:", bg=self.color_fondo_ventana).pack(side="left", padx=(20,5))
        fecha1_fin = tk.Entry(periodo1_frame, width=12)
        fecha1_fin.pack(side="left", padx=5)
        fecha1_fin.insert(0, "2025-09-25")
        
        # Período 2
        periodo2_frame = tk.Frame(periodos_frame, bg=self.color_fondo_ventana)
        periodo2_frame.pack(fill="x", pady=5)
        tk.Label(periodo2_frame, text="Período 2 - Desde:", bg=self.color_fondo_ventana).pack(side="left")
        fecha2_inicio = tk.Entry(periodo2_frame, width=12)
        fecha2_inicio.pack(side="left", padx=5)
        fecha2_inicio.insert(0, "2025-09-26")
        tk.Label(periodo2_frame, text="Hasta:", bg=self.color_fondo_ventana).pack(side="left", padx=(20,5))
        fecha2_fin = tk.Entry(periodo2_frame, width=12)
        fecha2_fin.pack(side="left", padx=5)
        fecha2_fin.insert(0, "2025-09-26")
        
        def realizar_comparacion():
            try:
                # Filtrar ventas por períodos
                periodo1_ventas = self._filtrar_ventas_por_fecha(fecha1_inicio.get(), fecha1_fin.get())
                periodo2_ventas = self._filtrar_ventas_por_fecha(fecha2_inicio.get(), fecha2_fin.get())
                
                # Mostrar resultados comparativos
                self._mostrar_resultados_comparativos(ventana_comparativo, periodo1_ventas, periodo2_ventas, 
                                                    fecha1_inicio.get(), fecha1_fin.get(), 
                                                    fecha2_inicio.get(), fecha2_fin.get())
            except Exception as e:
                messagebox.showerror("Error", f"Error en comparación: {str(e)}")
        
        # Botón comparar
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(periodos_frame, text="🔍 Comparar Períodos", command=realizar_comparacion,
                 bg="#9C27B0", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], 
                 pady=tamaños['boton_gestion_pady']).pack(pady=20)
    
    def _filtrar_ventas_por_fecha(self, fecha_inicio, fecha_fin):
        """Filtra ventas por rango de fechas"""
        fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        ventas_filtradas = []
        for venta in self.ventas:
            fecha_venta = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
            if fecha_inicio_dt.date() <= fecha_venta.date() <= fecha_fin_dt.date():
                ventas_filtradas.append(venta)
        
        return ventas_filtradas
    
    def _mostrar_resultados_comparativos(self, parent, ventas1, ventas2, fecha1_ini, fecha1_fin, fecha2_ini, fecha2_fin):
        """Muestra los resultados del análisis comparativo"""
        # Limpiar contenido anterior
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Frame) and widget != parent.winfo_children()[0]:  # Mantener título
                widget.destroy()
        
        # Frame para resultados
        resultados_frame = tk.Frame(parent, bg=self.color_fondo_ventana)
        resultados_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Calcular métricas de ambos períodos
        metricas1 = self._calcular_metricas_periodo(ventas1)
        metricas2 = self._calcular_metricas_periodo(ventas2)
        
        # Mostrar comparación
        tk.Label(resultados_frame, text="📈 RESULTADOS COMPARATIVOS", 
                font=("Helvetica", 14, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(0,20))
        
        # Tabla comparativa
        tree = ttk.Treeview(resultados_frame, columns=("Métrica", "Período1", "Período2", "Diferencia"), 
                           show="headings", height=10)
        
        for col in ["Métrica", "Período1", "Período2", "Diferencia"]:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        # Datos comparativos
        comparaciones = [
            ("Número de Ventas", metricas1['ventas'], metricas2['ventas']),
            ("Ingresos Totales", f"${metricas1['ingresos']:.2f}", f"${metricas2['ingresos']:.2f}"),
            ("Promedio por Venta", f"${metricas1['promedio']:.2f}", f"${metricas2['promedio']:.2f}"),
            ("Total Descuentos", f"${metricas1['descuentos']:.2f}", f"${metricas2['descuentos']:.2f}"),
            ("Ventas con Oferta", f"{metricas1['con_oferta']}", f"{metricas2['con_oferta']}")
        ]
        
        for metrica, valor1, valor2 in comparaciones:
            if metrica == "Número de Ventas":
                diferencia = metricas2['ventas'] - metricas1['ventas']
                diferencia_texto = f"{diferencia:+d}"
            elif "Ventas con Oferta" in metrica:
                diferencia = metricas2['con_oferta'] - metricas1['con_oferta']
                diferencia_texto = f"{diferencia:+d}"
            else:
                # Para valores monetarios - usar mapeo específico
                if metrica == "Ingresos Totales":
                    val1 = metricas1['ingresos']
                    val2 = metricas2['ingresos']
                elif metrica == "Promedio por Venta":
                    val1 = metricas1['promedio']
                    val2 = metricas2['promedio']
                elif metrica == "Total Descuentos":
                    val1 = metricas1['descuentos']
                    val2 = metricas2['descuentos']
                else:
                    val1 = val2 = 0  # fallback
                    
                diferencia = val2 - val1
                diferencia_texto = f"${diferencia:+.2f}"
            
            tree.insert("", "end", values=(metrica, valor1, valor2, diferencia_texto))
        
        tree.pack(expand=True, fill="both")
    
    def _calcular_metricas_periodo(self, ventas):
        """Calcula métricas para un período específico"""
        total_ventas = len(ventas)
        ingresos = sum(v['total_final'] for v in ventas)
        descuentos = sum(v['descuento_aplicado'] for v in ventas)
        promedio = ingresos / total_ventas if total_ventas > 0 else 0
        con_oferta = len([v for v in ventas if v['oferta_aplicada']])
        
        return {
            'ventas': total_ventas,
            'ingresos': ingresos,
            'descuentos': descuentos,
            'promedio': promedio,
            'con_oferta': con_oferta
        }
    
    def mostrar_alertas_inteligentes(self):
        """Muestra alertas basadas en patrones de venta"""
        ventana_alertas = tk.Toplevel(self)
        ventana_alertas.title("Alertas Inteligentes")
        ventana_alertas.geometry("700x500")
        ventana_alertas.configure(bg=self.color_fondo_ventana)
        
        # Título
        titulo_frame = tk.Frame(ventana_alertas, bg="#FF5722", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="🚨 ALERTAS INTELIGENTES DEL SISTEMA", 
                font=("Impact", 16, "bold"), bg="#FF5722", fg="white", 
                pady=10).pack()
        
        # Frame para alertas
        alertas_frame = tk.Frame(ventana_alertas, bg=self.color_fondo_ventana)
        alertas_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Generar alertas automáticas
        alertas = self._generar_alertas_automaticas()
        
        if not alertas:
            tk.Label(alertas_frame, text="✅ No hay alertas críticas en este momento", 
                    font=("Helvetica", 14), bg=self.color_fondo_ventana, fg="#4CAF50").pack(expand=True)
        else:
            for i, alerta in enumerate(alertas):
                alerta_frame = tk.Frame(alertas_frame, bg=alerta['color'], relief="raised", bd=2)
                alerta_frame.pack(fill="x", pady=10, padx=10)
                
                tk.Label(alerta_frame, text=alerta['icono'] + " " + alerta['titulo'], 
                        font=("Helvetica", 12, "bold"), bg=alerta['color'], fg="white").pack(anchor="w", padx=15, pady=5)
                tk.Label(alerta_frame, text=alerta['descripcion'], 
                        font=("Helvetica", 10), bg=alerta['color'], fg="white",
                        wraplength=600, justify="left").pack(anchor="w", padx=15, pady=(0,10))
    
    def _generar_alertas_automaticas(self):
        """Genera alertas automáticas basadas en análisis de datos"""
        alertas = []
        
        # Analizar productos por ventas
        productos_stats = {}
        for venta in self.ventas:
            for producto in venta['productos']:
                nombre = producto['nombre']
                if nombre not in productos_stats:
                    productos_stats[nombre] = 0
                productos_stats[nombre] += producto['cantidad']
        
        if productos_stats:
            producto_menos_vendido = min(productos_stats, key=productos_stats.get)
            producto_mas_vendido = max(productos_stats, key=productos_stats.get)
            
            # Alerta por producto poco vendido
            if productos_stats[producto_menos_vendido] < 2:
                alertas.append({
                    'icono': '⚠️',
                    'titulo': 'Producto con Pocas Ventas',
                    'descripcion': f'"{producto_menos_vendido}" solo ha vendido {productos_stats[producto_menos_vendido]} unidades. Considere revisar el precio o promocionarlo.',
                    'color': '#FF9800'
                })
            
            # Alerta por producto muy exitoso
            if productos_stats[producto_mas_vendido] > 5:
                alertas.append({
                    'icono': '🌟',
                    'titulo': 'Producto Estrella Detectado',
                    'descripcion': f'"{producto_mas_vendido}" ha vendido {productos_stats[producto_mas_vendido]} unidades. ¡Considere crear ofertas especiales o aumentar el stock!',
                    'color': '#4CAF50'
                })
        
        # Alerta por descuentos altos
        descuentos_totales = sum(v['descuento_aplicado'] for v in self.ventas)
        ingresos_totales = sum(v['total_final'] for v in self.ventas)
        if ingresos_totales > 0 and (descuentos_totales / ingresos_totales) > 0.15:
            alertas.append({
                'icono': '💰',
                'titulo': 'Alto Nivel de Descuentos',
                'descripcion': f'Los descuentos representan el {(descuentos_totales/ingresos_totales)*100:.1f}% de las ventas. Considere revisar la estrategia de ofertas.',
                'color': '#F44336'
            })
        
        # Alerta por métodos de pago
        pagos_efectivo = len([v for v in self.ventas if v.get('metodo_pago') == 'efectivo'])
        if pagos_efectivo / len(self.ventas) > 0.7:
            alertas.append({
                'icono': '💳',
                'titulo': 'Predomina el Pago en Efectivo',
                'descripcion': f'{(pagos_efectivo/len(self.ventas))*100:.1f}% de los pagos son en efectivo. Considere promover pagos con tarjeta.',
                'color': '#2196F3'
            })
        
        return alertas

    # --- 4. Opciones de Configuración ---
    def mostrar_configuracion(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Configuración del Sistema ⚙️", style="Titulo.TLabel").pack(pady=(0, 20))
        tamaños = self.calcular_tamaños_responsivos()
        
        # Configuraciones básicas
        ttk.Button(frame, text="🔑 Cambiar Contraseña", width=tamaños['boton_width'], command=self.mostrar_cambiar_password).pack(pady=tamaños['espaciado_botones'])
        ttk.Button(frame, text="🎨 Configurar Tema", width=tamaños['boton_width'], command=self.mostrar_configurar_tema).pack(pady=tamaños['espaciado_botones'])
        
        # Configuraciones de datos básicas
        ttk.Button(frame, text="💾 Respaldar Base de Datos", width=tamaños['boton_width'], command=self.respaldar_bd_simple).pack(pady=tamaños['espaciado_botones'])
        ttk.Button(frame, text="📂 Restaurar Base de Datos", width=tamaños['boton_width'], command=self.mostrar_restaurar_bd_simple).pack(pady=tamaños['espaciado_botones'])
        
        # Nota informativa
        info_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="ridge", bd=2)
        info_frame.pack(fill="x", padx=50, pady=20)
        
        tk.Label(info_frame, text="� FUNCIONES AVANZADAS", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(10, 5))
        
        tk.Label(info_frame, text="Las funciones de backup de reportes, análisis comparativo\ny alertas inteligentes ahora se encuentran en:", 
                font=("Helvetica", 10), bg=self.color_fondo_ventana, fg=self.color_texto).pack(pady=(0, 5))
        
        tk.Label(info_frame, text="� Reportes de Ventas → Pestaña 'Gestión de Datos'", 
                font=("Helvetica", 11, "bold"), bg=self.color_fondo_ventana, fg="#2196F3").pack(pady=(0, 15))
        
        ttk.Button(frame, text="⬅️ Regresar", width=tamaños['boton_width'], command=self.mostrar_menu_principal).pack(pady=25)

    def mostrar_cambiar_password(self):
        """Vista para cambiar contraseña"""
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Cambiar Contraseña 🔑", style="Titulo.TLabel").pack(pady=(0, 20))

        # Frame para el formulario
        form_frame = ttk.Frame(frame)
        form_frame.pack(pady=20)

        ttk.Label(form_frame, text="Contraseña actual:", style="Subtitulo.TLabel").pack(anchor="w", pady=(10, 2))
        actual_entry = ttk.Entry(form_frame, show="*", width=40)
        actual_entry.pack(pady=(0, 10))

        ttk.Label(form_frame, text="Nueva contraseña:", style="Subtitulo.TLabel").pack(anchor="w", pady=(10, 2))
        nueva_entry = ttk.Entry(form_frame, show="*", width=40)
        nueva_entry.pack(pady=(0, 10))

        ttk.Label(form_frame, text="Confirmar nueva contraseña:", style="Subtitulo.TLabel").pack(anchor="w", pady=(10, 2))
        confirmar_entry = ttk.Entry(form_frame, show="*", width=40)
        confirmar_entry.pack(pady=(0, 10))

        # Indicador de fortaleza
        fortaleza_label = ttk.Label(form_frame, text="")
        fortaleza_label.pack(pady=10)

        def verificar_fortaleza(*args):
            password = nueva_entry.get()
            if len(password) < 4:
                fortaleza_label.config(text="❌ Muy débil", foreground="red")
            elif len(password) < 8:
                fortaleza_label.config(text="⚠️ Débil", foreground="orange")
            else:
                fortaleza_label.config(text="✅ Fuerte", foreground="green")

        nueva_entry.bind('<KeyRelease>', verificar_fortaleza)

        def cambiar_password():
            from tkinter import messagebox
            actual = actual_entry.get()
            nueva = nueva_entry.get()
            confirmar = confirmar_entry.get()

            if not actual or not nueva or not confirmar:
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return

            if nueva != confirmar:
                messagebox.showerror("Error", "Las contraseñas nuevas no coinciden")
                return

            if len(nueva) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return

            messagebox.showinfo("Éxito", "Contraseña cambiada exitosamente")
            self.mostrar_configuracion()

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="💾 Guardar Cambios", command=cambiar_password, width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.mostrar_configuracion, width=20).pack(side="left", padx=5)

    def mostrar_configurar_tema(self):
        """Vista avanzada para configurar temas con preview en tiempo real"""
        frame = self.limpiar_ventana()
        
        # Título
        titulo_frame = tk.Frame(frame, bg="#673AB7", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="🎨 Configurar Tema Visual 🎨", 
                font=("Impact", 20, "bold"), bg="#673AB7", fg="white", 
                pady=12).pack()

        # Variable para tema actual
        tema_var = tk.StringVar(value=self.tema_actual.get())

        # Frame principal dividido en dos columnas
        main_container = tk.Frame(frame, bg=self.color_fondo_ventana)
        main_container.pack(expand=True, fill="both", padx=20)
        
        # Columna izquierda - Selección de tema
        left_column = tk.Frame(main_container, bg=self.color_fondo_ventana)
        left_column.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(left_column, text="Selecciona el tema:", 
                font=("Helvetica", 14, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=(0, 15))

        # Información del tema automático
        import datetime
        hora_actual = datetime.datetime.now().hour
        tema_auto = self.obtener_tema_automatico()
        info_automatico = f"Automático detectará: {tema_auto}\n(Hora actual: {hora_actual:02d}:00)"
        
        temas_info = [
            ("🌞 Claro", "Claro", "Tema diurno con colores claros y suaves"),
            ("🌙 Oscuro", "Oscuro", "Tema nocturno con colores oscuros"),
            (f"🔄 Automático", "Automatico", info_automatico)
        ]
        
        def actualizar_preview(*args):
            self.actualizar_vista_previa(preview_container, tema_var.get())
        
        # Radiobuttons con descripciones
        for texto, valor, descripcion in temas_info:
            tema_frame = tk.Frame(left_column, bg=self.color_fondo_ventana, relief="raised", bd=1)
            tema_frame.pack(fill="x", pady=8, padx=5)
            
            radio = tk.Radiobutton(tema_frame, text=texto, variable=tema_var, value=valor,
                                  bg=self.color_fondo_ventana, fg=self.color_texto, font=("Helvetica", 12, "bold"),
                                  command=actualizar_preview, activebackground=self.color_fondo_ventana)
            radio.pack(anchor="w", padx=10, pady=5)
            
            tk.Label(tema_frame, text=descripcion, 
                    font=("Helvetica", 10), bg=self.color_fondo_ventana, fg="#666666",
                    wraplength=200, justify="left").pack(anchor="w", padx=25, pady=(0, 10))
        
        # Columna derecha - Vista previa
        right_column = tk.Frame(main_container, bg=self.color_fondo_ventana, relief="raised", bd=2)
        right_column.pack(side="right", fill="both", expand=True)
        
        tk.Label(right_column, text="Vista Previa:", 
                font=("Helvetica", 14, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=15)

        # Contenedor de vista previa
        preview_container = tk.Frame(right_column, bg=self.color_fondo_ventana)
        preview_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Inicializar vista previa
        self.actualizar_vista_previa(preview_container, tema_var.get())
        
        def aplicar_tema_final():
            """Aplica el tema seleccionado definitivamente"""
            tema_seleccionado = tema_var.get()
            self.aplicar_tema(tema_seleccionado)
            
            # Refrescar la pantalla actual
            self.mostrar_configuracion()
            
            # Mostrar confirmación
            messagebox.showinfo("Éxito", 
                              f"✅ Tema '{tema_seleccionado}' aplicado correctamente\n\n"
                              f"El tema se ha aplicado a toda la aplicación.")

        # Botones finales
        btn_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(btn_frame, text="✅ Aplicar Tema", command=aplicar_tema_final,
                 bg="#4CAF50", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="left", padx=10)
        tk.Button(btn_frame, text="❌ Cancelar", command=self.mostrar_configuracion,
                 bg="#F44336", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="left", padx=10)

    def actualizar_vista_previa(self, container, tema_nombre):
        """Actualiza la vista previa del tema seleccionado"""
        # Limpiar preview anterior
        for widget in container.winfo_children():
            widget.destroy()
        
        # Obtener colores del tema
        colores = self.obtener_colores_tema(tema_nombre)
        
        # Crear preview simulado
        preview_frame = tk.Frame(container, bg=colores["COLOR_FONDO"], relief="raised", bd=3)
        preview_frame.pack(fill="both", expand=True)
        
        # Título del preview
        titulo_preview = tk.Label(preview_frame, text="🍣 MIZU SUSHI BAR 🍣", 
                                 font=("Impact", 16, "bold"), 
                                 bg=colores["COLOR_FONDO"], fg=colores["COLOR_TITULO"])
        titulo_preview.pack(pady=15)
        
        # Simulación de botones del menú
        botones_preview = tk.Frame(preview_frame, bg=colores["COLOR_FONDO"])
        botones_preview.pack(pady=10)
        
        # Botones de ejemplo
        ejemplos_botones = [
            ("🍣 Menú de Sushi", colores["COLOR_BOTON_FONDO"]),
            ("🎁 Ofertas", colores["COLOR_SECUNDARIO"]),
            ("⚙️ Configuración", colores["COLOR_INFO"])
        ]
        
        for texto, color_bg in ejemplos_botones:
            tamaños = self.calcular_tamaños_responsivos()
            btn_preview = tk.Button(botones_preview, text=texto,
                                   bg=color_bg, fg=colores["COLOR_BOTON_TEXTO"],
                                   font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                                   relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']//2,
                                   state="disabled")  # Deshabilitado para preview
            btn_preview.pack(pady=3)
        
        # Texto de ejemplo
        texto_preview = tk.Label(preview_frame, 
                                text=f"Tema: {tema_nombre}\nTexto de ejemplo en este tema",
                                font=("Helvetica", 11), 
                                bg=colores["COLOR_FONDO"], fg=colores["COLOR_TEXTO"])
        texto_preview.pack(pady=10)
        
        # Simulación de entrada de texto
        entry_frame = tk.Frame(preview_frame, bg=colores["COLOR_FONDO"])
        entry_frame.pack(pady=5)
        
        tk.Label(entry_frame, text="Campo de entrada:", 
                font=("Helvetica", 9), bg=colores["COLOR_FONDO"], fg=colores["COLOR_TEXTO"]).pack()
        
        # Simular entry con colores del tema
        entry_simulado = tk.Frame(entry_frame, bg=colores["COLOR_ENTRY_FONDO"], 
                                 relief="solid", bd=2, height=25)
        entry_simulado.pack(fill="x", padx=20, pady=3)
        tk.Label(entry_simulado, text="Texto de ejemplo", 
                font=("Helvetica", 10), bg=colores["COLOR_ENTRY_FONDO"], 
                fg=colores["COLOR_ENTRY_TEXTO"]).pack()
        
        # Simulación de tabla
        tabla_frame = tk.Frame(preview_frame, bg=colores["COLOR_FONDO"])
        tabla_frame.pack(pady=(10, 5), fill="x", padx=10)
        
        tk.Label(tabla_frame, text="Vista de tabla:", 
                font=("Helvetica", 9), bg=colores["COLOR_FONDO"], fg=colores["COLOR_TEXTO"]).pack()
        
        # Header de tabla simulado
        header_simulado = tk.Frame(tabla_frame, bg=colores["COLOR_TABLA_HEADER"], 
                                  relief="raised", bd=1)
        header_simulado.pack(fill="x", pady=1)
        tk.Label(header_simulado, text="ID | Nombre | Estado", 
                font=("Helvetica", 9, "bold"), bg=colores["COLOR_TABLA_HEADER"], 
                fg=colores["COLOR_TABLA_HEADER_TEXTO"], pady=3).pack()
        
        # Fila de tabla simulada
        fila_simulada = tk.Frame(tabla_frame, bg=colores["COLOR_TABLA_FONDO"], 
                                relief="solid", bd=1)
        fila_simulada.pack(fill="x")
        tk.Label(fila_simulada, text="001 | Producto Ejemplo | Activo", 
                font=("Helvetica", 9), bg=colores["COLOR_TABLA_FONDO"], 
                fg=colores["COLOR_TABLA_TEXTO"], pady=2).pack()
        
        # Información adicional del tema
        if tema_nombre == "Automatico":
            tema_efectivo = self.obtener_tema_automatico()
            info_extra = f"Se aplicará: {tema_efectivo}"
        else:
            info_extra = f"Tema fijo: {tema_nombre}"
            
        info_label = tk.Label(preview_frame, text=info_extra,
                             font=("Helvetica", 9, "italic"),
                             bg=colores["COLOR_FONDO"], fg="#999999")
        info_label.pack(pady=(10, 15))

    def respaldar_bd_simple(self):
        """Ventana simple de respaldando que se cierra automáticamente"""
        from tkinter import messagebox
        import tkinter as tk

        # Crear ventana modal
        ventana_respaldo = tk.Toplevel(self)
        ventana_respaldo.title("Respaldando...")
        ventana_respaldo.geometry("400x200")
        ventana_respaldo.configure(bg=self.color_fondo_ventana)
        ventana_respaldo.resizable(False, False)

        # Centrar la ventana
        ventana_respaldo.transient(self)
        ventana_respaldo.grab_set()

        # Contenido
        tk.Label(ventana_respaldo, text="💾", font=("Arial", 30), 
                 bg=self.color_fondo_ventana, fg="#4CAF50").pack(pady=20)

        tk.Label(ventana_respaldo, text="Respaldando Base de Datos", 
                 font=("Arial", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).pack()

        tk.Label(ventana_respaldo, text="Por favor espere...", 
                 font=("Arial", 12), bg=self.color_fondo_ventana, fg="#666").pack(pady=10)

        # Barra de progreso
        progress = ttk.Progressbar(ventana_respaldo, mode='indeterminate')
        progress.pack(pady=20, padx=50, fill="x")
        progress.start()

        def finalizar_respaldo():
            progress.stop()
            ventana_respaldo.destroy()
            messagebox.showinfo("Éxito", "✅ Base de datos respaldada correctamente\n\nUbicación: /backups/sushi_backup_2025-09-09.sql")

        # Cerrar automáticamente después de 3 segundos
        ventana_respaldo.after(3000, finalizar_respaldo)

    def mostrar_restaurar_bd_simple(self):
        """Vista visual simple para restaurar base de datos"""
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Restaurar Base de Datos 📂", style="Titulo.TLabel").pack(pady=(0, 20))

        # Frame de advertencia
        warning_frame = ttk.Frame(frame)
        warning_frame.pack(pady=20)

        ttk.Label(warning_frame, text="⚠️ ATENCIÓN", font=("Arial", 18, "bold"), foreground="#FF5722").pack()

        warning_text = """Esta operación reemplazará todos los datos actuales

🔹 Asegúrate de tener un respaldo reciente
🔹 La operación no se puede deshacer
🔹 Todos los usuarios serán desconectados"""

        ttk.Label(warning_frame, text=warning_text, justify="center").pack(pady=20)

        # Selector de archivo
        file_frame = ttk.Frame(frame)
        file_frame.pack(pady=20)

        ttk.Label(file_frame, text="Archivo de respaldo:", style="Subtitulo.TLabel").pack(anchor="w")

        entry_frame = ttk.Frame(file_frame)
        entry_frame.pack(fill="x", pady=5)

        file_entry = ttk.Entry(entry_frame, width=40)
        file_entry.pack(side="left", padx=(0, 10))
        file_entry.insert(0, "sushi_backup_2025-09-09.sql")

        ttk.Button(entry_frame, text="📁 Examinar", 
                   command=lambda: self._mostrar_selector_archivo()).pack(side="right")

        # Checkbox de confirmación
        confirm_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="✅ Entiendo los riesgos y deseo continuar", 
                       variable=confirm_var).pack(pady=20)

        def restaurar_bd():
            from tkinter import messagebox
            import tkinter as tk

            if not confirm_var.get():
                messagebox.showerror("Error", "Debe confirmar que entiende los riesgos")
                return

            resultado = messagebox.askyesno("⚠️ Confirmación Final", 
                                           "¿Está COMPLETAMENTE seguro?\n\n"
                                           "Esta acción eliminará todos los datos actuales "
                                           "y los reemplazará con el respaldo seleccionado.")
            if resultado:
                # Simular restauración
                ventana_restaurar = tk.Toplevel(self)
                ventana_restaurar.title("Restaurando...")
                ventana_restaurar.geometry("350x150")
                ventana_restaurar.configure(bg=self.color_fondo_ventana)
                ventana_restaurar.transient(self)
                ventana_restaurar.grab_set()

                tk.Label(ventana_restaurar, text="🔄", font=("Arial", 25), 
                         bg=self.color_fondo_ventana, fg="#FF9800").pack(pady=15)
                tk.Label(ventana_restaurar, text="Restaurando base de datos...", 
                         font=("Arial", 12, "bold"), bg=self.color_fondo_ventana).pack()

                progress = ttk.Progressbar(ventana_restaurar, mode='indeterminate')
                progress.pack(pady=15, padx=30, fill="x")
                progress.start()

                def finalizar():
                    progress.stop()
                    ventana_restaurar.destroy()
                    messagebox.showinfo("Éxito", "✅ Base de datos restaurada correctamente")
                    self.mostrar_configuracion()

                ventana_restaurar.after(2500, finalizar)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="🔄 Restaurar Ahora", command=restaurar_bd, width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.mostrar_configuracion, width=20).pack(side="left", padx=5)

    def _mostrar_selector_archivo(self):
        """Simula selector de archivo"""
        from tkinter import messagebox
        messagebox.showinfo("Selector de Archivos", "Funcionalidad de selector de archivos")

    def _crear_tabla(self, parent, columnas, datos):
        frame_tabla = ttk.Frame(parent)
        frame_tabla.pack(expand=True, fill="x", padx=10)
        scrollbar = ttk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")
        treeview = ttk.Treeview(frame_tabla, columns=columnas, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=treeview.yview)
        for col in columnas:
            treeview.heading(col, text=col)
            treeview.column(col, anchor="center", width=140)
        for dato in datos:
            treeview.insert("", "end", values=dato)
        treeview.pack(expand=True, fill="x")


if __name__ == "__main__":
    app = SushiApp()
    app.mainloop()
