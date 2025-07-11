from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import httpx
import asyncio
from typing import Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="НБКР CORS Proxy",
    description="CORS прокси для API Национального банка КР",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Разрешенные домены для безопасности
ALLOWED_DOMAINS = [
    "nbkr.kg",
    "www.nbkr.kg"
]

def is_allowed_url(url: str) -> bool:
    """Проверка, разрешен ли домен для проксирования"""
    for domain in ALLOWED_DOMAINS:
        if domain in url:
            return True
    return False

@app.get("/")
async def root():
    """Информация о прокси"""
    return {
        "message": "НБКР CORS Proxy",
        "usage": "/proxy?url=https://nbkr.kg/XML/daily.xml",
        "allowed_domains": ALLOWED_DOMAINS
    }

@app.get("/proxy")
async def proxy_request(url: str = Query(..., description="URL для проксирования")):
    """
    Проксирует запрос к указанному URL с добавлением CORS заголовков
    """
    
    # Проверка безопасности
    if not is_allowed_url(url):
        raise HTTPException(
            status_code=403, 
            detail=f"Домен не разрешен. Разрешенные домены: {ALLOWED_DOMAINS}"
        )
    
    try:
        logger.info(f"Проксирование запроса к: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            
            # Определение content-type
            content_type = response.headers.get("content-type", "application/xml")
            
            logger.info(f"Ответ получен. Статус: {response.status_code}, Content-Type: {content_type}")
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers={
                    "Content-Type": content_type,
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=300"  # Кэш на 5 минут
                }
            )
            
    except httpx.TimeoutException:
        logger.error(f"Таймаут при запросе к {url}")
        raise HTTPException(status_code=504, detail="Таймаут запроса")
    
    except httpx.RequestError as e:
        logger.error(f"Ошибка запроса к {url}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Ошибка запроса: {str(e)}")
    
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Тестовый запрос к НБКР
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://nbkr.kg/XML/daily.xml")
            return {
                "status": "healthy",
                "nbkr_api_status": "available" if response.status_code == 200 else "unavailable",
                "nbkr_response_time": f"{response.elapsed.total_seconds():.2f}s"
            }
    except Exception as e:
        return {
            "status": "degraded",
            "nbkr_api_status": "unavailable",
            "error": str(e)
        }

# Специфичные эндпоинты для НБКР API
@app.get("/nbkr/daily")
async def get_daily_rates():
    """Получить ежедневные курсы валют"""
    return await proxy_request("https://nbkr.kg/XML/daily.xml")

@app.get("/nbkr/weekly")
async def get_weekly_rates():
    """Получить еженедельные курсы валют"""
    return await proxy_request("https://nbkr.kg/XML/weekly.xml")

@app.get("/nbkr/reference")
async def get_currency_reference():
    """Получить справочник валют"""
    return await proxy_request("https://nbkr.kg/XML/CurrenciesReferenceList.xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )