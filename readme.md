# Steps To Run The Project Using Docker
## 1. Create The project directory and enter it

## 2. Create The Dockerfile

## 3. Run The Command In The Terminal: 
docker run --rm -v ${PWD}:/app -w /app python:3.12-slim sh -c "pip install django && django-admin startproject docaroo ."

## 4. To Create The Frontend Run This Command
npm create vite@latest frontend -- --template react
### Note: if you encounter an that says 'npm.ps1 is not digitally signed' then open windows powershell in adminstrator and run:
Set-ExecutionPolicy RemoteSigned
## 5. Select The Following Options
framework:      react 
variant:        typescript
install now:    no

## 6. Update The vite.config.ts File From Frontend
```
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",   // ← required so Docker can expose the port
    port: 3000,
    proxy: {
      // Proxy /api calls to Django — avoids CORS issues in dev
      "/api": {
        target: "http://django:8000",  // use container name, not localhost
        changeOrigin: true,
      },
    },
  },
});
```

## 7. Update The Settings.py File From docaroo
```
import os

# Database
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     os.environ.get("DB_NAME",     "mydb"),
        "USER":     os.environ.get("DB_USER",     "myuser"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "mypassword"),
        "HOST":     os.environ.get("DB_HOST",     "localhost"),
        "PORT":     os.environ.get("DB_PORT",     "5432"),
    }
}

# CORS
INSTALLED_APPS = [
    ...
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ← top of middleware
    ...
]

CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]

```
## 8. Run The Following Docker-Compose Command To Build Dev Enviornment
docker compose -f docker-compose.dev.yml up --build


## 9. Now Everything Should Be Ready.Use The Following Commands To Navigate Around
### Django — create a new app
docker compose -f docker-compose.dev.yml exec django python manage.py startapp cameras

### Django — make and run migrations
docker compose -f docker-compose.dev.yml exec django python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec django python manage.py migrate

### Django — create superuser
docker compose -f docker-compose.dev.yml exec django python manage.py createsuperuser

### React — install a new package
docker compose -f docker-compose.dev.yml exec frontend npm install axios react-router-dom @types/react-router-dom react-markdown

### start
docker compose -f docker-compose.dev.yml up

### stop
docker compose -f docker-compose.dev.yml down

### rebuild after changing Dockerfile or requirements.txt
docker compose -f docker-compose.dev.yml up --build

### see logs of one container
docker compose -f docker-compose.dev.yml logs -f django

### open a shell inside a container
docker compose -f docker-compose.dev.yml exec django bash
docker compose -f docker-compose.dev.yml exec frontend sh

### The only time you need to rebuild
Changed requirements.txt      → docker compose up --build
Changed Dockerfile             → docker compose up --build
Changed settings.py            → just save, Django auto-reloads
Changed any .py or .jsx file   → just save, auto-reloads