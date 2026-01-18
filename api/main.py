import os
from fastapi import FastAPI
from dotenv import load_dotenv

from api.routes.intake import router as intake_router
from api.routes.qualify import router as qualify_router
from api.routes.admin import router as admin_router
from api.routes.status import router as status_router
from api.routes.dashboard import router as dashboard_router
from api.routes.outreach import router as outreach_router
from api.routes.onboarder import router as onboarder_router
from api.routes.voice import router as voice_router


load_dotenv()

app = FastAPI(
    title="Solo AI Automation API",
    version="1.0.0",
)

app.include_router(intake_router)
app.include_router(qualify_router)
app.include_router(admin_router)
app.include_router(status_router)
app.include_router(dashboard_router)
app.include_router(outreach_router)
app.include_router(onboarder_router)
app.include_router(voice_router)


@app.get("/")
def root():
    return {"status": "ok"}
