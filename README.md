# Horarios Proyecto

## Descripción

Este proyecto es una aplicación web desarrollada en **Django** para la gestión de horarios escolares, apoderados, alumnos y mensualidades en un establecimiento educacional. Permite a los administradores gestionar horarios de profesores y cursos, registrar apoderados y sus alumnos, y administrar pagos de mensualidades con soporte para descuentos (en desarrollo).

El proyecto incluye las siguientes funcionalidades principales:

- Gestión de horarios de profesores y cursos, con generación de PDFs.
- Registro y administración de apoderados y alumnos, agrupados por año escolar y curso.
- Gestión de mensualidades, con soporte para diferentes modalidades de pago.
- Reportes de alumnos por año escolar y curso.
- Autenticación social con Google OAuth para los usuarios.

Este repositorio contiene la versión inicial del proyecto, lista para pruebas de QA. Las nuevas funcionalidades, como la gestión de descuentos, se están desarrollando en ramas separadas (`feature-descuentos`).

## Requisitos

- **Python** 3.8 o superior
- **Django** 4.x
- **SQLite** (base de datos por defecto, aunque se puede configurar para otros motores como PostgreSQL)
- **Apache** (para despliegue en producción; opcional para desarrollo)
- **Dependencias de Python** (listadas en `requirements.txt`)

## Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/fdosalvo/horarios-proyecto.git
cd horarios-proyecto
```

### 2. Configurar un Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En macOS/Linux
# venv\Scripts\activate  # En Windows
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nota:** Si no tienes un archivo `requirements.txt`, puedes generarlo ejecutando `pip freeze > requirements.txt` desde tu entorno actual.

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio raíz del proyecto y configura las credenciales necesarias, como las de Google OAuth:

```env
GOOGLE_OAUTH_CLIENT_ID=tu-client-id-aqui
GOOGLE_OAUTH_CLIENT_SECRET=tu-client-secret-aqui
SECRET_KEY=tu-django-secret-key-aqui
```

Asegúrate de que el archivo `.env` esté incluido en `.gitignore` para evitar subir información sensible a GitHub.

### 5. Aplicar Migraciones

```bash
python manage.py migrate
```

### 6. Recolectar Archivos Estáticos

```bash
python manage.py collectstatic
```

### 7. Crear un Superusuario (Opcional)

Para acceder al panel de administración de Django:

```bash
python manage.py createsuperuser
```

### 8. Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

Accede a la aplicación en `http://localhost:8000`.

### 9. Configurar Apache (Opcional, para Producción)

Si estás desplegando en Apache:

- Configura un virtual host apuntando al directorio del proyecto.

- Asegúrate de que los módulos `mod_wsgi` estén habilitados.

- Ejemplo de configuración:

  ```apache
  <VirtualHost *:80>
      ServerName tu-dominio.com
      DocumentRoot /Library/WebServer/Documents/horarios/myproject
      WSGIScriptAlias / /Library/WebServer/Documents/horarios/myproject/myproject/wsgi.py
      <Directory /Library/WebServer/Documents/horarios/myproject>
          Require all granted
      </Directory>
      Alias /static /Library/WebServer/Documents/horarios/myproject/staticfiles
      <Directory /Library/WebServer/Documents/horarios/myproject/staticfiles>
          Require all granted
      </Directory>
  </VirtualHost>
  ```

- Reinicia Apache:

  ```bash
  sudo apachectl restart
  ```

## Estructura del Proyecto

- **myproject/**: Configuración principal del proyecto Django (settings.py, urls.py, wsgi.py).
- **myapp/**: Aplicación principal que contiene los modelos, vistas, templates y lógica del negocio.
  - `models.py`: Definición de modelos como `Apoderado`, `Alumno`, `Curso`, `Mensualidad`, etc.
  - `views.py`: Vistas para gestionar horarios, apoderados, alumnos, reportes y mensualidades.
  - `templates/myapp/`: Plantillas HTML para las páginas de la aplicación.
- **static/**: Archivos estáticos como CSS, JavaScript y traducciones de DataTables.

## Funcionalidades Principales

- **Gestión de Horarios:** Permite asignar horarios a profesores y cursos, con restricciones de disponibilidad.
- **Mantenedor de Apoderados:** Registro y gestión de apoderados, con soporte para múltiples alumnos por apoderado.
- **Reporte de Alumnos:** Lista de alumnos agrupados por año escolar y curso, con información de sus apoderados.
- **Mensualidades:** Gestión de pagos de mensualidades, con soporte para descuentos (en desarrollo).

## Desarrollo en Curso

- **Funcionalidad de Descuentos:** En la rama `feature-descuentos`, se está implementando la capacidad de aplicar descuentos a las mensualidades de los apoderados a partir de un mes específico.
- **Próximas Mejoras:** Agregar filtros avanzados a los reportes, exportación a PDF/Excel, y ordenamiento en las tablas.

## Contribución

1. Clona el repositorio y crea una nueva rama para tus cambios:

   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```

2. Realiza tus cambios y haz commit:

   ```bash
   git add .
   git commit -m "Descripción de los cambios"
   ```

3. Sube tu rama a GitHub:

   ```bash
   git push -u origin feature/nueva-funcionalidad
   ```

4. Crea un Pull Request en GitHub para revisión.

## Licencia

Este proyecto no tiene una licencia definida actualmente. Si deseas contribuir o usar el código, por favor contacta al propietario del repositorio.

## Contacto

- Propietario: Fernando Salvo
- Email: fernandosalvoaguilera@gmail.com
- Repositorio: https://github.com/fdosalvo/horarios-proyecto