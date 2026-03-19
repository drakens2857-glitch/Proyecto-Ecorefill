# 🌱 Eco-Refill

## 📖 Introducción y Descripción

Eco-Refill es una aplicación que permite gestionar de manera profesional
las labores dentro de un entorno de trabajo mediante un sistema de
tareas. El sistema cuenta con dos roles principales: **👑 Administrador** y
**👷Trabajador**, cada uno con diferentes privilegios y funciones.

### 👷 Rol Trabajador

Cada trabajador puede gestionar sus propias tareas dentro de la
plataforma. Las acciones disponibles son:

-  📝 Crear tareas
-  ✏️ Modificar tareas cuando necesiten ajustes
-  ❌ Eliminar tareas si fueron creadas por error
-  🔄 Cambiar el estado de las tareas

Las tareas cuentan con los siguientes estados:

-  ⏳ Pendiente
-  ⚙️ En proceso
-  ✅ Completada

Cada trabajador dispone de **un perfil exclusivo**, lo que significa que
únicamente el propietario de la cuenta puede ver sus propias tareas.
Esto evita confusiones entre trabajadores y previene que las tareas de
diferentes usuarios se mezclen.

### 👑 Rol Administrador

El administrador tiene la función de **supervisar todo el sistema**.
Entre sus privilegios se encuentran:

-  👥 Ver las cuentas de todos los trabajadores
-  📋 Consultar las tareas de cada trabajador
-  📊 Supervisar el progreso de las tareas

### 🤖 Integración de Inteligencia Artificial

El sistema también incluye una **IA para automatizar acciones dentro del
sistema**.

🧠 Ejemplo de uso:

Eliminar una tarea usando IA:

Eliminar la tarea con el nombre (Nombre de la tarea)

La IA buscará la tarea y la eliminará automáticamente.

También se pueden **crear plantillas de tareas** usando la IA:

Crear tarea con nombre (Nombre de la tarea)

La IA generará una plantilla de tarea que luego el usuario podrá
modificar con los datos correspondientes.

------------------------------------------------------------------------

# ⚙️ Requisitos de Instalación

Para ejecutar este proyecto correctamente es necesario tener instaladas
las siguientes dependencias:

django\>=4.2 
djangorestframework\>=3.14 
drf-spectacular\>=0.27
firebase-admin\>=6.4 
python-decouple\>=3.8 
django-cors-headers\>=4.3
requests\>=2.31 
cloudinary\>=1.36 
google-genai\>=1.0

------------------------------------------------------------------------

# 🛠️ Guía de Instalación

Sigue los pasos a continuación para instalar y ejecutar el proyecto
correctamente.

### 1. Crear el entorno virtual

` py -m venv venv `

### 2. Activar el entorno virtual

.`\venv`{=tex}`\Scripts`{=tex}`\activate`{=tex}

### 3. Instalar las dependencias

` pip install Django `
` pip install djangorestframework `
` pip install drf-spectacular `
` pip install firebase-admin `
` pip install python-decouple `
` pip install django-cors-headers ` 
` pip install requests `
` pip install cloudinary `
` pip install google-genai `

### 4. Clonar el repositorio

` git clone "LINK_HTTPS_DEL_REPOSITORIO" `

### 5. Crear archivo .env

Se debe generar un archivo `.env` donde se almacenarán las ** 🔑 claves de
la API**.\
Estas claves son privadas y únicamente los propietarios del proyecto
deben tener acceso a ellas.

### 6. Agregar ServiceAccountKey

Se debe insertar en la carpeta del proyecto el archivo:

serviceAccountKey.json

Este archivo contiene la ** 🔐 clave principal de Firebase**, que permite la
conexión con la base de datos donde se almacenará la información.

### 7. Ejecutar el servidor

`python manage.py runserver`

------------------------------------------------------------------------

# 💻 Stack Tecnológico

Las tecnologías utilizadas en este prototipo son:

- 🐍 Django
- 🔗 Django REST Framework
- 🔥 Firebase
- ☁️ Cloudinary
- 🤖 Google Gemini

------------------------------------------------------------------------

# 📚 Documentación de la API
📄 
https://docs.google.com/document/d/1XHGqoVcxy1JL-wiFlDK6rNiMyq8sQAST2F3LFDlJGwQ/edit?usp=sharing

------------------------------------------------------------------------

# 👤 Cuenta del Proyecto

### 🏷️ Nombre de la cuenta

- drakens2857-glitch

### 👨‍💻 Propietario de la cuenta

- Nicolas Santiago Bello Neira

### 🤝 Colaboradores

- Frankyn Villalba Hortua
