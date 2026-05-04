# Documentación de Despliegue — Render + Supabase

## Resumen

El proyecto fue desplegado usando **Render** como plataforma de hosting y **Supabase** como base de datos PostgreSQL en la nube. Ambos servicios tienen plan gratuito.

---

## 1. Cambios en el código para producción

### `Gestion_de_Casos_T4/requirements.txt`
Se agregaron 4 dependencias de producción:

| Paquete | Para qué sirve |
|---|---|
| `gunicorn` | Servidor WSGI para producción (reemplaza el `runserver` de desarrollo) |
| `psycopg2-binary` | Driver de conexión a PostgreSQL (Supabase) |
| `dj-database-url` | Permite configurar la DB con una sola URL en lugar de credenciales separadas |
| `whitenoise` | Sirve los archivos estáticos (CSS, JS, imágenes) directamente desde Django |

### `Gestion_de_Casos_T4/Gestion_Casos_Django_T4/settings.py`
Se modificó para leer la configuración sensible desde variables de entorno:

```python
# Antes (hardcodeado, inseguro)
SECRET_KEY = 'django-insecure-...'
DEBUG = True
ALLOWED_HOSTS = []
DATABASES = {'default': {'ENGINE': 'sqlite3', ...}}

# Después (desde variables de entorno)
SECRET_KEY = os.environ.get('SECRET_KEY', '<valor de desarrollo>')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
DATABASES = {'default': dj_database_url.config(default='sqlite:///...')}
```

También se agregó **Whitenoise** al middleware para servir estáticos:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <- agregado
    ...
]
```

### Archivos nuevos en la raíz del repo

| Archivo | Contenido |
|---|---|
| `Procfile` | Le dice a Render cómo arrancar la app |
| `requirements.txt` | Apunta al requirements.txt de la app (necesario para que Render lo encuentre) |
| `runtime.txt` | Especifica la versión de Python |
| `.env.example` | Plantilla de variables de entorno para otros desarrolladores |

---

## 2. Configuración de Supabase (Base de datos)

1. Crear cuenta y proyecto en [supabase.com](https://supabase.com)
2. Ir a **Connect → Connection string → Transaction pooler**
3. Copiar la URI con formato:
   ```
   postgresql://postgres.<proyecto>:<password>@aws-1-us-west-2.pooler.supabase.com:6543/postgres
   ```
4. Esta URI se usa como valor de la variable `DATABASE_URL` en Render

> Se usa el **Transaction pooler** (puerto 6543) y no la conexión directa porque Render es un entorno serverless que abre y cierra conexiones frecuentemente.

---

## 3. Configuración de Render (Hosting)

1. Crear cuenta en [render.com](https://render.com)
2. **New → Web Service** → conectar repositorio GitHub → seleccionar branch `develop`
3. Configurar:
   - **Language**: Python 3
   - **Build Command**:
     ```
     pip install -r requirements.txt && python Gestion_de_Casos_T4/manage.py collectstatic --noinput
     ```
   - **Start Command**:
     ```
     python Gestion_de_Casos_T4/manage.py migrate --noinput && gunicorn --chdir Gestion_de_Casos_T4 Gestion_Casos_Django_T4.wsgi:application --bind 0.0.0.0:$PORT
     ```

4. Agregar las siguientes variables de entorno en el dashboard:

| Variable | Valor |
|---|---|
| `SECRET_KEY` | Clave generada con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `<tu-app>.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://<tu-app>.onrender.com` |
| `DATABASE_URL` | URI de Supabase |
| `PYTHON_VERSION` | `3.12.7` |

> `PYTHON_VERSION=3.12.7` fue necesario porque Render por defecto usa Python 3.14, que no es compatible con `psycopg2-binary 2.9.9`.

5. Hacer deploy y verificar los logs de build
6. Una vez desplegado, crear el superusuario desde la **Shell de Render** (plan pago) o cargando datos iniciales con fixtures

---

## 4. URL de producción

La aplicación quedó desplegada en:
```
https://buro-2wvs.onrender.com
```

> **Nota free tier**: la app se duerme tras 15 minutos sin tráfico y tarda ~30 segundos en despertar ante la primera solicitud.

---

## 5. Flujo de actualización

Cuando hay cambios nuevos en el repo de la universidad:
```bash
git pull origin develop          # traer cambios del repo de la U
git push personal develop        # subir al repo personal (Render redeploya automáticamente)
```
