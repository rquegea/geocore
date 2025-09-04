# 🤖 AI Visibility MVP

Sistema de monitoreo de visibilidad de marca en respuestas de IA (ChatGPT, Claude, etc.)

## 🎯 Características

- **Dashboard en tiempo real** con métricas de visibilidad
- **Análisis de sentimiento** de menciones de marca
- **Monitoreo multi-modelo** (GPT, Claude, Gemini, etc.)
- **Word cloud** de temas relevantes
- **Ranking competitivo** de industria
- **Sistema de insights** automático con CTAs

## 🏗️ Arquitectura

```
ai-visibility-mvp/
├── backend/          # API Flask + PostgreSQL
├── frontend/         # Next.js 14 + TypeScript
├── docker-compose.yml
└── scripts/          # Herramientas de desarrollo
```

## 🚀 Instalación Rápida

### 1. Clonar repositorio
```bash
git clone <tu-repo-url>
cd ai-visibility-mvp
```

### 2. Configurar Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configurar variables
```

### 3. Configurar Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local  # Configurar variables
```

### 4. Levantar Base de Datos
```bash
docker-compose up -d
```

### 5. Ejecutar Servicios
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && python app.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

## 🌐 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5050
- **Health Check**: http://localhost:5050/health

## 📊 Endpoints Principales

- `GET /api/visibility` - Métricas de visibilidad
- `GET /api/mentions` - Lista de menciones
- `GET /api/insights` - Insights y CTAs
- `GET /api/topics` - Análisis de temas

## 🛠️ Desarrollo

### Test de Endpoints
```bash
./test_endpoints.sh
```

### Depuración Completa
```bash
./debug_dashboard.sh
```

### Generar Datos de Prueba
```bash
cd backend
python -c "from src.scheduler.poll import main; main(loop_once=True)"
```

## 🔧 Stack Tecnológico

- **Backend**: Flask, PostgreSQL, SQLAlchemy
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Charts**: Recharts
- **Containerización**: Docker
- **UI**: Shadcn/ui

## 📝 Variables de Entorno

### Backend (.env)
```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=ai_visibility
DB_USER=postgres
DB_PASSWORD=postgres
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:5050
```

## 🚀 Deployment

[Instrucciones de deployment pendientes]

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.
