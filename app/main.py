"""
应用入口点
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import routes
from config.config import settings

app = FastAPI(title="Resume Screener API", description="基于LLM的智能简历筛选系统 API")

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


@app.get("/")
async def root():
    """根路径重定向到内置前端页面。"""
    if os.path.isdir(_STATIC_DIR):
        return RedirectResponse(url="/ui/")
    return {"message": "Welcome to the Resume Screener API"}
