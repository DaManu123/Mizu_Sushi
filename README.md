# 🍣 Sistema de Gestión de Restaurante Sushi

Una aplicación completa de gestión para restaurantes de sushi desarrollada en Python con Tkinter, que incluye punto de venta, inventario, reportes avanzados y más.

## 🚀 Características Principales

### 📊 **Sistema de Reportes Avanzados**
- **Vista de lista detallada** de todas las ventas
- **Filtros avanzados** por fecha, producto y método de pago
- **Exportación a PDF** de reportes completos
- **5 pestañas especializadas**: Resumen, Productos, Tendencias, Ofertas, Gestión de Datos
- **Detalles interactivos** de cada venta con ventana emergente

### 💰 **Punto de Venta (POS)**
- Interfaz intuitiva para registro de ventas
- Cálculo automático de totales y descuentos
- Soporte para múltiples productos y cantidades
- Aplicación de ofertas y promociones

### 📦 **Gestión de Inventario**
- Control completo de stock de productos
- Alertas de inventario bajo
- Gestión de proveedores
- Historial de movimientos

### 🎁 **Sistema de Ofertas**
- Creación y gestión de promociones
- Aplicación automática de descuentos
- Ofertas por cantidad, temporales y especiales
- Análisis de efectividad de promociones

### ⚙️ **Configuración del Sistema**
- Personalización de temas y colores
- Configuración de impresoras
- Gestión de usuarios y permisos
- Backup y restauración de datos

### 🔐 **Gestión de Usuarios**
- Sistema de login seguro
- Roles y permisos diferenciados
- Registro de actividades
- Control de acceso por funcionalidades

## 🛠️ **Tecnologías Utilizadas**

- **Python 3.x** - Lenguaje principal
- **Tkinter** - Interfaz gráfica de usuario
- **TTK** - Widgets avanzados para mejor UX
- **ReportLab** - Generación de reportes PDF
- **JSON** - Persistencia de datos
- **DateTime** - Manejo de fechas y horarios

## 📋 **Requisitos del Sistema**

```bash
Python 3.6 o superior
tkinter (incluido con Python)
reportlab (para exportación PDF)
```

## 🚀 **Instalación**

1. **Clona el repositorio:**
```bash
git clone https://github.com/TU_USUARIO/sushi-restaurant-system.git
cd sushi-restaurant-system
```

2. **Instala las dependencias:**
```bash
pip install reportlab
```

3. **Ejecuta la aplicación:**
```bash
python sushi_app.py
```

## 📸 **Capturas de Pantalla**

### Pantalla Principal
La interfaz principal con acceso a todas las funcionalidades del sistema.

### Sistema de Reportes
Vista detallada de ventas con filtros avanzados y exportación PDF.

### Punto de Venta
Interfaz intuitiva para registro rápido de ventas.

## 🎯 **Funcionalidades Destacadas**

### 📊 Reportes Inteligentes
- **Lista de ventas en tiempo real** con actualización automática
- **Filtros múltiples** para análisis específicos
- **Ventanas de detalle** para información completa de cada venta
- **Métricas automáticas** de ingresos, descuentos y promedios

### 🔄 Gestión de Datos
- **Backup automático** de información crítica
- **Restauración de datos** desde archivos de respaldo
- **Análisis comparativo** entre períodos
- **Alertas inteligentes** para situaciones importantes

### 🎨 Interfaz de Usuario
- **Diseño responsivo** que se adapta a diferentes tamaños de pantalla
- **Temas personalizables** con múltiples esquemas de color
- **Navegación intuitiva** con botones siempre visibles
- **Feedback visual** para todas las acciones del usuario

## 📁 **Estructura del Proyecto**

```
proyecto1/
├── sushi_app.py           # Archivo principal de la aplicación
├── contexto.txt           # Documentación del contexto
├── fondo_interfaz.png     # Recursos gráficos
├── README.md              # Este archivo
└── data/                  # Carpeta de datos (se crea automáticamente)
    ├── ventas.json        # Registro de ventas
    ├── inventario.json    # Datos de inventario
    └── usuarios.json      # Información de usuarios
```

## 🚦 **Uso de la Aplicación**

### Inicio de Sesión
1. Ejecuta `python sushi_app.py`
2. Usa las credenciales por defecto o crea un nuevo usuario
3. Accede al menú principal

### Registro de Ventas
1. Ve a "Punto de Venta" desde el menú principal
2. Selecciona productos y cantidades
3. Aplica ofertas si están disponibles
4. Confirma la venta

### Consulta de Reportes
1. Accede a "Reportes de Ventas Avanzados"
2. Usa los filtros para personalizar la vista
3. Consulta detalles de ventas específicas
4. Exporta reportes a PDF si es necesario

## 🤝 **Contribuciones**

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 **Licencia**

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 **Autor**

**Tu Nombre** - *Desarrollo inicial* - [Tu GitHub](https://github.com/TU_USUARIO)

## 🙏 **Agradecimientos**

- A la comunidad de Python por las excelentes librerías
- A todos los que han contribuido con feedback y sugerencias
- Al equipo de desarrollo que hizo posible este proyecto

---

⭐ **¡Si este proyecto te ha sido útil, considera darle una estrella en GitHub!** ⭐