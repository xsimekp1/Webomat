from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import auth, admin, crm, upload, website, web_project, preview, feedback

settings = get_settings()

app = FastAPI(
    title="Webomat API",
    description="CRM & Business Discovery System API",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(crm.router)
app.include_router(upload.router)
app.include_router(website.router)
app.include_router(web_project.router)
app.include_router(preview.router)
app.include_router(feedback.router)


@app.get("/")
async def root():
    return {"message": "Webomat API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
