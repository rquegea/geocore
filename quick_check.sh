#!/bin/bash

echo "�� Verificación rápida del proyecto..."
echo "📍 Directorio actual: $(pwd)"

# Archivos críticos del backend
echo "Backend:"
[ -f "backend/app.py" ] && echo "✅ app.py" || echo "❌ app.py FALTA"
[ -f "backend/.env" ] && echo "✅ .env" || echo "❌ .env FALTA"  
[ -f "backend/src/scheduler/poll.py" ] && echo "✅ scheduler" || echo "❌ scheduler FALTA"

# Archivos críticos del frontend
echo "Frontend:"
[ -f "frontend/package.json" ] && echo "✅ package.json" || echo "❌ package.json FALTA"
[ -f "frontend/app/api/mentions/route.ts" ] && echo "✅ API routes" || echo "❌ API routes FALTA"
[ -f "frontend/types.ts" ] && echo "✅ types.ts" || echo "❌ types.ts FALTA"

# Estado de servicios
echo "Servicios:"
curl -s http://localhost:5050/health >/dev/null && echo "✅ Backend corriendo" || echo "⚠️ Backend no corriendo"
curl -s http://localhost:3000 >/dev/null && echo "✅ Frontend corriendo" || echo "⚠️ Frontend no corriendo"

echo "🏁 Verificación completada"
