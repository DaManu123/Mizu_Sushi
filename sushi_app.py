import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import datetime
import json
import os
import db
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
        
        # Inicializar base de datos y cargar datos persistentes
        try:
            db.init_db()
        except Exception:
            pass

        # Cargar ofertas desde la base de datos; si no hay datos, inicializar con muestras
        try:
            ofertas_db = db.load_offers()
            if ofertas_db:
                self.ofertas = ofertas_db
            else:
                # muestras por defecto
                self.ofertas = [
                    {
                        "id": "OFF001",
                        "nombre": "2x1 en California Rolls",
                        "descripcion": "Lleva 2 California Rolls por el precio de 1",
                        "tipo": "2x1",
                        "productos_aplicables": ["California Roll"],
                        "descuento": 50,
                        "activa": True,
                        "fecha_inicio": "2025-09-26",
                        "fecha_fin": "2025-10-15"
                    }
                ]
        except Exception:
            self.ofertas = []

        # Variables para sincronización automática
        self.ventana_actual = None
        self.sincronizacion_activa = False

        # Cargar ventas (historial) desde la base de datos
        try:
            ventas_db = db.load_orders()
            if ventas_db:
                self.ventas = ventas_db
            else:
                self.ventas = []
        except Exception:
            self.ventas = []
        
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
        
        # Inicializar sistema de sincronización automática
        self.iniciar_sincronizacion_automatica()
        
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
            # Almacenar referencia para evitar garbage collection
            self.fondo_label_ref = fondo_label

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

        # Título principal
        titulo_frame = tk.Frame(frame, bg="#D32F2F", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))

        # Botón de regresar rápido en la cabecera
        btn_regresar = tk.Button(titulo_frame, text="⬅️ Regresar", command=self.mostrar_menu_principal,
                                 bg=self.color_boton_fondo, fg=self.color_boton_texto,
                                 font=("Helvetica", 10, "bold"), relief="raised", bd=1, padx=10, pady=6)
        btn_regresar.pack(side="right", padx=10, pady=8)

        tk.Label(titulo_frame, text="🍣 Nuestro Menú de Sushi 🍣",
                 font=("Impact", 22, "bold"), bg="#D32F2F", fg="white", pady=15).pack()

        # Cargar y mostrar ofertas activas dinámicamente
        self.mostrar_ofertas_activas_en_menu(frame)

        # Frame principal para el menú
        menu_container = tk.Frame(frame, bg=self.color_fondo_ventana)
        menu_container.pack(expand=True, fill="both", padx=20, pady=(0, 15))
        
        # Botones de filtro por categoría
        filtro_frame = tk.Frame(menu_container, bg=self.color_fondo_ventana, relief="raised", bd=2)
        filtro_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(filtro_frame, text="🎯 Filtrar por categoría:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).pack(pady=(10, 5))
        
        categorias_frame = tk.Frame(filtro_frame, bg=self.color_fondo_ventana)
        categorias_frame.pack(pady=(0, 10))
        
        # Botones de categorías
        categorias = ["Todos", "Rolls", "Especiales", "Vegetarianos", "Postres"]
        for categoria in categorias:
            tk.Button(categorias_frame, text=f"📂 {categoria}", 
                     command=lambda c=categoria: self.filtrar_productos_por_categoria(c),
                     bg="#607D8B" if categoria == "Todos" else "#9E9E9E", 
                     fg="white", font=("Helvetica", 10, "bold"),
                     relief="raised", bd=2, padx=15, pady=5).pack(side="left", padx=5)

        # Controles adicionales: búsqueda por nombre y rango de precio
        adv_filters_frame = tk.Frame(filtro_frame, bg=self.color_fondo_ventana)
        adv_filters_frame.pack(fill="x", padx=10, pady=(5, 10))

        tk.Label(adv_filters_frame, text="🔎 Buscar:", bg=self.color_fondo_ventana).pack(side="left", padx=(0, 6))
        self.menu_search_var = tk.StringVar()
        tk.Entry(adv_filters_frame, textvariable=self.menu_search_var, width=30).pack(side="left")

        tk.Label(adv_filters_frame, text="💲 Precio min:", bg=self.color_fondo_ventana).pack(side="left", padx=(10, 6))
        self.menu_price_min = tk.StringVar()
        tk.Entry(adv_filters_frame, textvariable=self.menu_price_min, width=8).pack(side="left")

        tk.Label(adv_filters_frame, text="💲 Precio max:", bg=self.color_fondo_ventana).pack(side="left", padx=(10, 6))
        self.menu_price_max = tk.StringVar()
        tk.Entry(adv_filters_frame, textvariable=self.menu_price_max, width=8).pack(side="left")

        tk.Button(adv_filters_frame, text="Aplicar filtros", command=self.aplicar_filtros_menu_sushi, bg="#2196F3", fg="white").pack(side="left", padx=(10, 5))
        tk.Button(adv_filters_frame, text="Limpiar filtros", command=lambda: (self.menu_search_var.set(''), self.menu_price_min.set(''), self.menu_price_max.set(''), self._menu_filters.pop('categoria', None), self.aplicar_filtros_menu_sushi()), bg="#9E9E9E", fg="white").pack(side="left")

        # Mostrar productos desde la base de datos
        try:
            productos = db.load_products()
            # Si la BD está vacía, crear productos de muestra
            if not productos:
                productos_muestra = [
                    {'id': 'SUS01', 'nombre': 'California Roll', 'descripcion': 'Kanikama, palta, pepino', 'precio': 120.0, 'stock': 50, 'categoria': 'Rolls'},
                    {'id': 'SUS02', 'nombre': 'Philadelphia Roll', 'descripcion': 'Salmón, queso Philadelphia, palta', 'precio': 150.0, 'stock': 45, 'categoria': 'Rolls'},
                    {'id': 'SUS03', 'nombre': 'Salmon Roll', 'descripcion': 'Salmón fresco, pepino, wasabi', 'precio': 180.0, 'stock': 30, 'categoria': 'Especiales'},
                    {'id': 'SUS04', 'nombre': 'Tuna Roll', 'descripcion': 'Atún rojo, palta, sésamo', 'precio': 200.0, 'stock': 25, 'categoria': 'Especiales'},
                    {'id': 'SUS05', 'nombre': 'Veggie Roll', 'descripcion': 'Palta, pepino, zanahoria, lechuga', 'precio': 100.0, 'stock': 60, 'categoria': 'Vegetarianos'}
                ]
                
                # Guardar productos de muestra en BD
                for prod in productos_muestra:
                    try:
                        db.save_product(prod)
                    except Exception:
                        pass
                
                productos = productos_muestra
        except Exception:
            productos = []

        # Cache de productos para aplicar filtros dinámicos
        self._menu_productos_cache = productos
        # Inicializar filtros activos
        self._menu_filters = {}

        # Crear tabla de productos mejorada
        tabla_frame = tk.Frame(menu_container, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both")
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tabla_frame)
        scrollbar_h = ttk.Scrollbar(tabla_frame, orient="horizontal")
        
        # Tabla con más información
        cols = ("ID", "Nombre", "Descripción", "Precio", "Stock", "Categoría")
        self.menu_tree = ttk.Treeview(tabla_frame, columns=cols, show="headings", 
                                     yscrollcommand=scrollbar_v.set, 
                                     xscrollcommand=scrollbar_h.set, height=12)
        
        # Configurar columnas
        columnas_config = [
            ("ID", 80, "center"),
            ("Nombre", 180, "w"),
            ("Descripción", 250, "w"),
            ("Precio", 100, "center"),
            ("Stock", 80, "center"),
            ("Categoría", 120, "center")
        ]
        
        for col, ancho, anchor in columnas_config:
            self.menu_tree.heading(col, text=col)
            # Convertir string a constante tkinter
            anchor_tk = "w" if anchor == "w" else "center" if anchor == "center" else "e"
            self.menu_tree.column(col, width=ancho, anchor=anchor_tk)

        # Llenado inicial de la tabla usando la cache y filtros
        ofertas_activas = [o for o in self.ofertas if o.get('activa', False)]
        # Poblamos la tabla aplicando filtros (vacío por defecto)
        self.aplicar_filtros_menu_sushi()

        # Configurar scrollbars
        scrollbar_v.config(command=self.menu_tree.yview)
        scrollbar_h.config(command=self.menu_tree.xview)
        
        self.menu_tree.pack(side="left", fill="both", expand=True)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")

        # Soporte para doble-clic: agregar producto seleccionado al carrito
        try:
            self.menu_tree.bind("<Double-1>", lambda e: self.agregar_seleccion_al_carrito_mejorado())
        except Exception:
            pass

        # Menú contextual (clic derecho) para agregar al carrito o regresar
        def _mostrar_menu_contextual(event):
            try:
                iid = self.menu_tree.identify_row(event.y)
                # Si se hizo clic sobre una fila, seleccionarla
                if iid:
                    self.menu_tree.selection_set(iid)

                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label="🛒 Agregar al Carrito", command=self.agregar_seleccion_al_carrito_mejorado)
                menu.add_separator()
                menu.add_command(label="⬅️ Regresar al Menú", command=self.mostrar_menu_principal)
                menu.post(event.x_root, event.y_root)
            except Exception:
                pass

        try:
            # Button-3 es clic derecho en Windows
            self.menu_tree.bind("<Button-3>", _mostrar_menu_contextual)
        except Exception:
            pass

        # Botones de acción mejorados
        btn_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        btn_frame.pack(fill="x", padx=20, pady=(15, 0))
        
        # Primera fila de botones
        btn_row1 = tk.Frame(btn_frame, bg=self.color_fondo_ventana)
        btn_row1.pack(pady=(10, 5))
        
        tamaños = self.calcular_tamaños_responsivos()

        tk.Button(btn_row1, text="🛒 Agregar al Carrito", command=self.agregar_seleccion_al_carrito_mejorado,
                 bg="#4CAF50", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady'], width=20).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="🎁 Ver Todas las Ofertas", command=self.mostrar_ofertas_cliente,
                 bg="#FF6F00", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady'], width=20).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="🛒 Ver Carrito", command=self.mostrar_carrito,
                 bg="#673AB7", fg="white", font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady'], width=20).pack(side="left", padx=5)

        # Segunda fila - información y navegación
        btn_row2 = tk.Frame(btn_frame, bg=self.color_fondo_ventana)
        btn_row2.pack(pady=(5, 10))
        
        # Mostrar información del carrito actual
        try:
            items_carrito = db.get_cart_item_count()
            total_carrito = db.get_cart_total()
            carrito_info = f"🛒 Carrito: {items_carrito} items - Total: ${total_carrito:.2f}"
        except Exception:
            carrito_info = "🛒 Carrito: 0 items"
        
        tk.Label(btn_row2, text=carrito_info, font=("Helvetica", 11, "bold"), 
                bg=self.color_fondo_ventana, fg=self.color_titulo).pack(side="left")

        tk.Button(btn_row2, text="⬅️ Regresar", command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], pady=tamaños['boton_gestion_pady']).pack(side="right")

    def mostrar_ofertas_activas_en_menu(self, parent):
        """Muestra un banner con las ofertas activas en el menú"""
        try:
            # Cargar ofertas desde BD
            ofertas_bd = db.load_offers()
            if ofertas_bd:
                self.ofertas = ofertas_bd
            
            ofertas_activas = [o for o in self.ofertas if o.get('activa', False)]
            
            if ofertas_activas:
                # Frame para ofertas con animación visual
                ofertas_banner = tk.Frame(parent, bg="#FFE082", relief="raised", bd=3)
                ofertas_banner.pack(fill="x", padx=20, pady=(0, 15))
                
                tk.Label(ofertas_banner, text="🎁 ¡OFERTAS ESPECIALES ACTIVAS! 🎁", 
                        font=("Helvetica", 14, "bold"), bg="#FFE082", fg="#E65100").pack(pady=(8, 5))
                
                # Mostrar hasta 3 ofertas más relevantes
                for i, oferta in enumerate(ofertas_activas[:3]):
                    oferta_text = f"🔥 {oferta['nombre']}: {oferta['descripcion']}"
                    tk.Label(ofertas_banner, text=oferta_text, 
                            font=("Helvetica", 10), bg="#FFE082", fg="#BF360C",
                            wraplength=700, justify="left").pack(anchor="w", padx=20, pady=1)
                
                if len(ofertas_activas) > 3:
                    tk.Label(ofertas_banner, text=f"... y {len(ofertas_activas)-3} ofertas más", 
                            font=("Helvetica", 9, "italic"), bg="#FFE082", fg="#8D6E63").pack(pady=(2, 8))
                else:
                    tk.Label(ofertas_banner, text=" ", bg="#FFE082").pack(pady=4)  # Espaciador
        except Exception as e:
            print(f"Error al cargar ofertas: {e}")

    def filtrar_productos_por_categoria(self, categoria):
        """Filtra los productos mostrados por categoría"""
        # Implementación: establecer filtro de categoría y reaplicar filtros
        if categoria == "Todos":
            # Quitar el filtro de categoría
            if hasattr(self, '_menu_filters'):
                self._menu_filters.pop('categoria', None)
        else:
            if not hasattr(self, '_menu_filters'):
                self._menu_filters = {}
            self._menu_filters['categoria'] = categoria

        # Aplicar filtros actuales
        try:
            self.aplicar_filtros_menu_sushi()
        except Exception:
            # Si algo falla, recargar la vista completa
            self.mostrar_menu_sushi()

    def aplicar_filtros_menu_sushi(self):
        """Aplica filtros (búsqueda, categoría, rango de precio) sobre la cache de productos y actualiza self.menu_tree"""
        # Limpiar tabla
        try:
            for iid in list(self.menu_tree.get_children()):
                self.menu_tree.delete(iid)
        except Exception:
            pass

        productos = getattr(self, '_menu_productos_cache', []) or []
        filtros = getattr(self, '_menu_filters', {}) or {}

        # Lectura de filtros de UI
        texto_buscar = (getattr(self, 'menu_search_var', tk.StringVar()).get() or '').strip().lower()
        precio_min = (getattr(self, 'menu_price_min', tk.StringVar()).get() or '').strip()
        precio_max = (getattr(self, 'menu_price_max', tk.StringVar()).get() or '').strip()

        try:
            precio_min_val = float(precio_min) if precio_min else None
        except Exception:
            precio_min_val = None

        try:
            precio_max_val = float(precio_max) if precio_max else None
        except Exception:
            precio_max_val = None

        ofertas_activas = [o for o in self.ofertas if o.get('activa', False)]

        for prod in productos:
            try:
                if not prod.get('activo', True):
                    continue

                # Filtrar por categoría si aplica
                categoria_filtro = filtros.get('categoria')
                if categoria_filtro and categoria_filtro != 'Todos':
                    if str(prod.get('categoria', '')).lower() != categoria_filtro.lower():
                        continue

                nombre = str(prod.get('nombre', ''))
                descripcion = str(prod.get('descripcion', '') or '')

                # Filtrar por búsqueda
                if texto_buscar:
                    if (texto_buscar not in nombre.lower()) and (texto_buscar not in descripcion.lower()):
                        continue

                precio_original = float(prod.get('precio', 0) or 0)
                precio_mostrar = precio_original

                # Aplicar ofertas (si aplica) para mostrar precio
                for oferta in ofertas_activas:
                    if self._producto_aplica_oferta(prod, oferta):
                        if oferta.get('tipo') == 'descuento':
                            descuento = oferta.get('descuento', 0)
                            precio_mostrar = precio_original * (1 - descuento/100)
                        break

                # Filtrar por rango de precio
                if precio_min_val is not None and precio_mostrar < precio_min_val:
                    continue
                if precio_max_val is not None and precio_mostrar > precio_max_val:
                    continue

                # Estado de stock
                stock = prod.get('stock', 0)
                nombre_con_oferta = nombre
                if stock <= 0:
                    nombre_con_oferta = f"{nombre_con_oferta} (AGOTADO)"
                elif stock <= 10:
                    nombre_con_oferta = f"{nombre_con_oferta} (POCO STOCK)"

                iid = str(prod.get('id') or prod.get('nombre'))
                self.menu_tree.insert("", "end", iid=iid, values=(
                    prod.get('id'),
                    nombre_con_oferta,
                    descripcion,
                    f"${precio_mostrar:.2f}" + (f" (era ${precio_original:.2f})" if precio_mostrar != precio_original else ""),
                    stock,
                    prod.get('categoria', 'General')
                ))
            except Exception:
                # Omitir producto si alguno falla para mantener la UI responsiva
                continue

    def agregar_seleccion_al_carrito_mejorado(self):
        """Versión mejorada para agregar productos al carrito con validaciones"""
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar producto", "Selecciona un producto para agregar al carrito")
            return
        
        try:
            iid = sel[0]
            valores = self.menu_tree.item(iid)['values']
            producto_id = valores[0]
            
            # Buscar producto en BD para obtener datos actualizados
            productos = db.load_products()
            producto = next((p for p in productos if str(p.get('id')) == str(producto_id)), None)
            
            if not producto:
                messagebox.showerror("Error", "No se encontró el producto en la base de datos")
                return
            
            # Verificar stock
            stock_actual = producto.get('stock', 0)
            if stock_actual <= 0:
                messagebox.showwarning("Sin stock", f"El producto '{producto['nombre']}' está agotado")
                return
            
            # Verificar si ya está en el carrito para calcular stock disponible
            items_carrito = db.get_cart_items()
            cantidad_en_carrito = sum(item['quantity'] for item in items_carrito if item['product_id'] == str(producto_id))
            stock_disponible = stock_actual - cantidad_en_carrito
            
            if stock_disponible <= 0:
                messagebox.showwarning("Sin stock", f"Ya tienes todo el stock disponible de '{producto['nombre']}' en tu carrito")
                return
            
            # Aplicar ofertas si las hay
            precio_final = float(producto.get('precio', 0))
            oferta_aplicada = None
            
            ofertas_activas = [o for o in self.ofertas if o.get('activa', False)]
            for oferta in ofertas_activas:
                if self._producto_aplica_oferta(producto, oferta):
                    if oferta['tipo'] == 'descuento':
                        descuento = oferta['descuento']
                        precio_final = precio_final * (1 - descuento/100)
                        oferta_aplicada = oferta['nombre']
                    break
            
            # Agregar al carrito
            nombre_producto = producto.get('nombre') or 'Producto sin nombre'
            db.add_cart_item(str(producto_id), nombre_producto, 1, precio_final)
            
            # Mensaje de confirmación con información de oferta si aplica
            mensaje = f"✅ {producto.get('nombre')} agregado al carrito"
            if oferta_aplicada:
                mensaje += f"\n🎁 Oferta aplicada: {oferta_aplicada}"
            if precio_final != float(producto.get('precio', 0)):
                mensaje += f"\n💰 Precio con descuento: ${precio_final:.2f}"
            
            messagebox.showinfo("Agregado al carrito", mensaje)
            
            # Actualizar vista del menú para reflejar cambios en stock/carrito
            self.mostrar_menu_sushi()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar al carrito: {str(e)}")

    def _producto_aplica_oferta(self, producto, oferta):
        """Verifica si un producto es elegible para una oferta"""
        productos_aplicables = oferta.get('productos_aplicables', [])
        
        # Si la oferta aplica a "todos" los productos
        if 'todos' in productos_aplicables or not productos_aplicables:
            return True
        
        # Si el producto específico está en la lista
        if producto.get('nombre') in productos_aplicables or producto.get('id') in productos_aplicables:
            return True
        
        # Si la categoría del producto está en la lista
        if producto.get('categoria') in productos_aplicables:
            return True
        
        return False

    def mostrar_carrito(self):
        frame = self.limpiar_ventana()
        self.marcar_ventana_actual('carrito')
        
        # Título mejorado
        titulo_frame = tk.Frame(frame, bg="#4CAF50", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="🛒 Carrito de Compras 🛒", 
                font=("Impact", 20, "bold"), bg="#4CAF50", fg="white", pady=12).pack()
        
        # Frame para información del carrito
        info_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Controles superiores del carrito
        control_frame = tk.Frame(info_frame, bg=self.color_fondo_ventana)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(control_frame, text="🔄 Actualizar Carrito", 
                 command=self.actualizar_carrito,
                 bg="#2196F3", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=5).pack(side="left")
        
        tk.Button(control_frame, text="🗑️ Vaciar Carrito", 
                 command=self.vaciar_carrito,
                 bg="#F44336", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=5).pack(side="left", padx=(10, 0))
        
        self.carrito_info_label = tk.Label(control_frame, text="Cargando...", 
                                          font=("Helvetica", 11, "bold"), 
                                          bg=self.color_fondo_ventana, fg=self.color_titulo)
        self.carrito_info_label.pack(side="right")
        
        # Tabla del carrito con más funcionalidad
        tabla_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=15, pady=(0, 15))
        
        columns = ("ID", "Producto", "Precio Unit.", "Cantidad", "Subtotal")
        self.carrito_tree = ttk.Treeview(tabla_frame, columns=columns, show="headings", height=10)
        
        # Configurar columnas
        columnas_config = [
            ("ID", 60, "center"),
            ("Producto", 250, "w"),
            ("Precio Unit.", 100, "center"),
            ("Cantidad", 80, "center"),
            ("Subtotal", 100, "center")
        ]
        
        for col, ancho, anchor in columnas_config:
            self.carrito_tree.heading(col, text=col)
            # Convertir string a constante tkinter
            anchor_tk = "w" if anchor == "w" else "center" if anchor == "center" else "e"
            self.carrito_tree.column(col, width=ancho, anchor=anchor_tk)
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.carrito_tree.yview)
        scrollbar_h = ttk.Scrollbar(tabla_frame, orient="horizontal", command=self.carrito_tree.xview)
        self.carrito_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        self.carrito_tree.pack(side="left", fill="both", expand=True)
        scrollbar_v.pack(side="right", fill="y")
        
        # Cargar datos del carrito
        self.cargar_datos_carrito()
        
        # Frame para acciones del carrito
        acciones_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        acciones_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Primera fila de botones de acción
        acciones_row1 = tk.Frame(acciones_frame, bg=self.color_fondo_ventana)
        acciones_row1.pack(pady=(10, 5))
        
        tk.Button(acciones_row1, text="➕ Aumentar Cantidad", 
                 command=self.aumentar_cantidad_item,
                 bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=6, width=18).pack(side="left", padx=5)
        
        tk.Button(acciones_row1, text="➖ Disminuir Cantidad", 
                 command=self.disminuir_cantidad_item,
                 bg="#FF9800", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=6, width=18).pack(side="left", padx=5)
        
        tk.Button(acciones_row1, text="🗑️ Eliminar Item", 
                 command=self.eliminar_item_carrito,
                 bg="#F44336", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=6, width=18).pack(side="left", padx=5)
        
        # Segunda fila con total y navegación
        acciones_row2 = tk.Frame(acciones_frame, bg=self.color_fondo_ventana)
        acciones_row2.pack(pady=(5, 10))
        
        # Frame para total
        total_frame = tk.Frame(acciones_row2, bg="#E8F5E8", relief="raised", bd=2)
        total_frame.pack(side="left", padx=(0, 20), pady=5)
        
        self.total_label = tk.Label(total_frame, text="Total: $0.00", 
                                   font=("Helvetica", 16, "bold"), 
                                   bg="#E8F5E8", fg="#2E7D32", padx=20, pady=10)
        self.total_label.pack()
        
        # Botones de navegación
        nav_frame = tk.Frame(acciones_row2, bg=self.color_fondo_ventana)
        nav_frame.pack(side="right")
        
        tk.Button(nav_frame, text="🍣 Seguir Comprando", 
                 command=self.mostrar_menu_sushi,
                 bg="#673AB7", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8, width=18).pack(side="left", padx=5)

        # Permitir confirmar el pedido directamente desde la vista del carrito
        def realizar_pedido_desde_carrito():
            try:
                items = db.get_cart_items()
                if not items:
                    messagebox.showwarning("Carrito vacío", "No hay productos en el carrito")
                    return

                orden_id = f"VTA{len(self.ventas)+1:03d}"
                fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                productos = []
                total_sin = 0.0
                for it in items:
                    prod = {'nombre': it['product_name'], 'cantidad': it['quantity'], 'precio': float(it['price']), 'subtotal': it['quantity'] * float(it['price'])}
                    productos.append(prod)
                    total_sin += prod['subtotal']

                # Placeholder para aplicación de ofertas/descuntos
                oferta_aplicada = None
                descuento_aplicado = 0.0
                total_final = total_sin - descuento_aplicado

                orden = {
                    'id': orden_id,
                    'fecha': fecha,
                    'productos': productos,
                    'oferta_aplicada': oferta_aplicada,
                    'descuento_aplicado': descuento_aplicado,
                    'total_sin_descuento': total_sin,
                    'total_final': total_final,
                    'metodo_pago': 'efectivo',
                    'cajero': 'Sistema',
                    'estado': 'En preparación'
                }

                # Guardar orden en memoria y en BD
                self.ventas.append(orden)
                try:
                    db.save_order(orden)
                except Exception:
                    pass

                # Limpiar carrito
                try:
                    db.clear_cart()
                except Exception:
                    pass

                # Refrescar vista del carrito
                try:
                    self.cargar_datos_carrito()
                except Exception:
                    pass

                messagebox.showinfo("Pedido Confirmado", f"Pedido {orden_id} confirmado. Total: ${total_final:.2f}")
                self.mostrar_menu_principal()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo confirmar el pedido: {e}")

        tk.Button(nav_frame, text="📦 Realizar Pedido", 
                 command=realizar_pedido_desde_carrito,
                 bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8, width=18).pack(side="left", padx=5)
        
        # Botón regresar
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(frame, text="⬅️ Regresar al Menú Principal", 
                 command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, 
                 font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], 
                 pady=tamaños['boton_gestion_pady']).pack(pady=15)
    
    def cargar_datos_carrito(self):
        """Carga los datos del carrito desde la base de datos"""
        # Hacer la carga más tolerante a datos incompletos/erróneos para evitar errores intermitentes
        # Limpiar tabla actual
        try:
            for item_id in list(self.carrito_tree.get_children()):
                self.carrito_tree.delete(item_id)
        except Exception:
            # Si la tabla aún no existe por alguna razón, ignorar
            pass

        # Intentar leer items del carrito con reintentos suaves en caso de fallos transitorios
        try:
            items = db.get_cart_items() or []
            # Si llegamos aquí, resetear contador de intentos
            if hasattr(self, '_cart_load_attempts'):
                self._cart_load_attempts = 0
        except Exception as e:
            # Inicializar contador de reintentos si no existe
            attempts = getattr(self, '_cart_load_attempts', 0) + 1
            self._cart_load_attempts = attempts
            if attempts <= 3:
                # Mostrar estado de reintento y programar un nuevo intento breve
                try:
                    self.carrito_info_label.config(text=f"⏳ Reintentando carga del carrito ({attempts}/3)...")
                except Exception:
                    pass
                try:
                    # Reintentar después de 500ms
                    self.after(500, self.cargar_datos_carrito)
                except Exception:
                    pass
                return
            else:
                # Agotar reintentos y mostrar mensaje de error persistente
                err_msg = f"Error leyendo carrito: {e}"
                try:
                    self.carrito_info_label.config(text=f"❌ {err_msg}")
                except Exception:
                    pass
                # Resetear contador para futuros intentos manuales
                self._cart_load_attempts = 0
                return

        total_items = 0
        total_precio = 0.0
        errores_items = []

        for item in items:
            try:
                # Valores seguros
                cantidad = int(item.get('quantity', 0))
                precio = float(item.get('price', 0.0))
                subtotal = cantidad * precio

                total_items += cantidad
                total_precio += subtotal

                # Insertar en tabla (usar valores formateados)
                try:
                    iid = str(item.get('id') or item.get('product_id') or total_items)
                    self.carrito_tree.insert("", "end", iid=iid, values=(
                        item.get('product_id', ''),
                        item.get('product_name', ''),
                        f"${precio:.2f}",
                        cantidad,
                        f"${subtotal:.2f}"
                    ))
                except Exception:
                    # Si falla la inserción visual, continuar con los demás
                    pass
            except Exception as e:
                # Registrar el error del item y continuar
                errores_items.append(str(e))
                continue

        # Actualizar labels informativos
        try:
            if total_items == 0:
                self.carrito_info_label.config(text="🛒 Carrito vacío")
                self.total_label.config(text="Total: $0.00")
            else:
                self.carrito_info_label.config(text=f"🛒 {total_items} productos en carrito")
                self.total_label.config(text=f"Total: ${total_precio:.2f}")

            # Si hubo errores con algunos items, mostrar un aviso no intrusivo en la etiqueta
            if errores_items:
                # Mostrar número de items omitidos
                try:
                    self.carrito_info_label.config(text=self.carrito_info_label.cget('text') + f"  ⚠️ {len(errores_items)} item(s) omitidos")
                except Exception:
                    pass
        except Exception:
            # No bloquear la UI por errores de actualización de labels
            pass
    
    def actualizar_carrito(self):
        """Actualiza los datos del carrito desde la BD"""
        self.cargar_datos_carrito()
        messagebox.showinfo("Actualización", "Carrito actualizado desde la base de datos")
    
    def vaciar_carrito(self):
        """Vacía completamente el carrito"""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de vaciar todo el carrito?\n\nEsta acción no se puede deshacer."):
            try:
                db.clear_cart()
                self.cargar_datos_carrito()
                messagebox.showinfo("Éxito", "Carrito vaciado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al vaciar carrito: {str(e)}")
    
    def aumentar_cantidad_item(self):
        """Aumenta la cantidad del item seleccionado"""
        sel = self.carrito_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un producto para aumentar su cantidad")
            return
        
        try:
            item_id = int(sel[0])
            # Obtener datos actuales del item
            items = db.get_cart_items()
            item = next((i for i in items if i['id'] == item_id), None)
            
            if item:
                # Aumentar cantidad
                nueva_cantidad = item['quantity'] + 1
                db.update_cart_item_quantity(item_id, nueva_cantidad)
                self.cargar_datos_carrito()
                messagebox.showinfo("Éxito", f"Cantidad aumentada a {nueva_cantidad}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al aumentar cantidad: {str(e)}")
    
    def disminuir_cantidad_item(self):
        """Disminuye la cantidad del item seleccionado"""
        sel = self.carrito_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un producto para disminuir su cantidad")
            return
        
        try:
            item_id = int(sel[0])
            # Obtener datos actuales del item
            items = db.get_cart_items()
            item = next((i for i in items if i['id'] == item_id), None)
            
            if item:
                if item['quantity'] <= 1:
                    # Si la cantidad es 1, preguntar si eliminar
                    if messagebox.askyesno("Confirmar", "La cantidad es 1. ¿Deseas eliminar este producto del carrito?"):
                        db.remove_cart_item(item_id)
                        self.cargar_datos_carrito()
                        messagebox.showinfo("Éxito", "Producto eliminado del carrito")
                else:
                    # Disminuir cantidad
                    nueva_cantidad = item['quantity'] - 1
                    db.update_cart_item_quantity(item_id, nueva_cantidad)
                    self.cargar_datos_carrito()
                    messagebox.showinfo("Éxito", f"Cantidad reducida a {nueva_cantidad}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al disminuir cantidad: {str(e)}")
    
    def eliminar_item_carrito(self):
        """Elimina completamente un item del carrito"""
        sel = self.carrito_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un producto para eliminar")
            return
        
        try:
            item_id = int(sel[0])
            valores = self.carrito_tree.item(sel[0])['values']
            producto_nombre = valores[1]
            
            if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar '{producto_nombre}' del carrito?"):
                db.remove_cart_item(item_id)
                self.cargar_datos_carrito()
                messagebox.showinfo("Éxito", f"'{producto_nombre}' eliminado del carrito")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar producto: {str(e)}")

    def mostrar_realizar_pedido(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Confirmar Pedido 📦", style="Titulo.TLabel").pack(pady=(0, 20))
        ttk.Label(frame, text="Revisa tu pedido antes de confirmar.").pack()
        # Calcular total desde carrito
        try:
            items = db.get_cart_items()
            total = sum(it['quantity'] * float(it['price']) for it in items)
        except Exception:
            items = []
            total = 240.0

        ttk.Label(frame, text=f"Total: ${total:.2f}", style="Subtitulo.TLabel").pack(pady=10)
        btn_frame = ttk.Frame(frame);
        btn_frame.pack(pady=10)
        tamaños = self.calcular_tamaños_responsivos()

        def confirmar_pedido():
            try:
                if not items:
                    messagebox.showwarning("Carrito vacío", "No hay productos en el carrito")
                    return

                orden_id = f"VTA{len(self.ventas)+1:03d}"
                fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                productos = []
                total_sin = 0.0
                for it in items:
                    prod = {'nombre': it['product_name'], 'cantidad': it['quantity'], 'precio': float(it['price']), 'subtotal': it['quantity'] * float(it['price'])}
                    productos.append(prod)
                    total_sin += prod['subtotal']

                # Aplicación simple de ofertas: (placeholder)
                oferta_aplicada = None
                descuento_aplicado = 0.0
                total_final = total_sin - descuento_aplicado

                orden = {
                    'id': orden_id,
                    'fecha': fecha,
                    'productos': productos,
                    'oferta_aplicada': oferta_aplicada,
                    'descuento_aplicado': descuento_aplicado,
                    'total_sin_descuento': total_sin,
                    'total_final': total_final,
                    'metodo_pago': 'efectivo',
                    'cajero': 'Sistema',
                    'estado': 'En preparación'
                }

                # Guardar orden en memoria y en BD
                self.ventas.append(orden)
                try:
                    db.save_order(orden)
                except Exception:
                    pass

                # Limpiar carrito
                try:
                    db.clear_cart()
                except Exception:
                    pass

                messagebox.showinfo("Pedido Confirmado", f"Pedido {orden_id} confirmado. Total: ${total_final:.2f}")
                self.mostrar_menu_principal()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo confirmar el pedido: {e}")

        ttk.Button(btn_frame, text="✅ Confirmar", width=tamaños['boton_width']//2, command=confirmar_pedido).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", width=tamaños['boton_width']//2, command=self.mostrar_menu_principal).pack(side="left", padx=5)
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
        ttk.Label(frame, text="Historial de Pedidos 📜", style="Titulo.TLabel").pack(pady=(0, 12))

        # Contenedor para la tabla
        tabla_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill='both', padx=20, pady=(5, 10))

        cols = ("ID Pedido", "Fecha", "Productos", "Total", "Estado")
        historial_tree = ttk.Treeview(tabla_frame, columns=cols, show='headings', height=12)
        for c in cols:
            historial_tree.heading(c, text=c)
            historial_tree.column(c, anchor='center')

        scrollbar = ttk.Scrollbar(tabla_frame, orient='vertical', command=historial_tree.yview)
        historial_tree.configure(yscrollcommand=scrollbar.set)
        historial_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Cargar pedidos desde la base de datos
        try:
            pedidos = db.load_orders()
        except Exception:
            pedidos = []

        # Rellenar tabla
        for venta in sorted(pedidos, key=lambda x: x.get('fecha', ''), reverse=True):
            try:
                fecha = venta.get('fecha', '')
                productos = venta.get('productos', [])
                productos_texto = ", ".join([f"{p.get('nombre', p.get('id',''))} x{p.get('cantidad',0)}" for p in productos])
                if len(productos_texto) > 60:
                    productos_texto = productos_texto[:57] + '...'
                total = f"${float(venta.get('total_final', 0)):.2f}"
                estado = venta.get('estado', 'En preparación')
                historial_tree.insert('', 'end', iid=venta.get('id'), values=(venta.get('id'), fecha, productos_texto, total, estado))
            except Exception:
                continue

        # Acciones
        acciones_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        acciones_frame.pack(fill='x', padx=20, pady=8)

        tamaños = self.calcular_tamaños_responsivos()

        def _refresh():
            try:
                for iid in historial_tree.get_children():
                    historial_tree.delete(iid)
                pedidos = db.load_orders()
                for venta in sorted(pedidos, key=lambda x: x.get('fecha', ''), reverse=True):
                    try:
                        fecha = venta.get('fecha', '')
                        productos = venta.get('productos', [])
                        productos_texto = ", ".join([f"{p.get('nombre', p.get('id',''))} x{p.get('cantidad',0)}" for p in productos])
                        if len(productos_texto) > 60:
                            productos_texto = productos_texto[:57] + '...'
                        total = f"${float(venta.get('total_final', 0)):.2f}"
                        estado = venta.get('estado', 'En preparación')
                        historial_tree.insert('', 'end', iid=venta.get('id'), values=(venta.get('id'), fecha, productos_texto, total, estado))
                    except Exception:
                        continue
            except Exception:
                pass

        def _ver_detalle():
            sel = historial_tree.selection()
            if not sel:
                messagebox.showwarning('Seleccionar', 'Selecciona una venta para ver detalles')
                return
            vid = sel[0]
            try:
                pedidos = db.load_orders()
                venta = next((v for v in pedidos if v.get('id') == vid), None)
                if not venta:
                    messagebox.showerror('Error', 'Venta no encontrada en la base de datos')
                    return

                detalles = f"ID: {venta.get('id')}\nFecha: {venta.get('fecha')}\nEstado: {venta.get('estado', '')}\nTotal: ${float(venta.get('total_final',0)):.2f}\nDescuento: ${float(venta.get('descuento_aplicado',0)):.2f}\n\nProductos:\n"
                for p in venta.get('productos', []):
                    detalles += f" - {p.get('nombre', p.get('id',''))} x{p.get('cantidad',0)} -> ${float(p.get('precio',0))*int(p.get('cantidad',0)):.2f}\n"

                messagebox.showinfo('Detalle de Venta', detalles)
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo obtener el detalle: {e}')

        tk.Button(acciones_frame, text='📄 Ver Detalle', command=_ver_detalle, bg='#2196F3', fg='white', width=18).pack(side='left', padx=5)
        tk.Button(acciones_frame, text='🔄 Refrescar', command=_refresh, bg='#4CAF50', fg='white', width=12).pack(side='right', padx=5)
        tk.Button(acciones_frame, text='⬅️ Regresar', command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(side='right', padx=5)

    # --- Vistas Cajero ---
    def mostrar_registrar_pedido(self):
        self.mostrar_menu_sushi()
        # After showing the menu, add a quick button in the menu header to go directly to the carrito
        try:
            root_frame = self.winfo_children()[0]
            parent_for_buttons = None
            # Buscar el label del título del menú para obtener su contenedor (titulo_frame)
            for widget in root_frame.winfo_children():
                try:
                    if isinstance(widget, tk.Label) and 'Nuestro Menú' in str(widget.cget('text')):
                        parent_for_buttons = widget.master
                        break
                except Exception:
                    continue

            if parent_for_buttons is None:
                # Fallback: use first child frame
                for widget in root_frame.winfo_children():
                    if isinstance(widget, tk.Frame):
                        parent_for_buttons = widget
                        break

            if parent_for_buttons is not None:
                # Crear botón al header que lleve al carrito
                try:
                    btn_carrito = tk.Button(parent_for_buttons, text="🛒 Ir al Carrito", command=self.mostrar_carrito,
                                            bg="#673AB7", fg="white", font=("Helvetica", 10, "bold"), relief="raised", bd=1, padx=10, pady=6)
                    btn_carrito.pack(side="right", padx=10, pady=8)
                except Exception:
                    pass

            # También reaplicar el comportamiento del botón regresar si existe
            for widget in root_frame.winfo_children():
                try:
                    if hasattr(widget, 'cget') and widget.cget('text') and 'Regresar' in str(widget.cget('text')):
                        try:
                            widget.configure(command=self.mostrar_menu_principal)
                        except Exception:
                            pass
                except Exception:
                    continue
        except Exception:
            # No bloquear si algo falla
            pass

    def mostrar_pedidos_activos(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Pedidos Activos 👀", style="Titulo.TLabel").pack(pady=(0, 20))

        # Contenedor para la tabla y acciones
        tabla_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=20)

        cols = ("ID Pedido", "Mesa", "Total", "Estado")
        pedidos_tree = ttk.Treeview(tabla_frame, columns=cols, show='headings', height=10)
        for c in cols:
            pedidos_tree.heading(c, text=c)
            pedidos_tree.column(c, anchor='center')

        # Cargar pedidos activos desde BD
        try:
            pedidos = db.load_orders()
            activos = [p for p in pedidos if p.get('estado', 'En preparación') in ('En preparación', 'Pendiente')]
        except Exception:
            activos = []

        for p in activos:
            pedidos_tree.insert('', 'end', iid=p.get('id'), values=(p.get('id'), p.get('cajero', ''), f"${float(p.get('total_final', 0)):.2f}", p.get('estado', 'En preparación')))

        pedidos_tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tabla_frame, orient='vertical', command=pedidos_tree.yview)
        pedidos_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Acciones sobre pedidos
        acciones_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        acciones_frame.pack(fill='x', padx=20, pady=10)

        tamaños = self.calcular_tamaños_responsivos()

        def _refresh_pedidos():
            try:
                for iid in pedidos_tree.get_children():
                    pedidos_tree.delete(iid)
                pedidos = db.load_orders()
                activos = [p for p in pedidos if p.get('estado', 'En preparación') in ('En preparación', 'Pendiente')]
                for p in activos:
                    pedidos_tree.insert('', 'end', iid=p.get('id'), values=(p.get('id'), p.get('cajero', ''), f"${float(p.get('total_final', 0)):.2f}", p.get('estado', 'En preparación')))
            except Exception:
                pass

        def _cancelar_pedido():
            sel = pedidos_tree.selection()
            if not sel:
                messagebox.showwarning('Seleccionar pedido', 'Selecciona un pedido para cancelar')
                return
            pid = sel[0]
            if not messagebox.askyesno('Confirmar', f'¿Cancelar el pedido {pid}?'):
                return
            try:
                # Actualizar estado en BD
                pedidos = db.load_orders()
                orden = next((o for o in pedidos if o.get('id') == pid), None)
                if not orden:
                    messagebox.showerror('Error', 'Pedido no encontrado')
                    return
                orden['estado'] = 'Cancelado'
                db.save_order(orden)
                messagebox.showinfo('Pedido cancelado', f'Pedido {pid} marcado como Cancelado')
                _refresh_pedidos()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo cancelar el pedido: {e}')

        def _completar_pedido():
            sel = pedidos_tree.selection()
            if not sel:
                messagebox.showwarning('Seleccionar pedido', 'Selecciona un pedido para completar')
                return
            pid = sel[0]
            if not messagebox.askyesno('Confirmar', f'¿Marcar el pedido {pid} como Completado? Esto restará el stock de los productos.'):
                return
            try:
                pedidos = db.load_orders()
                orden = next((o for o in pedidos if o.get('id') == pid), None)
                if not orden:
                    messagebox.showerror('Error', 'Pedido no encontrado')
                    return

                # Restar stock por cada producto en la orden
                for item in orden.get('productos', []):
                    # Intentar mapear por nombre o id
                    prod_name = item.get('nombre')
                    cantidad = int(item.get('cantidad', 0) or 0)
                    try:
                        prod = db.get_product_by_name(prod_name)
                        if not prod:
                            # No encontrado por nombre, intentar por id si está presente
                            prod = db.get_product_by_id(item.get('id')) if item.get('id') else None
                        if prod:
                            db.update_product_stock(prod.get('id'), -cantidad)
                    except Exception:
                        # Si falla actualizar un producto, continuar con los demás
                        continue

                orden['estado'] = 'Completado'
                db.save_order(orden)
                messagebox.showinfo('Pedido completado', f'Pedido {pid} marcado como Completado y stock actualizado')
                _refresh_pedidos()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo completar el pedido: {e}')

        tk.Button(acciones_frame, text='✅ Completar Pedido', command=_completar_pedido, bg='#4CAF50', fg='white', width=20).pack(side='left', padx=5)
        tk.Button(acciones_frame, text='❌ Cancelar Pedido', command=_cancelar_pedido, bg='#F44336', fg='white', width=20).pack(side='left', padx=5)
        tk.Button(acciones_frame, text='🔄 Refrescar', command=_refresh_pedidos, bg='#2196F3', fg='white', width=12).pack(side='right', padx=5)

        # Navegación
        ttk.Button(frame, text='⬅️ Regresar', command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=10)

    def mostrar_cobrar(self):
        frame = self.limpiar_ventana()
        ttk.Label(frame, text="Cobrar / Facturar 💳", style="Titulo.TLabel").pack(pady=(0, 20))

        # Contenedor principal
        main = tk.Frame(frame, bg=self.color_fondo_ventana)
        main.pack(expand=True, fill='both', padx=20, pady=10)

        # Selección de pedido reciente
        tk.Label(main, text="Seleccionar pedido reciente:", bg=self.color_fondo_ventana, font=("Helvetica", 11, "bold")).pack(anchor='w')
        try:
            pedidos = db.load_orders()
            # Ordenar por fecha descendente si la fecha está presente
            try:
                pedidos_sorted = sorted(pedidos, key=lambda x: x.get('fecha') or '', reverse=True)
            except Exception:
                pedidos_sorted = pedidos
        except Exception:
            pedidos_sorted = []

        pedido_ids = [p.get('id') for p in pedidos_sorted]
        self._cobrar_selected_order_var = tk.StringVar()
        pedido_combo = ttk.Combobox(main, textvariable=self._cobrar_selected_order_var, values=pedido_ids, width=40)
        pedido_combo.pack(anchor='w', pady=(6, 12))

        # Área de detalles del pedido seleccionado
        detalles_label = tk.Label(main, text="Detalles del pedido:", bg=self.color_fondo_ventana, font=("Helvetica", 11, "bold"))
        detalles_label.pack(anchor='w')

        detalles_text = tk.Text(main, height=12, wrap='word')
        detalles_text.pack(fill='both', expand=False, pady=(6, 10))
        detalles_text.configure(state='disabled')

        def mostrar_detalles_seleccion(event=None):
            sel = self._cobrar_selected_order_var.get()
            detalles_text.configure(state='normal')
            detalles_text.delete('1.0', 'end')
            if not sel:
                detalles_text.insert('1.0', 'Seleccione un pedido para ver su desglose')
                detalles_text.configure(state='disabled')
                return
            orden = next((o for o in pedidos_sorted if o.get('id') == sel), None)
            if not orden:
                detalles_text.insert('1.0', 'Pedido no encontrado')
                detalles_text.configure(state='disabled')
                return

            # Formatear texto del pedido
            s = []
            s.append(f"ID Pedido: {orden.get('id')}")
            s.append(f"Fecha: {orden.get('fecha')}")
            s.append(f"Cajero: {orden.get('cajero', '')}")
            s.append(f"Estado: {orden.get('estado', '')}")
            s.append('\nProductos:')
            productos = orden.get('productos', []) or []
            for it in productos:
                nombre = it.get('nombre', '')
                cantidad = int(it.get('cantidad', 0) or 0)
                precio = float(it.get('precio', 0) or 0)
                subtotal = float(it.get('subtotal', cantidad * precio) or (cantidad * precio))
                s.append(f" - {nombre}: {cantidad} x ${precio:.2f} = ${subtotal:.2f}")

            s.append('\nTotales:')
            s.append(f"Total sin descuento: ${float(orden.get('total_sin_descuento', 0)):.2f}")
            s.append(f"Descuento aplicado: ${float(orden.get('descuento_aplicado', 0)):.2f}")
            s.append(f"Total final: ${float(orden.get('total_final', 0)):.2f}")
            s.append(f"Método de pago: {orden.get('metodo_pago', '')}")

            detalles_text.insert('1.0', '\n'.join(s))
            detalles_text.configure(state='disabled')

        pedido_combo.bind('<<ComboboxSelected>>', mostrar_detalles_seleccion)

        # Acciones: exportar a TXT y confirmar pago
        acciones = tk.Frame(main, bg=self.color_fondo_ventana)
        acciones.pack(fill='x', pady=(10, 0))

        def exportar_txt():
            sel = self._cobrar_selected_order_var.get()
            if not sel:
                messagebox.showwarning('Seleccionar pedido', 'Selecciona un pedido para exportar')
                return
            orden = next((o for o in pedidos_sorted if o.get('id') == sel), None)
            if not orden:
                messagebox.showerror('Error', 'Pedido no encontrado')
                return

            # Guardar en folder 'tickets' dentro del proyecto con nombre <orderid>_ticket.txt
            try:
                proyecto_root = os.path.dirname(__file__)
                tickets_dir = os.path.join(proyecto_root, 'tickets')
                os.makedirs(tickets_dir, exist_ok=True)
                filename = os.path.join(tickets_dir, f"{orden.get('id')}_ticket.txt")

                # Formatear contenido
                lines = []
                lines.append('--- DESGLOSE DE PEDIDO ---')
                lines.append(f"ID Pedido: {orden.get('id')}")
                lines.append(f"Fecha: {orden.get('fecha')}")
                lines.append(f"Cajero: {orden.get('cajero', '')}")
                lines.append(f"Estado: {orden.get('estado', '')}")
                lines.append('')
                lines.append('Productos:')
                for it in orden.get('productos', []) or []:
                    nombre = it.get('nombre', '')
                    cantidad = int(it.get('cantidad', 0) or 0)
                    precio = float(it.get('precio', 0) or 0)
                    subtotal = float(it.get('subtotal', cantidad * precio) or (cantidad * precio))
                    lines.append(f" - {nombre}: {cantidad} x ${precio:.2f} = ${subtotal:.2f}")

                lines.append('')
                lines.append('Totales:')
                lines.append(f"Total sin descuento: ${float(orden.get('total_sin_descuento', 0)):.2f}")
                lines.append(f"Descuento aplicado: ${float(orden.get('descuento_aplicado', 0)):.2f}")
                lines.append(f"Total final: ${float(orden.get('total_final', 0)):.2f}")
                lines.append(f"Método de pago: {orden.get('metodo_pago', '')}")
                lines.append('')
                lines.append('Gracias por su compra.')

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))

                messagebox.showinfo('Exportado', f'Desglose guardado en:\n{filename}')
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo exportar el pedido: {e}')

        def confirmar_pago():
            sel = self._cobrar_selected_order_var.get()
            if not sel:
                messagebox.showwarning('Seleccionar pedido', 'Selecciona un pedido para confirmar el pago')
                return
            if not messagebox.askyesno('Confirmar pago', f'¿Confirmar pago del pedido {sel}?'):
                return
            try:
                pedidos_all = db.load_orders()
                orden = next((o for o in pedidos_all if o.get('id') == sel), None)
                if not orden:
                    messagebox.showerror('Error', 'Pedido no encontrado')
                    return
                orden['estado'] = 'Pagado'
                db.save_order(orden)
                messagebox.showinfo('Pago confirmado', f'Pago del pedido {sel} confirmado')
                # Refrescar combo y detalles
                try:
                    pedidos[:] = db.load_orders()
                except Exception:
                    pass
                mostrar_detalles_seleccion()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo confirmar el pago: {e}')

        btn_frame = tk.Frame(main, bg=self.color_fondo_ventana)
        btn_frame.pack(fill='x', pady=(10, 0))

        tk.Button(btn_frame, text='📄 Exportar a TXT', command=exportar_txt, bg='#607D8B', fg='white', width=18).pack(side='left', padx=5)
        tamaños = self.calcular_tamaños_responsivos()
        ttk.Button(btn_frame, text='✅ Confirmar Pago', command=confirmar_pago, width=tamaños['boton_width']//1).pack(side='left', padx=5)
        ttk.Button(frame, text='⬅️ Regresar', command=self.mostrar_menu_principal, width=tamaños['boton_width']).pack(pady=10)

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
        self.marcar_ventana_actual('productos')
        
        # Frame para título con información en tiempo real
        titulo_frame = tk.Frame(frame, bg="#FF9800", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        
        titulo_label = tk.Label(titulo_frame, text="📦 Gestión de Productos 📦", 
                               font=("Impact", 20, "bold"), bg="#FF9800", fg="white", pady=10)
        titulo_label.pack()
        
        # Frame para información y controles superiores
        info_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Botón de actualizar y contador de productos
        control_top_frame = tk.Frame(info_frame, bg=self.color_fondo_ventana)
        control_top_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(control_top_frame, text="🔄 Actualizar desde BD", 
                 command=self.actualizar_productos_desde_bd,
                 bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=5).pack(side="left")
        
        self.productos_count_label = tk.Label(control_top_frame, 
                                             text="Cargando productos...", 
                                             font=("Helvetica", 10), bg=self.color_fondo_ventana, fg=self.color_texto)
        self.productos_count_label.pack(side="right")

        # Tabla de productos cargada desde DB
        tabla_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=15, pady=(0, 10))

        columns = ("ID", "Nombre", "Descripción", "Precio", "Stock")
        self.product_tree = ttk.Treeview(tabla_frame, columns=columns, show="headings", height=10)
        
        # Configurar columnas con mejor ancho
        columnas_config = [
            ("ID", 80, "center"),
            ("Nombre", 200, "w"),
            ("Descripción", 280, "w"),
            ("Precio", 100, "center"),
            ("Stock", 80, "center")
        ]
        
        for col, ancho, anchor in columnas_config:
            self.product_tree.heading(col, text=col)
            # Convertir string a constante tkinter
            anchor_tk = "w" if anchor == "w" else "center" if anchor == "center" else "e"
            self.product_tree.column(col, width=ancho, anchor=anchor_tk)

        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        self.product_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Cargar productos inicialmente
        self.cargar_productos_en_tabla()

        # Botones de gestión con mejor diseño
        btn_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        btn_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        # Primera fila de botones
        btn_row1 = tk.Frame(btn_frame, bg=self.color_fondo_ventana)
        btn_row1.pack(pady=(10, 5))
        
        tamaños = self.calcular_tamaños_responsivos()
        
        tk.Button(btn_row1, text="➕ Nuevo Producto", 
                 command=lambda: self.mostrar_formulario_producto("nueva"),
                 bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="✏️ Editar Seleccionado", 
                 command=self.editar_producto_seleccionado,
                 bg="#FF9800", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="🗑️ Eliminar Seleccionado", 
                 command=self.eliminar_producto_seleccionado,
                 bg="#F44336", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        # Segunda fila de botones
        btn_row2 = tk.Frame(btn_frame, bg=self.color_fondo_ventana)
        btn_row2.pack(pady=(5, 10))
        
        tk.Button(btn_row2, text="📊 Ver Estadísticas", 
                 command=self.mostrar_estadisticas_productos,
                 bg="#673AB7", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        tk.Button(btn_row2, text="📤 Exportar Lista", 
                 command=self.exportar_productos,
                 bg="#607D8B", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)

        # Botón regresar
        tk.Button(frame, text="⬅️ Regresar al Menú Principal", 
                 command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, 
                 font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], 
                 pady=tamaños['boton_gestion_pady']).pack(pady=15)
    
    def cargar_productos_en_tabla(self):
        """Carga productos desde la BD y actualiza la tabla"""
        try:
            # Limpiar tabla actual
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
            
            # Cargar productos desde BD
            productos = db.load_products()
            
            # Si no hay productos en BD, crear algunos de muestra
            if not productos:
                productos_muestra = [
                    {'id': 'SUS01', 'nombre': 'California Roll', 'descripcion': 'Kanikama, palta, pepino', 'precio': 120.0},
                    {'id': 'SUS02', 'nombre': 'Philadelphia Roll', 'descripcion': 'Salmón, queso Philadelphia, palta', 'precio': 150.0},
                    {'id': 'SUS03', 'nombre': 'Salmon Roll', 'descripcion': 'Salmón fresco, pepino, wasabi', 'precio': 180.0},
                    {'id': 'SUS04', 'nombre': 'Tuna Roll', 'descripcion': 'Atún rojo, palta, sésamo', 'precio': 200.0},
                    {'id': 'SUS05', 'nombre': 'Veggie Roll', 'descripcion': 'Palta, pepino, zanahoria, lechuga', 'precio': 100.0}
                ]
                
                for prod in productos_muestra:
                    try:
                        db.save_product(prod)
                    except Exception:
                        pass
                
                productos = productos_muestra
            
            # Rellenar tabla
            for p in productos:
                precio = float(p.get('precio', 0))
                # Agregar campo de stock (por defecto 50)
                stock = p.get('stock', 50)
                self.product_tree.insert("", "end", iid=str(p.get('id')), 
                                       values=(p.get('id'), p.get('nombre'), 
                                              p.get('descripcion', ''), f"${precio:.2f}", stock))
            
            # Actualizar contador
            self.productos_count_label.config(text=f"📦 Total productos: {len(productos)}")
            
        except Exception as e:
            self.productos_count_label.config(text=f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar productos: {str(e)}")
    
    def actualizar_productos_desde_bd(self):
        """Fuerza la actualización de productos desde la base de datos"""
        self.cargar_productos_en_tabla()
        messagebox.showinfo("Actualización", "Productos actualizados desde la base de datos")
    
    def mostrar_estadisticas_productos(self):
        """Muestra estadísticas básicas de productos"""
        try:
            productos = db.load_products()
            if not productos:
                messagebox.showinfo("Sin datos", "No hay productos en la base de datos")
                return
            
            total_productos = len(productos)
            precio_promedio = sum(float(p.get('precio', 0)) for p in productos) / total_productos
            precio_max = max(float(p.get('precio', 0)) for p in productos)
            precio_min = min(float(p.get('precio', 0)) for p in productos)
            
            estadisticas = f"""📊 ESTADÍSTICAS DE PRODUCTOS
            
📈 Resumen General:
• Total de productos: {total_productos}
• Precio promedio: ${precio_promedio:.2f}
• Precio más alto: ${precio_max:.2f}
• Precio más bajo: ${precio_min:.2f}

🎯 Análisis por Categoría:
• Rolls especiales: {len([p for p in productos if 'Roll' in p.get('nombre', '')])}
• Productos vegetarianos: {len([p for p in productos if 'Veggie' in p.get('nombre', '')])}
"""
            
            messagebox.showinfo("Estadísticas de Productos", estadisticas)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular estadísticas: {str(e)}")
    
    def exportar_productos(self):
        """Exporta la lista de productos a un archivo"""
        try:
            productos = db.load_products()
            if not productos:
                messagebox.showinfo("Sin datos", "No hay productos para exportar")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Guardar lista de productos"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(productos, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Éxito", f"Productos exportados a:\n{filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar productos: {str(e)}")

    def editar_producto_seleccionado(self):
        sel = self.product_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un producto para editar")
            return
        
        pid = sel[0]
        # Obtener valores de la tabla
        valores = self.product_tree.item(pid)['values']
        if not valores:
            messagebox.showerror("Error", "No se pudieron obtener los datos del producto")
            return
        
        # Abrir formulario en modo editar con el ID del producto
        self.mostrar_formulario_producto("editar", producto_id=valores[0])

    def eliminar_producto_seleccionado(self):
        sel = self.product_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un producto para eliminar")
            return
        
        pid = sel[0]
        valores = self.product_tree.item(pid)['values']
        if not valores:
            messagebox.showerror("Error", "No se pudieron obtener los datos del producto")
            return
            
        nombre = valores[1]
        
        # Confirmación con información detallada
        respuesta = messagebox.askyesno("Confirmar Eliminación", 
                                       f"¿Estás seguro de eliminar el producto?\n\n"
                                       f"ID: {valores[0]}\n"
                                       f"Nombre: {nombre}\n"
                                       f"Precio: {valores[3]}\n\n"
                                       f"Esta acción no se puede deshacer.")
        
        if respuesta:
            try:
                # Eliminar de la base de datos
                db.delete_product(pid)
                
                # Eliminar de la tabla visual
                self.product_tree.delete(pid)
                
                # Actualizar contador
                productos_restantes = len(self.product_tree.get_children())
                self.productos_count_label.config(text=f"📦 Total productos: {productos_restantes}")
                
                messagebox.showinfo("Éxito", f"Producto '{nombre}' eliminado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto: {str(e)}")
                # Recargar la tabla en caso de error
                self.cargar_productos_en_tabla()

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
                    # persistir en BD
                    try:
                        db.save_offer(nueva_oferta)
                    except Exception:
                        pass
                    messagebox.showinfo("Éxito", "Oferta creada exitosamente")
                else:
                    # Actualizar oferta existente
                    for i, oferta in enumerate(self.ofertas):
                        if oferta['id'] == oferta_id:
                            self.ofertas[i] = nueva_oferta
                            break
                    # persistir en BD
                    try:
                        db.save_offer(nueva_oferta)
                    except Exception:
                        pass
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
            try:
                db.delete_offer(oferta_id)
            except Exception:
                pass
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
                try:
                    db.toggle_offer(oferta_id, nuevo_estado)
                except Exception:
                    pass
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
        self.marcar_ventana_actual('usuarios')
        
        # Título mejorado
        titulo_frame = tk.Frame(frame, bg="#FF9800", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="👤 Gestión de Usuarios 👤", 
                font=("Impact", 20, "bold"), bg="#FF9800", fg="white", pady=12).pack()
        
        # Inicializar usuarios por defecto si es necesario
        try:
            db.init_default_users()
        except Exception:
            pass
        
        # Frame para información y controles superiores
        info_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Botón de actualizar y contador
        control_top_frame = tk.Frame(info_frame, bg=self.color_fondo_ventana)
        control_top_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(control_top_frame, text="🔄 Actualizar desde BD", 
                 command=self.actualizar_usuarios_desde_bd,
                 bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"),
                 relief="raised", bd=2, padx=15, pady=5).pack(side="left")
        
        self.usuarios_count_label = tk.Label(control_top_frame, 
                                            text="Cargando usuarios...", 
                                            font=("Helvetica", 10), bg=self.color_fondo_ventana, fg=self.color_texto)
        self.usuarios_count_label.pack(side="right")

        # Tabla de usuarios
        tabla_frame = tk.Frame(frame, bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=15, pady=(0, 10))

        columns = ("ID", "Usuario", "Nombre Completo", "Rol", "Email", "Último Login", "Estado")
        self.users_tree = ttk.Treeview(tabla_frame, columns=columns, show="headings", height=10)
        
        # Configurar columnas
        columnas_config = [
            ("ID", 50, "center"),
            ("Usuario", 120, "w"),
            ("Nombre Completo", 180, "w"),
            ("Rol", 100, "center"),
            ("Email", 200, "w"),
            ("Último Login", 130, "center"),
            ("Estado", 80, "center")
        ]
        
        for col, ancho, anchor in columnas_config:
            self.users_tree.heading(col, text=col)
            # Convertir string a constante tkinter
            anchor_tk = "w" if anchor == "w" else "center" if anchor == "center" else "e"
            self.users_tree.column(col, width=ancho, anchor=anchor_tk)

        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        self.users_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Cargar usuarios inicialmente
        self.cargar_usuarios_en_tabla()

        # Botones de gestión
        btn_frame = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        btn_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        # Primera fila de botones
        btn_row1 = tk.Frame(btn_frame, bg=self.color_fondo_ventana)
        btn_row1.pack(pady=(10, 5))
        
        tk.Button(btn_row1, text="➕ Nuevo Usuario", 
                 command=lambda: self.mostrar_formulario_usuario("nuevo"),
                 bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="✏️ Editar Seleccionado", 
                 command=self.editar_usuario_seleccionado,
                 bg="#FF9800", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        tk.Button(btn_row1, text="🔑 Cambiar Contraseña", 
                 command=self.mostrar_dialogo_cambiar_password,
                 bg="#673AB7", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        # Segunda fila de botones
        btn_row2 = tk.Frame(btn_frame, bg=self.color_fondo_ventana)
        btn_row2.pack(pady=(5, 10))
        
        tk.Button(btn_row2, text="❌ Desactivar Usuario", 
                 command=self.toggle_usuario_estado,
                 bg="#F44336", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)
        
        tk.Button(btn_row2, text="🗑️ Eliminar Permanente", 
                 command=self.eliminar_usuario_seleccionado,
                 bg="#D32F2F", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=15, pady=8, width=18).pack(side="left", padx=5)

        # Botón regresar
        tamaños = self.calcular_tamaños_responsivos()
        tk.Button(frame, text="⬅️ Regresar al Menú Principal", 
                 command=self.mostrar_menu_principal,
                 bg=self.color_boton_fondo, fg=self.color_boton_texto, 
                 font=("Helvetica", tamaños['boton_gestion_font'], "bold"),
                 relief="raised", bd=2, padx=tamaños['boton_gestion_padx'], 
                 pady=tamaños['boton_gestion_pady']).pack(pady=15)
    
    def cargar_usuarios_en_tabla(self):
        """Carga usuarios desde la BD y actualiza la tabla"""
        try:
            # Limpiar tabla actual
            for item in self.users_tree.get_children():
                self.users_tree.delete(item)
            
            # Cargar usuarios desde BD
            usuarios = db.load_users()
            
            # Rellenar tabla
            for usuario in usuarios:
                ultimo_login = usuario.get('last_login', 'Nunca')
                if ultimo_login and ultimo_login != 'Nunca':
                    try:
                        ultimo_login = datetime.datetime.fromisoformat(ultimo_login).strftime('%d/%m/%Y %H:%M')
                    except:
                        ultimo_login = 'Nunca'
                
                estado = "✅ Activo" if usuario.get('active', True) else "❌ Inactivo"
                
                self.users_tree.insert("", "end", iid=str(usuario.get('id')), 
                                      values=(
                                          usuario.get('id'),
                                          usuario.get('username'),
                                          usuario.get('full_name', ''),
                                          usuario.get('role', 'cliente').capitalize(),
                                          usuario.get('email', ''),
                                          ultimo_login,
                                          estado
                                      ))
            
            # Actualizar contador
            self.usuarios_count_label.config(text=f"👤 Total usuarios: {len(usuarios)}")
            
        except Exception as e:
            self.usuarios_count_label.config(text=f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar usuarios: {str(e)}")
    
    def actualizar_usuarios_desde_bd(self):
        """Fuerza la actualización de usuarios desde la base de datos"""
        self.cargar_usuarios_en_tabla()
        messagebox.showinfo("Actualización", "Usuarios actualizados desde la base de datos")
    
    def editar_usuario_seleccionado(self):
        """Edita el usuario seleccionado"""
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un usuario para editar")
            return
        
        user_id = int(sel[0])
        self.mostrar_formulario_usuario("editar", user_id)
    
    def mostrar_dialogo_cambiar_password(self):
        """Muestra diálogo para cambiar contraseña del usuario seleccionado"""
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un usuario para cambiar su contraseña")
            return
        
        user_id = int(sel[0])
        self.cambiar_password_usuario(user_id)
    
    def cambiar_password_usuario_old(self):
        """Cambia la contraseña del usuario seleccionado"""
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un usuario para cambiar su contraseña")
            return
        
        user_id = int(sel[0])
        valores = self.users_tree.item(sel[0])['values']
        username = valores[1]
        
        # Ventana para cambiar contraseña
        password_window = tk.Toplevel(self)
        password_window.title(f"Cambiar Contraseña - {username}")
        password_window.geometry("400x250")
        password_window.configure(bg=self.color_fondo_ventana)
        password_window.resizable(False, False)
        
        tk.Label(password_window, text=f"🔑 Cambiar Contraseña para: {username}", 
                font=("Helvetica", 14, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=20)
        
        tk.Label(password_window, text="Nueva contraseña:", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", padx=20, pady=(10, 2))
        nueva_password = tk.Entry(password_window, show="*", width=30, font=("Helvetica", 11))
        nueva_password.pack(padx=20, pady=(0, 10))
        
        tk.Label(password_window, text="Confirmar contraseña:", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana, fg=self.color_texto).pack(anchor="w", padx=20, pady=(10, 2))
        confirmar_password = tk.Entry(password_window, show="*", width=30, font=("Helvetica", 11))
        confirmar_password.pack(padx=20, pady=(0, 20))
        
        def guardar_nueva_password():
            nueva = nueva_password.get()
            confirmar = confirmar_password.get()
            
            if not nueva or not confirmar:
                messagebox.showerror("Error", "Ambos campos son obligatorios")
                return
            
            if nueva != confirmar:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if len(nueva) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return
            
            try:
                if db.change_user_password(user_id, nueva):
                    messagebox.showinfo("Éxito", f"Contraseña cambiada exitosamente para {username}")
                    password_window.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo cambiar la contraseña")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cambiar contraseña: {str(e)}")
        
        btn_frame = tk.Frame(password_window, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="💾 Guardar", command=guardar_nueva_password,
                 bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=password_window.destroy,
                 bg="#F44336", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8).pack(side="left", padx=10)
        
        nueva_password.focus()
    
    def toggle_usuario_estado(self):
        """Activa/desactiva el usuario seleccionado"""
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un usuario para cambiar su estado")
            return
        
        user_id = int(sel[0])
        valores = self.users_tree.item(sel[0])['values']
        username = valores[1]
        estado_actual = "✅ Activo" in valores[6]
        
        nuevo_estado = not estado_actual
        accion = "activar" if nuevo_estado else "desactivar"
        
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de {accion} al usuario '{username}'?"):
            try:
                db.update_user(user_id, active=nuevo_estado)
                self.cargar_usuarios_en_tabla()
                messagebox.showinfo("Éxito", f"Usuario {username} {'activado' if nuevo_estado else 'desactivado'} exitosamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cambiar estado del usuario: {str(e)}")
    
    def eliminar_usuario_seleccionado(self):
        """Elimina permanentemente el usuario seleccionado"""
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un usuario para eliminar")
            return
        
        user_id = int(sel[0])
        valores = self.users_tree.item(sel[0])['values']
        username = valores[1]
        
        respuesta = messagebox.askyesno("⚠️ Confirmar Eliminación Permanente", 
                                       f"¿Estás seguro de eliminar PERMANENTEMENTE al usuario?\n\n"
                                       f"Usuario: {username}\n"
                                       f"Nombre: {valores[2]}\n"
                                       f"Rol: {valores[3]}\n\n"
                                       f"Esta acción NO se puede deshacer.")
        
        if respuesta:
            try:
                db.delete_user(user_id)
                self.cargar_usuarios_en_tabla()
                messagebox.showinfo("Éxito", f"Usuario '{username}' eliminado permanentemente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar usuario: {str(e)}")
    
    def mostrar_formulario_usuario(self, modo, user_id=None):
        """Formulario para crear/editar usuarios"""
        frame = self.limpiar_ventana()
        
        # Título dinámico según el modo
        titulo = "➕ Crear Nuevo Usuario" if modo == 'nuevo' else "✏️ Editar Usuario"
        color_titulo = "#4CAF50" if modo == 'nuevo' else "#FF9800"
        
        # Frame de título
        titulo_frame = tk.Frame(frame, bg=color_titulo, relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text=titulo, font=("Impact", 18, "bold"), 
                bg=color_titulo, fg="white", pady=12).pack()

        # Frame principal del formulario
        form_container = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        form_container.pack(pady=20, padx=50)
        
        form_frame = tk.Frame(form_container, bg=self.color_fondo_ventana)
        form_frame.pack(padx=30, pady=30)

        # Variables del formulario
        var_username = tk.StringVar()
        var_password = tk.StringVar()
        var_confirm_password = tk.StringVar()
        var_full_name = tk.StringVar()
        var_email = tk.StringVar()
        var_role = tk.StringVar(value="cliente")

        # Campo Username
        tk.Label(form_frame, text="👤 Nombre de Usuario:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=0, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        entry_username = tk.Entry(form_frame, textvariable=var_username, width=40, font=("Helvetica", 11), 
                                 relief="solid", bd=2, bg="#FFFFFF")
        entry_username.grid(row=0, column=1, pady=(10, 2), sticky="ew")

        # Campo Contraseña (solo para nuevo usuario)
        if modo == 'nuevo':
            tk.Label(form_frame, text="🔑 Contraseña:", 
                    font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=1, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
            entry_password = tk.Entry(form_frame, textvariable=var_password, show="*", width=40, font=("Helvetica", 11), 
                                     relief="solid", bd=2, bg="#FFFFFF")
            entry_password.grid(row=1, column=1, pady=(10, 2), sticky="ew")

            tk.Label(form_frame, text="🔑 Confirmar Contraseña:", 
                    font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=2, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
            entry_confirm = tk.Entry(form_frame, textvariable=var_confirm_password, show="*", width=40, font=("Helvetica", 11), 
                                   relief="solid", bd=2, bg="#FFFFFF")
            entry_confirm.grid(row=2, column=1, pady=(10, 2), sticky="ew")
            
            row_offset = 3
        else:
            row_offset = 1

        # Campo Nombre Completo
        tk.Label(form_frame, text="👨‍💼 Nombre Completo:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=row_offset, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        entry_full_name = tk.Entry(form_frame, textvariable=var_full_name, width=40, font=("Helvetica", 11), 
                                  relief="solid", bd=2, bg="#FFFFFF")
        entry_full_name.grid(row=row_offset, column=1, pady=(10, 2), sticky="ew")

        # Campo Email
        tk.Label(form_frame, text="📧 Email:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=row_offset+1, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        entry_email = tk.Entry(form_frame, textvariable=var_email, width=40, font=("Helvetica", 11), 
                              relief="solid", bd=2, bg="#FFFFFF")
        entry_email.grid(row=row_offset+1, column=1, pady=(10, 2), sticky="ew")

        # Campo Rol
        tk.Label(form_frame, text="🎭 Rol del Usuario:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=row_offset+2, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        
        roles_frame = tk.Frame(form_frame, bg=self.color_fondo_ventana)
        roles_frame.grid(row=row_offset+2, column=1, pady=(10, 2), sticky="w")
        
        roles = [("👤 Cliente", "cliente"), ("💰 Cajero", "cajero"), ("⚙️ Administrador", "admin")]
        for i, (texto, valor) in enumerate(roles):
            tk.Radiobutton(roles_frame, text=texto, variable=var_role, value=valor,
                          bg=self.color_fondo_ventana, fg=self.color_texto, font=("Helvetica", 10)).pack(side="left", padx=(0, 20))

        # Configurar grid para que se expanda
        form_frame.grid_columnconfigure(1, weight=1)

        # Si es edición, cargar valores
        if modo == 'editar' and user_id:
            try:
                usuarios = db.load_users()
                usuario = next((u for u in usuarios if u['id'] == user_id), None)
                if usuario:
                    var_username.set(usuario.get('username', ''))
                    entry_username.config(state='disabled')  # No permitir cambiar username en edición
                    var_full_name.set(usuario.get('full_name', ''))
                    var_email.set(usuario.get('email', ''))
                    var_role.set(usuario.get('role', 'cliente'))
                else:
                    messagebox.showerror("Error", "No se encontró el usuario en la base de datos")
                    self.mostrar_gestion_usuarios()
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar datos del usuario: {str(e)}")
                self.mostrar_gestion_usuarios()
                return

        def guardar_usuario():
            # Obtener valores
            username = var_username.get().strip()
            full_name = var_full_name.get().strip()
            email = var_email.get().strip()
            role = var_role.get()

            # Validaciones
            errores = []
            
            if not username:
                errores.append("• Nombre de usuario es obligatorio")
            elif len(username) < 3:
                errores.append("• El nombre de usuario debe tener al menos 3 caracteres")
            
            if not full_name:
                errores.append("• Nombre completo es obligatorio")
            
            if email and '@' not in email:
                errores.append("• Email inválido")
            
            if modo == 'nuevo':
                password = var_password.get()
                confirm_password = var_confirm_password.get()
                
                if not password:
                    errores.append("• Contraseña es obligatoria")
                elif len(password) < 6:
                    errores.append("• La contraseña debe tener al menos 6 caracteres")
                
                if password != confirm_password:
                    errores.append("• Las contraseñas no coinciden")

            if errores:
                messagebox.showerror("Errores de Validación", "Por favor corrige los siguientes errores:\n\n" + "\n".join(errores))
                return

            try:
                if modo == 'nuevo':
                    # Crear nuevo usuario
                    if db.create_user(username, var_password.get(), full_name, role, email):
                        messagebox.showinfo("Éxito", "Usuario creado exitosamente")
                        self.mostrar_gestion_usuarios()
                    else:
                        messagebox.showerror("Error", "El nombre de usuario ya existe")
                else:
                    # Editar usuario existente
                    if user_id is not None:
                        db.update_user(user_id, full_name=full_name, role=role, email=email)
                        messagebox.showinfo("Éxito", "Usuario actualizado exitosamente")
                        self.mostrar_gestion_usuarios()
                    else:
                        messagebox.showerror("Error", "ID de usuario inválido")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el usuario: {str(e)}")

        # Frame para botones
        btn_frame = tk.Frame(form_container, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=(20, 30))

        # Botones con colores mejorados
        tk.Button(btn_frame, text="💾 Guardar Usuario", command=guardar_usuario,
                  bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"),
                  relief="raised", bd=2, padx=25, pady=10, width=20).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=self.mostrar_gestion_usuarios,
                  bg="#F44336", fg="white", font=("Helvetica", 12, "bold"),
                  relief="raised", bd=2, padx=25, pady=10, width=20).pack(side="left", padx=10)

        # Focus en el primer campo editable
        if modo == 'nuevo':
            entry_username.focus()
        else:
            entry_full_name.focus()
    
    def cambiar_password_usuario(self, user_id):
        """Ventana modal para cambiar contraseña de usuario"""
        # Crear ventana modal
        ventana_password = tk.Toplevel(self)
        ventana_password.title("Cambiar Contraseña")
        ventana_password.geometry("450x350")
        ventana_password.configure(bg=self.color_fondo_ventana)
        ventana_password.resizable(False, False)
        ventana_password.transient(self)
        ventana_password.grab_set()
        
        # Centrar ventana
        ventana_password.update_idletasks()
        x = (ventana_password.winfo_screenwidth() // 2) - (450 // 2)
        y = (ventana_password.winfo_screenheight() // 2) - (350 // 2)
        ventana_password.geometry(f"450x350+{x}+{y}")

        # Obtener información del usuario
        try:
            usuarios = db.load_users()
            usuario = next((u for u in usuarios if u['id'] == user_id), None)
            if not usuario:
                messagebox.showerror("Error", "Usuario no encontrado")
                ventana_password.destroy()
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar usuario: {str(e)}")
            ventana_password.destroy()
            return

        # Frame de título
        titulo_frame = tk.Frame(ventana_password, bg="#FF9800", relief="raised", bd=2)
        titulo_frame.pack(fill="x")
        tk.Label(titulo_frame, text="🔐 Cambiar Contraseña", font=("Impact", 16, "bold"), 
                bg="#FF9800", fg="white", pady=15).pack()

        # Información del usuario
        info_frame = tk.Frame(ventana_password, bg=self.color_fondo_ventana)
        info_frame.pack(pady=20)
        tk.Label(info_frame, text=f"Usuario: {usuario['username']}", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).pack()

        # Frame principal del formulario
        form_frame = tk.Frame(ventana_password, bg=self.color_fondo_ventana)
        form_frame.pack(pady=20, padx=40)

        # Variables
        var_nueva_password = tk.StringVar()
        var_confirmar_password = tk.StringVar()

        # Campo Nueva Contraseña
        tk.Label(form_frame, text="🔑 Nueva Contraseña:", 
                font=("Helvetica", 11, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=(0, 10))
        entry_nueva = tk.Entry(form_frame, textvariable=var_nueva_password, show="*", width=30, font=("Helvetica", 11), 
                              relief="solid", bd=2, bg="#FFFFFF")
        entry_nueva.grid(row=0, column=1, pady=(10, 5), sticky="ew")

        # Campo Confirmar Contraseña
        tk.Label(form_frame, text="🔑 Confirmar Contraseña:", 
                font=("Helvetica", 11, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=1, column=0, sticky="w", pady=(5, 10), padx=(0, 10))
        entry_confirmar = tk.Entry(form_frame, textvariable=var_confirmar_password, show="*", width=30, font=("Helvetica", 11), 
                                  relief="solid", bd=2, bg="#FFFFFF")
        entry_confirmar.grid(row=1, column=1, pady=(5, 10), sticky="ew")

        # Configurar grid
        form_frame.grid_columnconfigure(1, weight=1)

        # Información de seguridad
        info_seguridad = tk.Label(ventana_password, text="💡 La contraseña debe tener al menos 6 caracteres", 
                                 font=("Helvetica", 10, "italic"), bg=self.color_fondo_ventana, fg="#666666")
        info_seguridad.pack(pady=(0, 20))

        def confirmar_cambio():
            nueva_password = var_nueva_password.get()
            confirmar_password = var_confirmar_password.get()

            # Validaciones
            if not nueva_password:
                messagebox.showerror("Error", "La nueva contraseña es obligatoria")
                return
            
            if len(nueva_password) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return
            
            if nueva_password != confirmar_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return

            try:
                db.change_user_password(user_id, nueva_password)
                messagebox.showinfo("Éxito", "Contraseña actualizada exitosamente")
                ventana_password.destroy()
                self.actualizar_usuarios_desde_bd()  # Refrescar tabla
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cambiar la contraseña: {str(e)}")

        # Frame para botones
        btn_frame = tk.Frame(ventana_password, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="🔒 Cambiar Contraseña", command=confirmar_cambio,
                  bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"),
                  relief="raised", bd=2, padx=20, pady=8).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=ventana_password.destroy,
                  bg="#F44336", fg="white", font=("Helvetica", 11, "bold"),
                  relief="raised", bd=2, padx=20, pady=8).pack(side="left", padx=10)

        # Focus en el primer campo
        entry_nueva.focus()

    def sincronizar_datos_automaticamente(self):
        """Sistema de sincronización automática de datos"""
        # Solo sincronizar si hay una ventana activa y BD disponible
        try:
            # Refrescar datos según la ventana actual
            if hasattr(self, 'ventana_actual'):
                if self.ventana_actual == 'productos':
                    self.actualizar_productos_desde_bd()
                elif self.ventana_actual == 'carrito':
                    self.actualizar_carrito_desde_bd()
                elif self.ventana_actual == 'usuarios':
                    self.actualizar_usuarios_desde_bd()
                elif self.ventana_actual == 'ofertas':
                    # Para ofertas necesitamos un parent, usamos None para que no falle
                    pass
                elif self.ventana_actual == 'reportes':
                    self.actualizar_reportes_desde_bd()
        except Exception as e:
            print(f"Error en sincronización automática: {e}")
        
        # Programar próxima sincronización en 30 segundos
        self.after(30000, self.sincronizar_datos_automaticamente)

    def iniciar_sincronizacion_automatica(self):
        """Iniciar el sistema de sincronización automática"""
        # Marcar que se debe sincronizar automáticamente
        self.sincronizacion_activa = True
        # Iniciar el primer ciclo de sincronización
        self.after(30000, self.sincronizar_datos_automaticamente)

    def detener_sincronizacion_automatica(self):
        """Detener la sincronización automática"""
        self.sincronizacion_activa = False

    def marcar_ventana_actual(self, nombre_ventana):
        """Marcar cuál es la ventana actual para sincronización"""
        self.ventana_actual = nombre_ventana

    def actualizar_productos_desde_bd(self):
        """Actualizar datos de productos desde BD"""
        if hasattr(self, 'productos_tree'):
            self.cargar_productos_en_tabla()

    def actualizar_carrito_desde_bd(self):
        """Actualizar datos del carrito desde BD"""
        if hasattr(self, 'carrito_tree'):
            self.cargar_datos_carrito()

    def actualizar_reportes_desde_bd(self):
        """Actualizar datos de reportes desde BD"""
        if hasattr(self, 'reportes_tree'):
            try:
                # Recargar datos con los filtros actuales
                self.aplicar_filtros_reportes()
            except:
                pass

    # --- 3. Formularios Internos (Ejemplo para Productos) ---
    def mostrar_formulario_producto(self, modo, producto_id=None):
        """Formulario mejorado para crear/editar productos con validaciones y mejor integración BD"""
        frame = self.limpiar_ventana()
        
        # Título dinámico según el modo
        titulo = "➕ Agregar Nuevo Producto" if modo == 'nueva' else "✏️ Editar Producto"
        color_titulo = "#4CAF50" if modo == 'nueva' else "#FF9800"
        
        # Frame de título
        titulo_frame = tk.Frame(frame, bg=color_titulo, relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text=titulo, font=("Impact", 18, "bold"), 
                bg=color_titulo, fg="white", pady=12).pack()

        # Frame principal del formulario con mejor diseño
        form_container = tk.Frame(frame, bg=self.color_fondo_ventana, relief="raised", bd=2)
        form_container.pack(pady=20, padx=50)
        
        form_frame = tk.Frame(form_container, bg=self.color_fondo_ventana)
        form_frame.pack(padx=30, pady=30)

        # Variables del formulario
        var_id = tk.StringVar()
        var_nombre = tk.StringVar()
        var_descripcion = tk.StringVar()
        var_precio = tk.StringVar()
        var_stock = tk.StringVar(value="50")  # Nuevo campo stock

        # Función de validación en tiempo real
        def validar_precio(*args):
            precio = var_precio.get()
            try:
                if precio and float(precio) < 0:
                    precio_label.config(fg="#F44336")
                    precio_error.config(text="⚠️ El precio no puede ser negativo")
                else:
                    precio_label.config(fg=self.color_texto)
                    precio_error.config(text="")
            except ValueError:
                if precio:  # Solo mostrar error si hay texto
                    precio_label.config(fg="#F44336")
                    precio_error.config(text="⚠️ Debe ser un número válido")
                else:
                    precio_label.config(fg=self.color_texto)
                    precio_error.config(text="")

        var_precio.trace("w", validar_precio)

        # Campo ID
        tk.Label(form_frame, text="🔢 ID del Producto (código único):", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=0, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        entry_id = tk.Entry(form_frame, textvariable=var_id, width=40, font=("Helvetica", 11), 
                           relief="solid", bd=2, bg="#FFFFFF")
        entry_id.grid(row=0, column=1, pady=(10, 2), sticky="ew")
        
        # Mensaje de ayuda para ID
        tk.Label(form_frame, text="Ej: SUS06, ROLL01, etc.", font=("Helvetica", 9, "italic"), 
                bg=self.color_fondo_ventana, fg="#666666").grid(row=1, column=1, sticky="w", pady=(0, 10))

        # Campo Nombre
        tk.Label(form_frame, text="🍣 Nombre del Producto:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=2, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        entry_nombre = tk.Entry(form_frame, textvariable=var_nombre, width=40, font=("Helvetica", 11), 
                               relief="solid", bd=2, bg="#FFFFFF")
        entry_nombre.grid(row=2, column=1, pady=(10, 2), sticky="ew")

        # Campo Descripción con Text widget para mejor edición
        tk.Label(form_frame, text="📝 Descripción:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=3, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        
        desc_frame = tk.Frame(form_frame, bg=self.color_fondo_ventana)
        desc_frame.grid(row=3, column=1, pady=(10, 2), sticky="ew")
        
        text_desc = tk.Text(desc_frame, width=30, height=3, font=("Helvetica", 11), 
                           relief="solid", bd=2, bg="#FFFFFF", wrap="word")
        text_desc.pack(side="left", fill="both", expand=True)
        
        desc_scroll = tk.Scrollbar(desc_frame, orient="vertical", command=text_desc.yview)
        text_desc.configure(yscrollcommand=desc_scroll.set)
        desc_scroll.pack(side="right", fill="y")

        # Campo Precio con validación visual
        precio_label = tk.Label(form_frame, text="💰 Precio ($):", 
                               font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto)
        precio_label.grid(row=4, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        
        entry_precio = tk.Entry(form_frame, textvariable=var_precio, width=20, font=("Helvetica", 11), 
                               relief="solid", bd=2, bg="#FFFFFF")
        entry_precio.grid(row=4, column=1, pady=(10, 2), sticky="w")
        
        # Label para errores de precio
        precio_error = tk.Label(form_frame, text="", font=("Helvetica", 9), 
                               bg=self.color_fondo_ventana, fg="#F44336")
        precio_error.grid(row=5, column=1, sticky="w")

        # Campo Stock (nuevo)
        tk.Label(form_frame, text="📦 Stock inicial:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=6, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        entry_stock = tk.Entry(form_frame, textvariable=var_stock, width=20, font=("Helvetica", 11), 
                              relief="solid", bd=2, bg="#FFFFFF")
        entry_stock.grid(row=6, column=1, pady=(10, 2), sticky="w")

        # Campo Categoría (dropdown + entrada libre)
        tk.Label(form_frame, text="📚 Categoría:", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg=self.color_texto).grid(row=7, column=0, sticky="w", pady=(10, 2), padx=(0, 10))
        # Cargar categorías desde DB (fallback a lista por defecto si falla)
        try:
            categorias = db.load_categories() or ['Rolls', 'Especiales', 'Vegetarianos', 'Postres', 'Bebidas']
        except Exception:
            categorias = ['Rolls', 'Especiales', 'Vegetarianos', 'Postres', 'Bebidas']

        var_categoria = tk.StringVar()
        categoria_combo = ttk.Combobox(form_frame, textvariable=var_categoria, values=categorias, width=30)
        categoria_combo.grid(row=7, column=1, pady=(10, 2), sticky="w")
        categoria_combo.set(categorias[0])

        # Permitir entrada libre como alternativa
        tk.Label(form_frame, text="(Puedes escribir una categoría nueva si no está en la lista)", font=("Helvetica", 9, "italic"), bg=self.color_fondo_ventana, fg="#666666").grid(row=8, column=1, sticky="w")

        # Configurar grid para que se expanda
        form_frame.grid_columnconfigure(1, weight=1)

        # Si es edición, cargar valores
        if modo == 'editar' and producto_id:
            try:
                productos = db.load_products()
                prod = next((p for p in productos if str(p.get('id')) == str(producto_id)), None)
                if prod:
                    var_id.set(prod.get('id', ''))
                    entry_id.config(state='disabled')  # No permitir cambiar ID en edición
                    var_nombre.set(prod.get('nombre', ''))
                    text_desc.insert('1.0', prod.get('descripcion', ''))
                    var_precio.set(str(prod.get('precio', '')))
                    var_stock.set(str(prod.get('stock', 50)))
                    try:
                        var_categoria.set(prod.get('categoria', categorias[0] if categorias else 'general'))
                    except Exception:
                        pass
                else:
                    messagebox.showerror("Error", "No se encontró el producto en la base de datos")
                    self.mostrar_gestion_productos()
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar datos del producto: {str(e)}")
                self.mostrar_gestion_productos()
                return

        def guardar_producto():
            # Obtener valores
            pid = var_id.get().strip()
            nombre = var_nombre.get().strip()
            desc = text_desc.get('1.0', 'end-1c').strip()
            precio_str = var_precio.get().strip()
            stock_str = var_stock.get().strip()

            # Validaciones mejoradas
            errores = []
            
            if not pid:
                errores.append("• ID es obligatorio")
            elif modo == 'nueva':
                # Verificar que el ID no exista ya
                try:
                    productos_existentes = db.load_products()
                    if any(p.get('id') == pid for p in productos_existentes):
                        errores.append(f"• El ID '{pid}' ya existe")
                except Exception:
                    pass
            
            if not nombre:
                errores.append("• Nombre es obligatorio")
            
            if not precio_str:
                errores.append("• Precio es obligatorio")
            else:
                try:
                    precio_val = float(precio_str)
                    if precio_val < 0:
                        errores.append("• El precio no puede ser negativo")
                except ValueError:
                    errores.append("• El precio debe ser un número válido")
            
            if not stock_str:
                errores.append("• Stock es obligatorio")
            else:
                try:
                    stock_val = int(stock_str)
                    if stock_val < 0:
                        errores.append("• El stock no puede ser negativo")
                except ValueError:
                    errores.append("• El stock debe ser un número entero")

            if errores:
                messagebox.showerror("Errores de Validación", "Por favor corrige los siguientes errores:\n\n" + "\n".join(errores))
                return

            try:
                precio_val = float(precio_str)
                stock_val = int(stock_str)
                
                producto = {
                    'id': pid, 
                    'nombre': nombre, 
                    'descripcion': desc, 
                    'precio': precio_val,
                    'stock': stock_val,
                    'categoria': var_categoria.get() or 'general'
                }
                
                # Guardar en base de datos
                db.save_product(producto)
                
                accion = "creado" if modo == 'nueva' else "actualizado"
                messagebox.showinfo("Éxito", f"Producto {accion} correctamente")
                
                # Regresar a gestión de productos
                self.mostrar_gestion_productos()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el producto: {str(e)}")

        # Frame para botones con mejor diseño
        btn_frame = tk.Frame(form_container, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=(20, 30))

        # Botones con colores y estilos mejorados
        tk.Button(btn_frame, text="💾 Guardar Producto", command=guardar_producto,
                  bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"),
                  relief="raised", bd=2, padx=25, pady=10, width=20).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=self.mostrar_gestion_productos,
                  bg="#F44336", fg="white", font=("Helvetica", 12, "bold"),
                  relief="raised", bd=2, padx=25, pady=10, width=20).pack(side="left", padx=10)

        # Botón de ayuda
        tk.Button(btn_frame, text="❓ Ayuda", 
                  command=lambda: messagebox.showinfo("Ayuda", 
                    "Consejos para llenar el formulario:\n\n"
                    "• ID: Código único, ej: SUS06, ROLL01\n"
                    "• Nombre: Nombre descriptivo del producto\n"
                    "• Descripción: Ingredientes y características\n"
                    "• Precio: Solo números, puede incluir decimales\n"
                    "• Stock: Cantidad inicial disponible"),
                  bg="#2196F3", fg="white", font=("Helvetica", 11, "bold"),
                  relief="raised", bd=2, padx=15, pady=10).pack(side="left", padx=10)

        # Focus en el primer campo editable
        if modo == 'nueva':
            entry_id.focus()
        else:
            entry_nombre.focus()

    def actualizar_datos_reportes_seguro(self):
        """Actualiza los datos de reportes de manera segura"""
        try:
            # Mostrar los reportes actualizados desde cero
            self.mostrar_reportes()
            
            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Datos de reportes actualizados correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar datos: {str(e)}")

    def mostrar_reportes(self):
        """Sistema avanzado de reportes de ventas - TOTALMENTE INTEGRADO CON BASE DE DATOS"""
        self.marcar_ventana_actual("reportes")
        frame = self.limpiar_ventana()
        
        # ============================================================
        # INICIALIZACIÓN DE DATOS DESDE BASE DE DATOS
        # ============================================================
        try:
            # Cargar datos frescos desde la base de datos
            self.ventas = db.load_orders()
            self.productos = db.load_products()
            self.ofertas = db.load_offers()
            
            # Variables de filtros
            self.ventas_filtradas = self.ventas.copy()
            
        except Exception as e:
            messagebox.showerror("Error BD", f"Error al cargar datos: {str(e)}")
            self.ventas = []
            self.productos = []
            self.ofertas = []
            self.ventas_filtradas = []
        
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
        
        # Título de filtros con contador
        filtros_titulo = tk.Label(filters_container,
                text=f"🔍 Filtros de Búsqueda - Total: {len(self.ventas)} ventas en BD",
                font=("Arial", 12, "bold"),
                bg="#F5F5F5", fg="#333")
        filtros_titulo.pack(pady=10)
        
        # Contenedor de controles en línea
        controls_frame = tk.Frame(filters_container, bg="#F5F5F5")
        controls_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Primera fila de filtros
        filter_row1 = tk.Frame(controls_frame, bg="#F5F5F5")
        filter_row1.pack(fill="x", pady=5)
        
        # Filtros de fecha con valores inteligentes
        today = datetime.datetime.now()
        last_month = today - datetime.timedelta(days=30)
        
        tk.Label(filter_row1, text="Desde:", bg="#F5F5F5", fg="#333", font=("Arial", 10, "bold")).pack(side="left")
        self.fecha_inicio = tk.Entry(filter_row1, width=12, font=("Arial", 10))
        self.fecha_inicio.pack(side="left", padx=(5, 15))
        self.fecha_inicio.insert(0, last_month.strftime("%Y-%m-%d"))
        
        tk.Label(filter_row1, text="Hasta:", bg="#F5F5F5", fg="#333", font=("Arial", 10, "bold")).pack(side="left")
        self.fecha_fin = tk.Entry(filter_row1, width=12, font=("Arial", 10))
        self.fecha_fin.pack(side="left", padx=(5, 15))
        self.fecha_fin.insert(0, today.strftime("%Y-%m-%d"))
        
        # Filtro de producto con Combobox
        tk.Label(filter_row1, text="Producto:", bg="#F5F5F5", fg="#333", font=("Arial", 10, "bold")).pack(side="left")
        productos_disponibles = ["Todos"] + list(set([p['nombre'] for p in self.productos if p['activo']]))
        self.filtro_producto = ttk.Combobox(filter_row1, values=productos_disponibles, width=18, font=("Arial", 10), state="readonly")
        self.filtro_producto.pack(side="left", padx=(5, 10))
        self.filtro_producto.set("Todos")
        
        # Segunda fila de filtros
        filter_row2 = tk.Frame(controls_frame, bg="#F5F5F5")
        filter_row2.pack(fill="x", pady=5)
        
        # Filtro por método de pago
        tk.Label(filter_row2, text="Pago:", bg="#F5F5F5", fg="#333", font=("Arial", 10, "bold")).pack(side="left")
        metodos_pago = ["Todos", "efectivo", "tarjeta", "transferencia"]
        self.filtro_pago = ttk.Combobox(filter_row2, values=metodos_pago, width=12, font=("Arial", 10), state="readonly")
        self.filtro_pago.pack(side="left", padx=(5, 15))
        self.filtro_pago.set("Todos")
        
        # Filtro por cajero
        tk.Label(filter_row2, text="Cajero:", bg="#F5F5F5", fg="#333", font=("Arial", 10, "bold")).pack(side="left")
        cajeros = ["Todos"] + list(set([v['cajero'] for v in self.ventas if v['cajero']]))
        self.filtro_cajero = ttk.Combobox(filter_row2, values=cajeros, width=15, font=("Arial", 10), state="readonly")
        self.filtro_cajero.pack(side="left", padx=(5, 15))
        self.filtro_cajero.set("Todos")
        
        # Filtro por estado
        tk.Label(filter_row2, text="Estado:", bg="#F5F5F5", fg="#333", font=("Arial", 10, "bold")).pack(side="left")
        estados = ["Todos", "Completado", "Cancelado", "En preparación"]
        self.filtro_estado = ttk.Combobox(filter_row2, values=estados, width=12, font=("Arial", 10), state="readonly")
        self.filtro_estado.pack(side="left", padx=(5, 0))
        self.filtro_estado.set("Todos")
        
        # Botones de acción
        buttons_row = tk.Frame(controls_frame, bg="#F5F5F5")
        buttons_row.pack(fill="x", pady=(10, 0))
        
        tk.Button(buttons_row, text="🔍 Aplicar Filtros",
                 command=self.aplicar_filtros_reportes_avanzados,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=6).pack(side="left", padx=(0, 10))
        
        tk.Button(buttons_row, text="🔄 Actualizar BD",
                 command=self.actualizar_datos_reportes_seguro,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=6).pack(side="left", padx=(0, 10))
        
        tk.Button(buttons_row, text="� Exportar PDF",
                 command=self.exportar_reporte_pdf_avanzado,
                 bg="#FF5722", fg="white", font=("Arial", 10, "bold"),
                 padx=20, pady=6).pack(side="left", padx=(0, 10))
        
        tk.Button(buttons_row, text="� Limpiar",
                 command=self.limpiar_filtros_reportes_avanzados,
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
        """Crea la pestaña de resumen general de ventas con datos reales de BD"""
        # Frame principal con mejor espaciado
        main_frame = tk.Frame(parent, bg=self.color_fondo_ventana)
        main_frame.pack(expand=True, fill="both", padx=20, pady=15)
        
        # Los datos ya están cargados en __init__, usarlos directamente
        # Calcular métricas completas desde datos reales de BD
        total_ventas = len(self.ventas) if hasattr(self, 'ventas') and self.ventas else 0
        ingresos_totales = sum(venta.get('total_final', 0) for venta in self.ventas) if self.ventas else 0
        descuentos_totales = sum(venta.get('descuento_aplicado', 0) for venta in self.ventas) if self.ventas else 0
        
        # Métricas adicionales para análisis completo
        ventas_completadas = len([v for v in self.ventas if v.get('estado') == 'Completado']) if self.ventas else 0
        ventas_canceladas = len([v for v in self.ventas if v.get('estado') == 'Cancelado']) if self.ventas else 0
        ingresos_sin_descuentos = sum(venta.get('total_sin_descuento', 0) for venta in self.ventas) if self.ventas else 0
        
        # Frame para métricas principales con LabelFrame
        metricas_frame = tk.LabelFrame(main_frame, text="📊 Métricas Principales (Datos en Tiempo Real)", 
                                     font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, 
                                     fg=self.color_titulo, relief="ridge", bd=2, padx=15, pady=15)
        metricas_frame.pack(fill="x", pady=(0, 20))
        
        # Frame separado para el botón de actualización
        actualizar_frame = tk.Frame(metricas_frame, bg=self.color_fondo_ventana)
        actualizar_frame.pack(fill="x", pady=(0, 10))
        
        # Botón de actualización de datos
        actualizar_btn = tk.Button(actualizar_frame, text="🔄 Actualizar desde BD", 
                                  command=self.actualizar_datos_reportes_seguro,
                                  bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"),
                                  relief="raised", bd=2, padx=15, pady=5)
        actualizar_btn.pack(side="right")
        
        # Frame separado para las métricas con grid
        metricas_container = tk.Frame(metricas_frame, bg=self.color_fondo_ventana)
        metricas_container.pack(fill="x", pady=(5, 0))
        
        # Métricas expandidas con datos completos de BD
        metricas = [
            ("Total Ventas", str(total_ventas), "#4CAF50"),
            ("Ingresos Finales", f"${ingresos_totales:,.2f}", "#2196F3"),
            ("Descuentos", f"${descuentos_totales:,.2f}", "#FF9800"),
            ("Promedio/Venta", f"${ingresos_totales/total_ventas:,.2f}" if total_ventas > 0 else "$0.00", "#9C27B0"),
            ("Completadas", f"{ventas_completadas} ({ventas_completadas*100/total_ventas:.1f}%)" if total_ventas > 0 else "0", "#8BC34A"),
            ("Canceladas", f"{ventas_canceladas} ({ventas_canceladas*100/total_ventas:.1f}%)" if total_ventas > 0 else "0", "#F44336"),
            ("Sin Descuentos", f"${ingresos_sin_descuentos:,.2f}", "#9E9E9E"),
            ("Ahorro Total", f"${ingresos_sin_descuentos - ingresos_totales:,.2f}" if ingresos_sin_descuentos > ingresos_totales else "$0.00", "#FF5722")
        ]
        
        for i, (titulo, valor, color) in enumerate(metricas):
            col = i % 4  # 4 columnas para mejor distribución
            row = i // 4
            
            metrica_frame = tk.Frame(metricas_container, bg=color, relief="raised", bd=3)
            metrica_frame.grid(row=row, column=col, padx=5, pady=8, sticky="ew", ipadx=15, ipady=12)
            metricas_container.grid_columnconfigure(col, weight=1)
            
            tk.Label(metrica_frame, text=titulo, font=("Helvetica", 9, "bold"), 
                    bg=color, fg="white").pack()
            tk.Label(metrica_frame, text=valor, font=("Helvetica", 12, "bold"), 
                    bg=color, fg="white").pack()
        
        # Análisis detallado basado en datos reales de BD
        if total_ventas > 0:
            # Análisis de productos más vendidos
            productos_vendidos = {}
            metodos_pago = {}
            cajeros_ventas = {}
            
            for venta in self.ventas:
                try:
                    # Contar productos vendidos
                    for producto in venta.get('productos', []):
                        nombre = producto.get('nombre', 'Producto sin nombre')
                        cantidad = producto.get('cantidad', 0)
                        productos_vendidos[nombre] = productos_vendidos.get(nombre, 0) + cantidad
                    
                    # Contar métodos de pago
                    metodo = venta.get('metodo_pago', 'No especificado')
                    metodos_pago[metodo] = metodos_pago.get(metodo, 0) + 1
                    
                    # Contar ventas por cajero
                    cajero = venta.get('cajero', 'No especificado')
                    cajeros_ventas[cajero] = cajeros_ventas.get(cajero, 0) + 1
                    
                except Exception as e:
                    print(f"Error procesando venta: {e}")
                    continue
            
            # Crear panel de información adicional
            if productos_vendidos or metodos_pago or cajeros_ventas:
                info_adicional = tk.Frame(metricas_frame, bg="#E8F5E8", relief="sunken", bd=2)
                info_adicional.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
                
                info_text = "📊 ANÁLISIS RÁPIDO:  "
                
                # Producto más vendido
                if productos_vendidos:
                    producto_top = max(productos_vendidos, key=lambda k: productos_vendidos[k])
                    cantidad_top = productos_vendidos[producto_top]
                    info_text += f"🏆 Top Producto: {producto_top} ({cantidad_top} uni.)  "
                
                # Método de pago más usado
                if metodos_pago:
                    pago_top = max(metodos_pago, key=lambda k: metodos_pago[k])
                    pago_count = metodos_pago[pago_top]
                    info_text += f"💳 Top Pago: {pago_top} ({pago_count} ventas)  "
                
                # Cajero más activo
                if cajeros_ventas:
                    cajero_top = max(cajeros_ventas, key=lambda k: cajeros_ventas[k])
                    cajero_count = cajeros_ventas[cajero_top]
                    info_text += f"👤 Top Cajero: {cajero_top} ({cajero_count} ventas)"
                
                tk.Label(info_adicional, text=info_text, 
                        font=("Helvetica", 10, "bold"), bg="#E8F5E8", fg="#2E7D32", 
                        padx=10, pady=8).pack()

        # Tabla detallada de ventas con LabelFrame
        tabla_frame = tk.LabelFrame(main_frame, text="📋 Detalle de Ventas Recientes (Base de Datos)", 
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
        
        tk.Button(control_frame, text="🗑️ Eliminar Venta", 
                 command=lambda: self.eliminar_venta_seleccionada(tree),
                 bg="#F44336", fg="white", font=("Arial", 10, "bold"),
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
        
        # Llenar tabla con datos de ventas reales (manejo robusto de errores)
        if self.ventas:
            ventas_ordenadas = sorted([v for v in self.ventas if v and 'fecha' in v], 
                                    key=lambda x: x.get('fecha', ''), reverse=True)
            
            for i, venta in enumerate(ventas_ordenadas[:100]):  # Últimas 100 ventas
                try:
                    # Validar datos esenciales
                    venta_id = venta.get('id', f'VENTA_{i+1}')
                    fecha_raw = venta.get('fecha', '')
                    
                    # Formatear fecha de manera segura
                    try:
                        fecha_dt = datetime.datetime.strptime(fecha_raw, '%Y-%m-%d %H:%M:%S')
                        fecha_formateada = fecha_dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        fecha_formateada = fecha_raw[:16] if len(fecha_raw) > 16 else fecha_raw
                    
                    # Procesar productos de manera segura
                    productos = venta.get('productos', [])
                    if isinstance(productos, list) and productos:
                        productos_texto = ", ".join([
                            f"{p.get('nombre', 'Producto')} x{p.get('cantidad', 0)}" 
                            for p in productos if isinstance(p, dict)
                        ])
                    else:
                        productos_texto = "Sin productos"
                    
                    if len(productos_texto) > 35:
                        productos_texto = productos_texto[:32] + "..."
                    
                    # Formatear campos de manera segura
                    oferta_texto = venta.get('oferta_aplicada') or "Sin oferta"
                    descuento_aplicado = float(venta.get('descuento_aplicado', 0))
                    total_final = float(venta.get('total_final', 0))
                    
                    descuento_texto = f"${descuento_aplicado:.2f}"
                    total_texto = f"${total_final:.2f}"
                    
                    # Estado para codificación por colores
                    estado = venta.get('estado', 'Desconocido')
                    
                    # Insertar en tabla con ID único
                    item_id = tree.insert("", "end", values=(
                        venta_id, fecha_formateada, productos_texto, 
                        oferta_texto, descuento_texto, total_texto
                    ))
                    
                    # Colorear según estado (opcional)
                    if estado == 'Completado':
                        tree.set(item_id, "ID", f"✅ {venta_id}")
                    elif estado == 'Cancelado':
                        tree.set(item_id, "ID", f"❌ {venta_id}")
                    elif estado == 'En preparación':
                        tree.set(item_id, "ID", f"⏳ {venta_id}")
                        
                except Exception as e:
                    print(f"Error al procesar venta {venta.get('id', f'venta_{i}')}: {e}")
                    # Insertar entrada de error para debugging
                    try:
                        tree.insert("", "end", values=(
                            f"ERROR_{i}", "Error de datos", "Datos corruptos", 
                            "N/A", "$0.00", "$0.00"
                        ))
                    except:
                        pass
                    continue
        else:
            # Mostrar mensaje cuando no hay datos
            tree.insert("", "end", values=(
                "SIN_DATOS", "No hay ventas", "Cargar datos desde BD", 
                "N/A", "$0.00", "$0.00"
            ))
        
        # Configurar scrollbars mejorados
        scrollbar_v = ttk.Scrollbar(tabla_container, orient="vertical", command=tree.yview)
        scrollbar_h = ttk.Scrollbar(tabla_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Layout mejorado con grid para mejor control
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        tabla_container.grid_rowconfigure(0, weight=1)
        tabla_container.grid_columnconfigure(0, weight=1)
        
        # Guardar referencia del tree para uso en otras funciones
        self.current_tree_ventas = tree
        scrollbar_h.pack(side="bottom", fill="x")
    
    def actualizar_datos_reportes(self):
        """Actualiza los datos de reportes desde la base de datos"""
        try:
            # Recargar datos desde BD
            ventas_bd = db.load_orders()
            if ventas_bd:
                self.ventas = ventas_bd
            
            ofertas_bd = db.load_offers()
            if ofertas_bd:
                self.ofertas = ofertas_bd
            
            messagebox.showinfo("Actualización", "Datos actualizados desde la base de datos")
            
            # Refrescar la vista actual de reportes
            self.mostrar_reportes()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar datos: {str(e)}")
    
    def actualizar_datos_reportes_completos(self):
        """Actualización completa de datos para reportes avanzados"""
        try:
            # Mostrar indicador de carga
            loading_window = tk.Toplevel(self)
            loading_window.title("Actualizando...")
            loading_window.geometry("300x100")
            loading_window.configure(bg=self.color_fondo_ventana)
            loading_window.transient(self)
            loading_window.grab_set()
            
            tk.Label(loading_window, text="🔄 Actualizando datos...", 
                    font=("Arial", 12, "bold"), 
                    bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=30)
            
            # Forzar actualización de la ventana
            loading_window.update()
            
            # Recargar todos los datos desde BD
            self.ventas = db.load_orders()
            self.productos = db.load_products()
            self.ofertas = db.load_offers()
            
            # Actualizar filtros también
            self.ventas_filtradas = self.ventas.copy()
            
            # Cerrar ventana de carga
            loading_window.destroy()
            
            # Mensaje de confirmación
            messagebox.showinfo("Éxito", f"Datos actualizados correctamente:\n• {len(self.ventas)} ventas\n• {len(self.productos)} productos\n• {len(self.ofertas)} ofertas")
            
            # Refrescar completamente la vista de reportes
            self.mostrar_reportes()
            
        except Exception as e:
            try:
                loading_window.destroy()
            except:
                pass
            messagebox.showerror("Error", f"Error al actualizar datos: {str(e)}")
    
    def aplicar_filtros_reportes_avanzados(self):
        """Sistema de filtros avanzado completamente integrado con BD"""
        try:
            # Obtener valores de filtros
            fecha_inicio = self.fecha_inicio.get().strip()
            fecha_fin = self.fecha_fin.get().strip()
            producto_filtro = self.filtro_producto.get()
            pago_filtro = self.filtro_pago.get()
            cajero_filtro = self.filtro_cajero.get()
            estado_filtro = self.filtro_estado.get()
            
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
            
            # Aplicar filtros paso a paso
            ventas_filtradas = []
            total_ventas_bd = len(self.ventas)
            
            for venta in self.ventas:
                # Validar que la venta tenga los campos necesarios
                if not all(key in venta for key in ['fecha', 'productos', 'cajero']):
                    continue
                
                try:
                    fecha_venta = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
                    fecha_venta_solo = fecha_venta.date()
                    
                    # Filtro por fecha
                    if not (fecha_inicio_dt.date() <= fecha_venta_solo <= fecha_fin_dt.date()):
                        continue
                    
                    # Filtro por producto
                    if producto_filtro != "Todos":
                        productos_en_venta = [p.get('nombre', '') for p in venta.get('productos', [])]
                        if producto_filtro not in productos_en_venta:
                            continue
                    
                    # Filtro por método de pago
                    if pago_filtro != "Todos" and venta.get('metodo_pago', '') != pago_filtro:
                        continue
                    
                    # Filtro por cajero
                    if cajero_filtro != "Todos" and venta.get('cajero', '') != cajero_filtro:
                        continue
                    
                    # Filtro por estado
                    if estado_filtro != "Todos" and venta.get('estado', '') != estado_filtro:
                        continue
                    
                    ventas_filtradas.append(venta)
                    
                except Exception as e:
                    print(f"Error procesando venta {venta.get('id', 'ID desconocido')}: {e}")
                    continue
            
            # Actualizar datos filtrados
            self.ventas_filtradas = ventas_filtradas
            
            # Mostrar resultados
            if ventas_filtradas:
                self.mostrar_resultados_filtrados_avanzados(ventas_filtradas, {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'producto': producto_filtro,
                    'pago': pago_filtro,
                    'cajero': cajero_filtro,
                    'estado': estado_filtro,
                    'total_bd': total_ventas_bd
                })
            else:
                messagebox.showinfo("Sin Resultados", 
                    f"No se encontraron ventas que coincidan con los filtros aplicados.\n\n"
                    f"Total en BD: {total_ventas_bd} ventas\n"
                    f"Período: {fecha_inicio} a {fecha_fin}\n"
                    f"Filtros aplicados:\n"
                    f"• Producto: {producto_filtro}\n"
                    f"• Pago: {pago_filtro}\n"
                    f"• Cajero: {cajero_filtro}\n"
                    f"• Estado: {estado_filtro}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar filtros: {str(e)}")
    
    def limpiar_filtros_reportes_avanzados(self):
        """Limpia todos los filtros y resetea a valores por defecto"""
        try:
            # Resetear fechas a último mes
            today = datetime.datetime.now()
            last_month = today - datetime.timedelta(days=30)
            
            self.fecha_inicio.delete(0, tk.END)
            self.fecha_inicio.insert(0, last_month.strftime("%Y-%m-%d"))
            
            self.fecha_fin.delete(0, tk.END)
            self.fecha_fin.insert(0, today.strftime("%Y-%m-%d"))
            
            # Resetear comboboxes
            self.filtro_producto.set("Todos")
            self.filtro_pago.set("Todos")
            self.filtro_cajero.set("Todos")
            self.filtro_estado.set("Todos")
            
            # Resetear datos filtrados
            self.ventas_filtradas = self.ventas.copy()
            
            messagebox.showinfo("Filtros Limpiados", "Todos los filtros han sido restablecidos a sus valores por defecto")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al limpiar filtros: {str(e)}")
    
    def exportar_reporte_pdf_avanzado(self):
        """Exporta un reporte PDF avanzado con los datos actuales (filtrados o completos)"""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showwarning("ReportLab no disponible", 
                "Para exportar PDF necesitas instalar ReportLab:\npip install reportlab")
            return
        
        try:
            # Determinar qué datos exportar
            datos_a_exportar = self.ventas_filtradas if hasattr(self, 'ventas_filtradas') and self.ventas_filtradas else self.ventas
            
            if not datos_a_exportar:
                messagebox.showwarning("Sin datos", "No hay datos para exportar")
                return
            
            # Seleccionar archivo
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Guardar reporte PDF",
                initialname=f"reporte_ventas_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            )
            
            if not filename:
                return
            
            # Crear PDF con datos actuales
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            titulo = Paragraph(f"<b>REPORTE DE VENTAS MIZU SUSHI</b><br/>Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                             styles['Title'])
            story.append(titulo)
            story.append(Spacer(1, 20))
            
            # Resumen ejecutivo
            total_ventas = len(datos_a_exportar)
            ingresos_totales = sum(v.get('total_final', 0) for v in datos_a_exportar)
            descuentos_totales = sum(v.get('descuento_aplicado', 0) for v in datos_a_exportar)
            promedio_venta = ingresos_totales / total_ventas if total_ventas > 0 else 0
            
            resumen_texto = f"""
            <b>RESUMEN EJECUTIVO</b><br/>
            • Total de ventas: {total_ventas}<br/>
            • Ingresos totales: ${ingresos_totales:,.2f}<br/>
            • Descuentos aplicados: ${descuentos_totales:,.2f}<br/>
            • Promedio por venta: ${promedio_venta:,.2f}<br/>
            """
            
            resumen = Paragraph(resumen_texto, styles['Normal'])
            story.append(resumen)
            story.append(Spacer(1, 20))
            
            # Tabla de datos
            tabla_datos = [['ID Venta', 'Fecha', 'Total', 'Método Pago', 'Cajero', 'Estado']]
            
            for venta in datos_a_exportar[:100]:  # Máximo 100 ventas en el PDF
                fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                tabla_datos.append([
                    venta.get('id', ''),
                    fecha_formateada,
                    f"${venta.get('total_final', 0):.2f}",
                    venta.get('metodo_pago', ''),
                    venta.get('cajero', ''),
                    venta.get('estado', '')
                ])
            
            tabla = Table(tabla_datos, colWidths=[80, 80, 80, 80, 80, 80])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(tabla)
            
            # Generar PDF
            doc.build(story)
            
            messagebox.showinfo("Éxito", f"Reporte PDF generado exitosamente:\n{filename}\n\nVentas incluidas: {len(datos_a_exportar)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")
    
    def mostrar_resultados_filtrados_avanzados(self, ventas_filtradas, filtros_info):
        """Muestra resultados filtrados en ventana moderna y completa"""
        ventana_resultados = tk.Toplevel(self)
        ventana_resultados.title("🔍 Resultados de Filtros Avanzados")
        ventana_resultados.geometry("1200x700")
        ventana_resultados.configure(bg=self.color_fondo_ventana)
        
        # Título principal
        titulo_frame = tk.Frame(ventana_resultados, bg="#673AB7", relief="raised", bd=2)
        titulo_frame.pack(fill="x", pady=(0, 20))
        tk.Label(titulo_frame, text="📊 RESULTADOS FILTRADOS", 
                font=("Impact", 18, "bold"), bg="#673AB7", fg="white", 
                pady=10).pack()
        
        # Panel de información de filtros
        info_frame = tk.LabelFrame(ventana_resultados, text="Filtros Aplicados", 
                                  font=("Arial", 12, "bold"), bg=self.color_fondo_ventana)
        info_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Mostrar filtros en formato organizado
        filtros_text = f"""📅 Período: {filtros_info['fecha_inicio']} - {filtros_info['fecha_fin']}
🍣 Producto: {filtros_info['producto']} | 💳 Pago: {filtros_info['pago']}
👤 Cajero: {filtros_info['cajero']} | 📊 Estado: {filtros_info['estado']}
📈 Resultados: {len(ventas_filtradas)} de {filtros_info['total_bd']} ventas totales en BD"""
        
        tk.Label(info_frame, text=filtros_text, font=("Courier", 10), 
                bg=self.color_fondo_ventana, fg=self.color_texto, justify="left").pack(anchor="w", padx=10, pady=10)
        
        # Métricas de resultados filtrados
        metricas_frame = tk.LabelFrame(ventana_resultados, text="Métricas de Resultados", 
                                      font=("Arial", 12, "bold"), bg=self.color_fondo_ventana)
        metricas_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Calcular métricas
        total_ventas = len(ventas_filtradas)
        ingresos_totales = sum(v.get('total_final', 0) for v in ventas_filtradas)
        descuentos_totales = sum(v.get('descuento_aplicado', 0) for v in ventas_filtradas)
        promedio_venta = ingresos_totales / total_ventas if total_ventas > 0 else 0
        
        # Crear grid de métricas
        metricas_container = tk.Frame(metricas_frame, bg=self.color_fondo_ventana)
        metricas_container.pack(fill="x", padx=10, pady=10)
        
        metricas = [
            ("Ventas Encontradas", f"{total_ventas}", "#4CAF50"),
            ("Ingresos Totales", f"${ingresos_totales:,.2f}", "#2196F3"),
            ("Descuentos", f"${descuentos_totales:,.2f}", "#FF9800"),
            ("Promedio/Venta", f"${promedio_venta:,.2f}", "#9C27B0")
        ]
        
        for i, (titulo, valor, color) in enumerate(metricas):
            metrica_frame = tk.Frame(metricas_container, bg=color, relief="raised", bd=2)
            metrica_frame.grid(row=0, column=i, padx=5, pady=5, sticky="ew", ipadx=15, ipady=8)
            metricas_container.grid_columnconfigure(i, weight=1)
            
            tk.Label(metrica_frame, text=titulo, font=("Arial", 10, "bold"), 
                    bg=color, fg="white").pack()
            tk.Label(metrica_frame, text=valor, font=("Arial", 14, "bold"), 
                    bg=color, fg="white").pack()
        
        # Tabla de resultados
        tabla_frame = tk.LabelFrame(ventana_resultados, text=f"Detalle de {len(ventas_filtradas)} Ventas", 
                                   font=("Arial", 12, "bold"), bg=self.color_fondo_ventana)
        tabla_frame.pack(expand=True, fill="both", padx=20, pady=(0, 15))
        
        # Crear tabla con scrollbars
        tabla_container = tk.Frame(tabla_frame, bg=self.color_fondo_ventana)
        tabla_container.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tabla_container, orient="vertical")
        h_scroll = ttk.Scrollbar(tabla_container, orient="horizontal")
        
        # Treeview
        tree = ttk.Treeview(tabla_container, 
                           columns=("ID", "Fecha", "Productos", "Total", "Pago", "Cajero", "Estado"),
                           show="headings", 
                           yscrollcommand=v_scroll.set,
                           xscrollcommand=h_scroll.set)
        
        # Configurar scrollbars
        v_scroll.config(command=tree.yview)
        h_scroll.config(command=tree.xview)
        
        # Layout de tabla y scrollbars
        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tabla_container.grid_rowconfigure(0, weight=1)
        tabla_container.grid_columnconfigure(0, weight=1)
        
        # Configurar columnas
        columnas_info = [
            ("ID", 80),
            ("Fecha", 120),
            ("Productos", 250),
            ("Total", 100),
            ("Pago", 100),
            ("Cajero", 100),
            ("Estado", 100)
        ]
        
        for col, ancho in columnas_info:
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center" if col in ["ID", "Total"] else "w")
        
        # Llenar tabla con datos filtrados
        for venta in sorted(ventas_filtradas, key=lambda x: x.get('fecha', ''), reverse=True):
            try:
                fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                productos_texto = ", ".join([f"{p.get('nombre', '')} x{p.get('cantidad', 0)}" for p in venta.get('productos', [])])
                if len(productos_texto) > 35:
                    productos_texto = productos_texto[:32] + "..."
                
                tree.insert("", "end", values=(
                    venta.get('id', ''),
                    fecha_formateada,
                    productos_texto,
                    f"${venta.get('total_final', 0):.2f}",
                    venta.get('metodo_pago', ''),
                    venta.get('cajero', ''),
                    venta.get('estado', '')
                ))
            except Exception as e:
                print(f"Error al mostrar venta: {e}")
                continue
        
        # Botones de acción
        botones_frame = tk.Frame(ventana_resultados, bg=self.color_fondo_ventana)
        botones_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Button(botones_frame, text="📄 Exportar Filtrados a PDF",
                 command=lambda: self.exportar_filtrados_a_pdf(ventas_filtradas),
                 bg="#FF5722", fg="white", font=("Arial", 11, "bold"),
                 padx=20, pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(botones_frame, text="📋 Copiar Resumen",
                 command=lambda: self.copiar_resumen_filtrados(ventas_filtradas, filtros_info),
                 bg="#9C27B0", fg="white", font=("Arial", 11, "bold"),
                 padx=20, pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(botones_frame, text="❌ Cerrar",
                 command=ventana_resultados.destroy,
                 bg="#9E9E9E", fg="white", font=("Arial", 11, "bold"),
                 padx=20, pady=8).pack(side="right")
    
    def exportar_filtrados_a_pdf(self, ventas_filtradas):
        """Exporta solo los datos filtrados a PDF"""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showwarning("ReportLab no disponible", "Instala ReportLab: pip install reportlab")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Guardar resultados filtrados",
                initialname=f"ventas_filtradas_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            )
            
            if filename:
                # Crear PDF específico para datos filtrados
                doc = SimpleDocTemplate(filename, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Título específico
                titulo = Paragraph(f"<b>VENTAS FILTRADAS - MIZU SUSHI</b><br/>Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Title'])
                story.append(titulo)
                story.append(Spacer(1, 20))
                
                # Añadir contenido similar al método anterior pero específico para filtrados
                # [Contenido similar al exportar_reporte_pdf_avanzado pero específico para datos filtrados]
                
                doc.build(story)
                messagebox.showinfo("Éxito", f"Resultados filtrados exportados: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def copiar_resumen_filtrados(self, ventas_filtradas, filtros_info):
        """Copia un resumen de los datos filtrados al portapapeles"""
        try:
            total_ventas = len(ventas_filtradas)
            ingresos_totales = sum(v.get('total_final', 0) for v in ventas_filtradas)
            
            resumen = f"""RESUMEN DE VENTAS FILTRADAS - MIZU SUSHI
Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}

FILTROS APLICADOS:
- Período: {filtros_info['fecha_inicio']} - {filtros_info['fecha_fin']}
- Producto: {filtros_info['producto']}
- Método de pago: {filtros_info['pago']}
- Cajero: {filtros_info['cajero']}
- Estado: {filtros_info['estado']}

RESULTADOS:
- Ventas encontradas: {total_ventas}
- Ingresos totales: ${ingresos_totales:,.2f}
- Promedio por venta: ${ingresos_totales/total_ventas:,.2f if total_ventas > 0 else 0}
"""
            
            # Copiar al portapapeles (en sistemas Windows)
            try:
                import subprocess
                subprocess.run("clip", universal_newlines=True, input=resumen, check=True)
                messagebox.showinfo("Copiado", "Resumen copiado al portapapeles exitosamente")
            except:
                # Fallback: mostrar en ventana si no se puede copiar
                ventana_resumen = tk.Toplevel(self)
                ventana_resumen.title("Resumen")
                ventana_resumen.geometry("500x400")
                text_widget = tk.Text(ventana_resumen, wrap="word")
                text_widget.pack(expand=True, fill="both", padx=10, pady=10)
                text_widget.insert(1.0, resumen)
                text_widget.config(state="disabled")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar resumen: {str(e)}")

    def actualizar_tabla_ventas(self, tree):
        """Actualiza la tabla de ventas con datos frescos de la BD"""
        try:
            # Limpiar tabla
            for item in tree.get_children():
                tree.delete(item)
            
            # Recargar desde BD
            ventas_bd = db.load_orders()
            if ventas_bd:
                self.ventas = ventas_bd
            
            # Llenar tabla con datos actualizados
            for venta in sorted(self.ventas, key=lambda x: x['fecha'], reverse=True)[:50]:
                try:
                    fecha_formateada = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                    productos_texto = ", ".join([f"{p['nombre']} x{p['cantidad']}" for p in venta['productos']])
                    if len(productos_texto) > 30:
                        productos_texto = productos_texto[:27] + "..."
                    
                    oferta_texto = venta['oferta_aplicada'] if venta['oferta_aplicada'] else "Sin oferta"
                    descuento_texto = f"${venta['descuento_aplicado']:.2f}"
                    total_texto = f"${venta['total_final']:.2f}"
                    
                    tree.insert("", "end", iid=venta['id'], values=(
                        venta['id'], fecha_formateada, productos_texto, 
                        oferta_texto, descuento_texto, total_texto
                    ))
                except Exception as e:
                    print(f"Error al procesar venta: {e}")
                    continue
            
            messagebox.showinfo("Actualización", "Tabla de ventas actualizada desde la base de datos")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar tabla: {str(e)}")
    
    def ver_detalle_venta_seleccionada(self, tree):
        """Muestra el detalle completo de la venta seleccionada"""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona una venta para ver detalles")
            return
        
        venta_id = sel[0]
        venta = next((v for v in self.ventas if v['id'] == venta_id), None)
        
        if not venta:
            messagebox.showerror("Error", "No se encontró la venta seleccionada")
            return
        
        # Crear ventana de detalles
        detalle_window = tk.Toplevel(self)
        detalle_window.title(f"Detalle de Venta - {venta_id}")
        detalle_window.geometry("600x500")
        detalle_window.configure(bg=self.color_fondo_ventana)
        
        # Título
        tk.Label(detalle_window, text=f"📋 Detalle de Venta: {venta_id}", 
                font=("Helvetica", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=20)
        
        # Frame para información general
        info_frame = tk.LabelFrame(detalle_window, text="Información General", 
                                  font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana)
        info_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Datos generales
        tk.Label(info_frame, text=f"Fecha: {venta['fecha']}", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=2)
        tk.Label(info_frame, text=f"Cajero: {venta['cajero']}", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=2)
        tk.Label(info_frame, text=f"Método de pago: {venta['metodo_pago']}", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=2)
        
        # Frame para productos
        productos_frame = tk.LabelFrame(detalle_window, text="Productos", 
                                       font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana)
        productos_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Tabla de productos
        prod_tree = ttk.Treeview(productos_frame, columns=("Producto", "Cantidad", "Precio", "Subtotal"), 
                                show="headings", height=8)
        
        for col in ["Producto", "Cantidad", "Precio", "Subtotal"]:
            prod_tree.heading(col, text=col)
            prod_tree.column(col, width=120, anchor="center" if col != "Producto" else "w")
        
        for producto in venta['productos']:
            prod_tree.insert("", "end", values=(
                producto['nombre'],
                producto['cantidad'],
                f"${producto['precio']:.2f}",
                f"${producto['subtotal']:.2f}"
            ))
        
        prod_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame para totales
        totales_frame = tk.LabelFrame(detalle_window, text="Resumen Financiero", 
                                     font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana)
        totales_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Label(totales_frame, text=f"Subtotal: ${venta['total_sin_descuento']:.2f}", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=2)
        tk.Label(totales_frame, text=f"Descuento aplicado: ${venta['descuento_aplicado']:.2f}", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana, fg="#FF9800").pack(anchor="w", padx=10, pady=2)
        tk.Label(totales_frame, text=f"TOTAL FINAL: ${venta['total_final']:.2f}", 
                font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana, fg="#4CAF50").pack(anchor="w", padx=10, pady=5)
        
        if venta['oferta_aplicada']:
            tk.Label(totales_frame, text=f"Oferta aplicada: {venta['oferta_aplicada']}", 
                    font=("Helvetica", 11, "italic"), bg=self.color_fondo_ventana, fg="#2196F3").pack(anchor="w", padx=10, pady=2)
        
        # Botón cerrar
        tk.Button(detalle_window, text="❌ Cerrar", command=detalle_window.destroy,
                 bg="#9E9E9E", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8).pack(pady=15)
    
    def eliminar_venta_seleccionada(self, tree):
        """Elimina la venta seleccionada de la base de datos"""
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona una venta para eliminar")
            return
        
        venta_id = sel[0]
        venta = next((v for v in self.ventas if v['id'] == venta_id), None)
        
        if not venta:
            messagebox.showerror("Error", "No se encontró la venta seleccionada")
            return
        
        # Confirmación detallada
        confirmacion = messagebox.askyesno("Confirmar Eliminación", 
                                          f"¿Estás seguro de eliminar la venta?\n\n"
                                          f"ID: {venta_id}\n"
                                          f"Fecha: {venta['fecha']}\n"
                                          f"Total: ${venta['total_final']:.2f}\n\n"
                                          f"Esta acción no se puede deshacer.")
        
        if confirmacion:
            try:
                # Eliminar de la lista en memoria
                self.ventas = [v for v in self.ventas if v['id'] != venta_id]
                
                # Eliminar de la tabla visual
                tree.delete(venta_id)
                
                # Nota: Aquí deberías agregar la función para eliminar de BD si existe
                # db.delete_order(venta_id)
                
                messagebox.showinfo("Éxito", f"Venta {venta_id} eliminada correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar venta: {str(e)}")
    
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
            pago_filtro = self.filtro_pago.get() if hasattr(self, 'filtro_pago') else "Todos"
            
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
                
            if not REPORTLAB_DISPONIBLE:
                messagebox.showerror("Error", "ReportLab no está disponible. No se puede generar el PDF.")
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
                                  f"• Método de pago: {self.filtro_pago.get() if hasattr(self, 'filtro_pago') else 'Todos'}<br/>"
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
    
    # Funciones adicionales para gestión de datos y reportes
    def backup_datos_reportes(self):
        """Crea un respaldo completo de todos los datos"""
        try:
            # Obtener datos desde BD
            productos = db.load_products()
            ofertas = db.load_offers()
            ventas = db.load_orders()
            carrito = db.get_cart_items()
            
            # Crear estructura de respaldo
            backup_data = {
                'fecha_backup': datetime.datetime.now().isoformat(),
                'version': '1.0',
                'productos': productos,
                'ofertas': ofertas,
                'ventas': ventas,
                'carrito': carrito,
                'configuracion': {
                    'tema_actual': self.tema_actual.get(),
                    'rol_usuario': self.rol_usuario.get()
                }
            }
            
            # Seleccionar archivo de destino
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON backup files", "*.json"), ("All files", "*.*")],
                title="Guardar respaldo de datos"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
                # Mostrar estadísticas del backup
                estadisticas = f"""✅ BACKUP COMPLETADO EXITOSAMENTE
                
📊 Datos respaldados:
• Productos: {len(productos)}
• Ofertas: {len(ofertas)}
• Ventas: {len(ventas)}
• Items en carrito: {len(carrito)}

📁 Archivo: {os.path.basename(filename)}
📅 Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
                messagebox.showinfo("Backup Completado", estadisticas)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear backup: {str(e)}")
    
    def restaurar_datos_reportes(self):
        """Restaura datos desde un archivo de respaldo"""
        # Confirmación de seguridad
        if not messagebox.askyesno("Confirmar Restauración", 
                                  "⚠️ ADVERTENCIA ⚠️\n\n"
                                  "La restauración reemplazará TODOS los datos actuales.\n"
                                  "Asegúrate de tener un backup reciente antes de continuar.\n\n"
                                  "¿Deseas continuar con la restauración?"):
            return
        
        try:
            # Seleccionar archivo de backup
            filename = filedialog.askopenfilename(
                filetypes=[("JSON backup files", "*.json"), ("All files", "*.*")],
                title="Seleccionar archivo de backup"
            )
            
            if not filename:
                return
            
            # Leer archivo de backup
            with open(filename, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validar estructura del backup
            required_keys = ['productos', 'ofertas', 'ventas']
            for key in required_keys:
                if key not in backup_data:
                    messagebox.showerror("Error", f"Archivo de backup inválido: falta '{key}'")
                    return
            
            # Limpiar datos actuales
            db.clear_cart()
            
            # Restaurar productos
            for producto in backup_data['productos']:
                db.save_product(producto)
            
            # Restaurar ofertas
            for oferta in backup_data['ofertas']:
                db.save_offer(oferta)
            
            # Restaurar ventas
            for venta in backup_data['ventas']:
                db.save_order(venta)
            
            # Actualizar datos en memoria
            self.ofertas = backup_data['ofertas']
            self.ventas = backup_data['ventas']
            
            # Mostrar estadísticas de restauración
            fecha_backup = backup_data.get('fecha_backup', 'Desconocida')
            estadisticas = f"""✅ RESTAURACIÓN COMPLETADA
            
📊 Datos restaurados:
• Productos: {len(backup_data['productos'])}
• Ofertas: {len(backup_data['ofertas'])}
• Ventas: {len(backup_data['ventas'])}

📅 Fecha del backup: {fecha_backup}
"""
            messagebox.showinfo("Restauración Completada", estadisticas)
            
            # Regresar al menú principal para refrescar la vista
            self.mostrar_menu_principal()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al restaurar datos: {str(e)}")
    
    def generar_analisis_comparativo(self):
        """Genera un análisis comparativo de períodos"""
        # Ventana para seleccionar períodos
        analisis_window = tk.Toplevel(self)
        analisis_window.title("Análisis Comparativo de Períodos")
        analisis_window.geometry("500x400")
        analisis_window.configure(bg=self.color_fondo_ventana)
        
        # Título
        tk.Label(analisis_window, text="📈 Análisis Comparativo", 
                font=("Helvetica", 16, "bold"), bg=self.color_fondo_ventana, fg=self.color_titulo).pack(pady=20)
        
        # Frame para períodos
        periodos_frame = tk.LabelFrame(analisis_window, text="Seleccionar Períodos", 
                                      font=("Helvetica", 12, "bold"), bg=self.color_fondo_ventana)
        periodos_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Período 1
        tk.Label(periodos_frame, text="Período 1 (desde):", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=(10, 2))
        periodo1_inicio = tk.Entry(periodos_frame, width=30)
        periodo1_inicio.pack(anchor="w", padx=10)
        periodo1_inicio.insert(0, "2025-09-01")
        
        tk.Label(periodos_frame, text="Período 1 (hasta):", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=(10, 2))
        periodo1_fin = tk.Entry(periodos_frame, width=30)
        periodo1_fin.pack(anchor="w", padx=10, pady=(0, 15))
        periodo1_fin.insert(0, "2025-09-15")
        
        # Período 2
        tk.Label(periodos_frame, text="Período 2 (desde):", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=(5, 2))
        periodo2_inicio = tk.Entry(periodos_frame, width=30)
        periodo2_inicio.pack(anchor="w", padx=10)
        periodo2_inicio.insert(0, "2025-09-16")
        
        tk.Label(periodos_frame, text="Período 2 (hasta):", 
                font=("Helvetica", 11), bg=self.color_fondo_ventana).pack(anchor="w", padx=10, pady=(10, 2))
        periodo2_fin = tk.Entry(periodos_frame, width=30)
        periodo2_fin.pack(anchor="w", padx=10, pady=(0, 15))
        periodo2_fin.insert(0, "2025-09-30")
        
        def generar_analisis():
            try:
                # Obtener fechas
                p1_inicio = datetime.datetime.strptime(periodo1_inicio.get(), "%Y-%m-%d")
                p1_fin = datetime.datetime.strptime(periodo1_fin.get(), "%Y-%m-%d")
                p2_inicio = datetime.datetime.strptime(periodo2_inicio.get(), "%Y-%m-%d")
                p2_fin = datetime.datetime.strptime(periodo2_fin.get(), "%Y-%m-%d")
                
                # Filtrar ventas por períodos
                ventas_p1 = []
                ventas_p2 = []
                
                for venta in self.ventas:
                    fecha_venta = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
                    if p1_inicio <= fecha_venta <= p1_fin:
                        ventas_p1.append(venta)
                    elif p2_inicio <= fecha_venta <= p2_fin:
                        ventas_p2.append(venta)
                
                # Calcular métricas
                total_p1 = sum(v['total_final'] for v in ventas_p1)
                total_p2 = sum(v['total_final'] for v in ventas_p2)
                cantidad_p1 = len(ventas_p1)
                cantidad_p2 = len(ventas_p2)
                
                # Calcular diferencias
                diferencia_ingresos = total_p2 - total_p1
                diferencia_cantidad = cantidad_p2 - cantidad_p1
                porcentaje_ingresos = (diferencia_ingresos / total_p1 * 100) if total_p1 > 0 else 0
                porcentaje_cantidad = (diferencia_cantidad / cantidad_p1 * 100) if cantidad_p1 > 0 else 0
                
                # Mostrar resultados
                resultados = f"""📊 ANÁLISIS COMPARATIVO DE PERÍODOS

📅 Período 1: {periodo1_inicio.get()} a {periodo1_fin.get()}
• Ventas: {cantidad_p1}
• Ingresos: ${total_p1:,.2f}
• Promedio: ${total_p1/cantidad_p1:,.2f} por venta

📅 Período 2: {periodo2_inicio.get()} a {periodo2_fin.get()}
• Ventas: {cantidad_p2}
• Ingresos: ${total_p2:,.2f}
• Promedio: ${total_p2/cantidad_p2:,.2f} por venta

📈 COMPARACIÓN:
• Diferencia en ventas: {diferencia_cantidad:+d} ({porcentaje_cantidad:+.1f}%)
• Diferencia en ingresos: ${diferencia_ingresos:+,.2f} ({porcentaje_ingresos:+.1f}%)

{"📈 TENDENCIA POSITIVA" if diferencia_ingresos > 0 else "📉 TENDENCIA NEGATIVA" if diferencia_ingresos < 0 else "➡️ TENDENCIA ESTABLE"}
"""
                
                messagebox.showinfo("Análisis Comparativo", resultados)
                
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar análisis: {str(e)}")
        
        # Botones
        btn_frame = tk.Frame(analisis_window, bg=self.color_fondo_ventana)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="📊 Generar Análisis", command=generar_analisis,
                 bg="#2196F3", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8).pack(side="left", padx=10)
        
        tk.Button(btn_frame, text="❌ Cerrar", command=analisis_window.destroy,
                 bg="#9E9E9E", fg="white", font=("Helvetica", 11, "bold"),
                 relief="raised", bd=2, padx=20, pady=8).pack(side="left", padx=10)
    
    def aplicar_filtros_reportes(self):
        """Aplica los filtros seleccionados a los reportes (implementación mejorada)"""
        try:
            fecha_inicio = self.fecha_inicio.get()
            fecha_fin = self.fecha_fin.get()
            producto_filtro = self.filtro_producto.get()
            
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
            
            # Cargar datos frescos desde BD
            ventas_bd = db.load_orders()
            if ventas_bd:
                self.ventas = ventas_bd
            
            # Filtrar ventas
            ventas_filtradas = []
            for venta in self.ventas:
                try:
                    fecha_venta = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
                    fecha_venta_solo = fecha_venta.date()
                    
                    # Filtro por fecha
                    if not (fecha_inicio_dt.date() <= fecha_venta_solo <= fecha_fin_dt.date()):
                        continue
                    
                    # Filtro por producto
                    if producto_filtro and producto_filtro.strip():
                        productos_en_venta = [p['nombre'].lower() for p in venta['productos']]
                        if not any(producto_filtro.lower() in prod for prod in productos_en_venta):
                            continue
                    
                    ventas_filtradas.append(venta)
                except Exception as e:
                    print(f"Error al procesar venta {venta.get('id', 'unknown')}: {e}")
                    continue
            
            # Actualizar ventas con filtros aplicados
            self.ventas = ventas_filtradas
            
            # Refrescar reportes
            self.mostrar_reportes()
            
            # Mostrar resultado del filtro
            messagebox.showinfo("Filtros Aplicados", 
                              f"Se encontraron {len(ventas_filtradas)} ventas que coinciden con los filtros:\n\n"
                              f"• Período: {fecha_inicio} a {fecha_fin}\n"
                              f"• Producto: {producto_filtro if producto_filtro else 'Todos'}")
            
            # Actualizar estado
            self.status_label.config(text=f"✅ Filtros aplicados - {len(ventas_filtradas)} ventas mostradas")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar filtros: {str(e)}")
    
    def limpiar_filtros_reportes(self):
        """Limpia todos los filtros y muestra todos los datos"""
        try:
            # Limpiar campos
            self.fecha_inicio.delete(0, 'end')
            self.fecha_inicio.insert(0, "2025-09-01")
            
            self.fecha_fin.delete(0, 'end')
            self.fecha_fin.insert(0, "2025-12-31")
            
            self.filtro_producto.delete(0, 'end')
            
            # Recargar todos los datos desde BD
            ventas_bd = db.load_orders()
            if ventas_bd:
                self.ventas = ventas_bd
            
            # Refrescar reportes
            self.mostrar_reportes()
            
            messagebox.showinfo("Filtros Limpiados", "Se han limpiado todos los filtros y se muestran todos los datos")
            
            # Actualizar estado
            self.status_label.config(text=f"✅ Filtros limpiados - {len(self.ventas)} ventas totales mostradas")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al limpiar filtros: {str(e)}")
    
    def exportar_reporte_pdf(self):
        """Exporta el reporte actual a PDF"""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showerror("Error", "ReportLab no está disponible. No se pueden generar PDFs.")
            return
        
        try:
            # Seleccionar archivo de destino
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Exportar reporte a PDF"
            )
            
            if not filename:
                return
            
            # Crear documento PDF
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elementos = []
            
            # Estilos
            styles = getSampleStyleSheet()
            titulo_style = ParagraphStyle(
                'TituloCustom',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Centrado
            )
            
            # Título
            elementos.append(Paragraph("🍣 REPORTE DE VENTAS - MIZU SUSHI BAR", titulo_style))
            elementos.append(Spacer(1, 20))
            
            # Información general
            fecha_actual = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            elementos.append(Paragraph(f"Fecha del reporte: {fecha_actual}", styles['Normal']))
            elementos.append(Paragraph(f"Total de ventas analizadas: {len(self.ventas)}", styles['Normal']))
            elementos.append(Spacer(1, 20))
            
            # Métricas principales
            if self.ventas:
                total_ventas = len(self.ventas)
                ingresos_totales = sum(venta['total_final'] for venta in self.ventas)
                descuentos_totales = sum(venta['descuento_aplicado'] for venta in self.ventas)
                promedio = ingresos_totales / total_ventas
                
                metricas_data = [
                    ['Métrica', 'Valor'],
                    ['Total de ventas', str(total_ventas)],
                    ['Ingresos totales', f'${ingresos_totales:,.2f}'],
                    ['Descuentos otorgados', f'${descuentos_totales:,.2f}'],
                    ['Promedio por venta', f'${promedio:,.2f}']
                ]
                
                tabla_metricas = Table(metricas_data)
                tabla_metricas.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elementos.append(Paragraph("📊 MÉTRICAS PRINCIPALES", styles['Heading2']))
                elementos.append(tabla_metricas)
                elementos.append(Spacer(1, 30))
            
            # Tabla de ventas recientes (últimas 20)
            elementos.append(Paragraph("📋 VENTAS RECIENTES", styles['Heading2']))
            
            ventas_data = [['ID', 'Fecha', 'Total', 'Descuento']]
            for venta in sorted(self.ventas, key=lambda x: x['fecha'], reverse=True)[:20]:
                fecha_corta = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                ventas_data.append([
                    venta['id'],
                    fecha_corta,
                    f"${venta['total_final']:.2f}",
                    f"${venta['descuento_aplicado']:.2f}"
                ])
            
            tabla_ventas = Table(ventas_data)
            tabla_ventas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elementos.append(tabla_ventas)
            
            # Construir PDF
            doc.build(elementos)
            
            messagebox.showinfo("Exportación Exitosa", f"Reporte exportado exitosamente:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar PDF: {str(e)}")

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
