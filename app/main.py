"""
应用入口点
"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import routes
from config.config import settings


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title="Resume Screener API",
    description="基于LLM的智能简历筛选系统 API",
    default_response_class=UTF8JSONResponse,
)

# 跨域支持（前端单独部署时需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.SERVER_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(routes.router)

# 挂载内置静态前端页面（/ui）
_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/ui", StaticFiles(directory=_STATIC_DIR, html=True), name="ui")


@app.middleware("http")
async def add_charset_middleware(request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type and "charset" not in content_type.lower():
        if (
            content_type.startswith("text/")
            or content_type in ("application/json", "application/javascript")
        ):
            response.headers["content-type"] = content_type + "; charset=utf-8"
    return response


@app.get("/")
async def root():
    """根路径重定向到内置前端页面。"""
    if os.path.isdir(_STATIC_DIR):
        return RedirectResponse(url="/ui/")
    return {"message": "Welcome to the Resume Screener API"}
