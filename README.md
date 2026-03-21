# Guía de Configuración: Seguros Personas (Django + Tailwind)
[Haz clic aquí para abrir el archivo](https://drive.google.com/file/d/1Hj7k6iPfRRL13Vury6V1PbIoZIvbV6fG/view?usp=sharing)

## 1️⃣ Configuración del Entorno Python
Sigue estos comandos para preparar el entorno virtual e instalar las dependencias del backend:

# Crear el entorno virtual
python -m venv venv

# Activar el entorno
# En Windows: venv\Scripts\activate
# En Linux/Mac: source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

## 2️⃣ Configuración de Base de Datos (MySQL)
Antes de continuar, asegúrate de tener MySQL corriendo y crea la base de datos necesaria:

1. Abre tu terminal de MySQL o herramienta (HeidiSQL, Workbench, etc.).
2. Crea la base de datos: CREATE DATABASE seguros_personas;
3. La configuración en settings.py es:
   - NAME: 'seguros_personas'
   - USER: 'root'
   - PASSWORD: 'root'
   - HOST: 'localhost'
   - PORT: '3306'

# Una vez creada la BD, aplica las migraciones:
python manage.py migrate

# Crea tu acceso de administrador:
python manage.py createsuperuser

## 3️⃣ Configuración de Tailwind CSS (Frontend)
Necesitas Node.js y npm instalados en tu sistema. Si no tienes los paquetes instalados en el proyecto, ejecuta:

# Entrar a la carpeta donde está el package.json (si aplica) y ejecutar:
npm install

# Si Tailwind no se instaló correctamente por alguna razón, forzar:
npm install -D tailwindcss@3 postcss autoprefixer

## 4️⃣ Ejecución del Proyecto (Doble Terminal)
Para que el proyecto funcione correctamente, DEBES tener dos terminales abiertas simultáneamente:

--- TERMINAL 1: DJANGO ---
# (Asegúrate de tener el venv activo)
python manage.py runserver

--- TERMINAL 2: TAILWIND ---
# Este comando compila y vigila cambios en el CSS:
npx tailwindcss -i ./input.css -o ./static/css/output.css --watch

# Para generar la versión final optimizada (Producción):
npx tailwindcss -i ./input.css -o ./static/css/output.css --minify

## 🛠 Solución de problemas rápidos
- Si 'npx tailwindcss' falla: Verifica que el archivo 'package.json' no tenga el nombre "tailwind" como nombre de proyecto (cámbialo a "seguros-css").
- MySQL: Asegúrate de que el servicio esté activo antes de migrar.

 El proyecto estará disponible en: http://127.0.0.1:8000/


 npm install -D tailwindcss@3 postcss autoprefixer

 mysql.server start
 mysql.server stop
 mysql -u root
 brew services start redis
 brew services stop redis
 redis-server
 redis-cli ping
 celery -A config worker --loglevel=info
