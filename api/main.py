from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.auth import SESSION_COOKIE, SESSION_MAX_AGE_SECONDS, create_session_token, is_authenticated, verify_credentials
from api.routes import collect, core_pages, intelligence, sites, stats, visitor_rules


app = FastAPI(title="Website Visitor Intelligence", version="0.2.0")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")

app.include_router(sites.router, prefix="/api")
app.include_router(collect.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(core_pages.router, prefix="/api")
app.include_router(visitor_rules.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")

PUBLIC_PATHS = (
    "/health",
    "/login",
    "/static/",
    "/api/collect/access-log",
)


@app.middleware("http")
async def dashboard_auth_middleware(request: Request, call_next):
    path = request.url.path
    is_public = path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PATHS if prefix.endswith("/"))
    protected = (
        path in {"/", "/dashboard", "/docs", "/redoc", "/openapi.json"}
        or path.startswith("/api/sites")
        or path.startswith("/api/stats")
        or path.startswith("/api/core-pages")
        or path.startswith("/api/visitor-rules")
        or path.startswith("/api/intelligence")
    )

    if protected and not is_public and not is_authenticated(request):
        if path.startswith("/api/") or path == "/openapi.json":
            return JSONResponse({"detail": "authentication required"}, status_code=401)
        return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse(url="/dashboard")


@app.get("/login", include_in_schema=False)
def login_page():
    return FileResponse(FRONTEND_DIR / "login.html", headers={"Cache-Control": "no-store"})


@app.post("/login", include_in_schema=False)
async def login(request: Request):
    payload = await request.json()
    username = str(payload.get("username", ""))
    password = str(payload.get("password", ""))
    if not verify_credentials(username, password):
        return JSONResponse({"detail": "invalid username or password"}, status_code=401)

    response = JSONResponse({"ok": True})
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(username),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/logout", include_in_schema=False)
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html", headers={"Cache-Control": "no-store"})


@app.get("/health")
def health():
    return {"status": "ok"}
