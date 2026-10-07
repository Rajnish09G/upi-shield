from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi import Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from .crawler.capture import capture
from .crawler.app_inspector import inspect_apk
from .config import allowed_target, get_settings
from .db import close_connections, get_db_session, get_detections, init_db, save_detection
from .detection.scorer import score
from .evaluation import evaluate_labels
from .graph.builder import add_observation, graph_snapshot, init_schema
from .models import CaptureRequest, DetectionRequest, DetectionResponse, DiscoverRequest, GraphObservation
from .takedown.report import create_report


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_connections()


app = FastAPI(title="UPI Shield API", version="0.1.0", lifespan=lifespan)
app.mount("/artifacts", StaticFiles(directory=Path("data/captures")), name="artifacts")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    configured_key = get_settings().admin_api_key
    if configured_key and x_api_key != configured_key:
        raise HTTPException(status_code=401, detail="Valid X-API-Key header required")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/detections")
async def list_detections() -> list[DetectionResponse]:
    async for session in get_db_session():
        records = await get_detections(session)
    return [
        DetectionResponse(
            id=record.id, url=record.url, brand=record.brand, score=record.score,
            verdict=record.verdict, behavioral=record.signals,
            screenshot=record.screenshot, dom=record.dom,
            created_at=record.created_at,
        )
        for record in records
    ]


@app.post("/detections", dependencies=[Depends(require_api_key)])
async def create_detection(request: DetectionRequest) -> DetectionResponse:
    screenshot_path = Path(request.screenshot)
    dom_path = Path(request.dom)
    if not screenshot_path.is_absolute():
        screenshot_path = Path.cwd() / screenshot_path
    if not dom_path.is_absolute():
        dom_path = Path.cwd() / dom_path
    missing = [
        str(path)
        for path in (screenshot_path, dom_path)
        if not path.is_file()
    ]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Screenshot or DOM file was not found. Replace YOUR_ID with a real capture ID.",
                "missing": missing,
            },
        )
    settings = get_settings()
    detection = score(
        str(request.url), str(screenshot_path), str(dom_path), request.brand_keywords,
        settings.phishing_threshold, settings.suspicious_threshold,
    )
    async for session in get_db_session():
        record = await save_detection(
            session, detection, str(screenshot_path), str(dom_path)
        )
    return DetectionResponse(
        id=record.id, url=record.url, brand=record.brand, score=record.score,
        verdict=record.verdict, behavioral=record.signals,
        screenshot=record.screenshot, dom=record.dom,
        created_at=record.created_at,
    )


@app.post("/captures", response_model=DetectionResponse, dependencies=[Depends(require_api_key)])
async def capture_and_detect(request: CaptureRequest) -> DetectionResponse:
    if not allowed_target(str(request.url)):
        raise HTTPException(status_code=403, detail="Target is outside CRAWL_ALLOWLIST")
    capture_result = await capture(str(request.url))
    if not capture_result["ok"]:
        raise HTTPException(status_code=502, detail=capture_result.get("error"))
    settings = get_settings()
    detection = score(
        str(request.url), capture_result["screenshot"], capture_result["dom"],
        request.brand_keywords, settings.phishing_threshold, settings.suspicious_threshold,
    )
    async for session in get_db_session():
        record = await save_detection(
            session, detection, capture_result["screenshot"], capture_result["dom"]
        )
    return DetectionResponse(
        id=record.id, url=record.url, brand=record.brand, score=record.score,
        verdict=record.verdict, behavioral=record.signals,
        screenshot=record.screenshot, dom=record.dom,
        created_at=record.created_at,
    )


@app.post("/discover", dependencies=[Depends(require_api_key)])
async def discover(request: DiscoverRequest) -> dict:
    disallowed = [str(url) for url in request.urls if not allowed_target(str(url))]
    if disallowed:
        raise HTTPException(status_code=403, detail={"message": "Some targets are outside CRAWL_ALLOWLIST", "targets": disallowed})
    return {
        "source": request.source,
        "queued": [str(url) for url in request.urls],
        "count": len(request.urls),
        "next_step": "POST /captures for authorized targets",
    }


@app.post("/apps/inspect", dependencies=[Depends(require_api_key)])
async def inspect_app(path: str) -> dict:
    try:
        return inspect_apk(path)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/graph")
async def get_graph() -> dict:
    return await graph_snapshot()


@app.post("/graph/observations", dependencies=[Depends(require_api_key)])
async def create_graph_observation(observation: GraphObservation) -> dict[str, str]:
    await init_schema()
    await add_observation(**observation.model_dump())
    return {"status": "stored", "domain": observation.domain}


@app.get("/evaluation")
async def evaluation() -> dict:
    return evaluate_labels()


@app.get("/detections/{detection_id}", response_model=DetectionResponse)
async def get_detection(detection_id: int) -> DetectionResponse:
    async for session in get_db_session():
        records = [record for record in await get_detections(session) if record.id == detection_id]
    if not records:
        raise HTTPException(status_code=404, detail="Detection not found")
    record = records[0]
    return DetectionResponse(
        id=record.id, url=record.url, brand=record.brand, score=record.score,
        verdict=record.verdict, behavioral=record.signals,
        screenshot=record.screenshot, dom=record.dom,
        created_at=record.created_at,
    )


@app.get("/detections/{detection_id}/report")
async def detection_report(detection_id: int) -> Response:
    detection = await get_detection(detection_id)
    details = (
        f"URL: {detection.url}\nVerdict: {detection.verdict}\n"
        f"Score: {detection.score:.2f}\nBrand: {detection.brand or 'Unidentified'}\n"
        f"Signals: {detection.behavioral}"
    )
    return Response(
        content=create_report("UPI Shield takedown evidence", details),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=detection-{detection_id}.pdf"},
    )
