#!/bin/bash

echo "🚀 Starting Retail Action Plan Generator MVP..."
echo ""

# 启动 Docker 容器
echo "📦 Building and starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "🗄️  Initializing database..."
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Application is running at: http://localhost:8000"
echo ""
echo "📊 To view logs, run: docker-compose logs -f"
echo "🛑 To stop, run: docker-compose down"
echo ""

