"""Aplicação FastAPI para o tutor de código IPEIA VIBE CODING."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import get_settings
from services.kimi_service import (
    KimiAuthError,
    KimiConnectionError,
    KimiInvalidRequestError,
    KimiRateLimitError,
    KimiService,
    KimiServiceError,
    KimiServiceUnavailableError,
)

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not app.state.kimi.configured:
        logger.warning(
            "A KIMI_API_KEY não está configurada. A interface vai funcionar, mas /api/composer "
            "retornará 503 até que uma chave de API seja fornecida."
        )
    yield
    logger.info("Desligando o servidor IPEIA VIBE CODING.")


app = FastAPI(title="IPEIA VIBE CODING", version="0.2.0", lifespan=lifespan)
app.state.kimi = KimiService(
    request_timeout=settings.kimi_request_timeout,
    max_code_chars=settings.max_code_chars,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComposeRequest(BaseModel):
    code: str = Field(..., description="O código-fonte a ser melhorado.")
    prompt: str = Field(..., description="O que o modelo deve fazer com o código.")
    language: str = Field(default="python", description="Linguagem de programação.")


class ComposeResponse(BaseModel):
    success: bool
    data: dict


@app.exception_handler(KimiServiceError)
async def kimi_service_error_handler(request: Request, exc: KimiServiceError):
    """Converte exceções do serviço em respostas JSON com tipo e mensagem em português."""
    logger.warning("KimiServiceError em %s: %s", request.url.path, exc)

    status_map = {
        KimiAuthError.error_type: 401,
        KimiRateLimitError.error_type: 429,
        KimiServiceUnavailableError.error_type: 503,
        KimiConnectionError.error_type: 503,
        KimiInvalidRequestError.error_type: 400,
        KimiServiceError.error_type: 502,
    }
    status_code = status_map.get(exc.error_type, 502)

    return JSONResponse(
        status_code=status_code,
        content={"error_type": exc.error_type, "message": exc.message},
    )


@app.get("/api/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "kimi_configured": app.state.kimi.configured,
    }


@app.post("/api/composer", response_model=ComposeResponse)
async def composer(req: ComposeRequest) -> ComposeResponse:
    try:
        result = await app.state.kimi.compose(req.code, req.prompt, req.language)
        return ComposeResponse(success=True, data=result)
    except KimiServiceError:
        # Handled by the dedicated exception handler above.
        raise
    except Exception as exc:
        logger.exception("Erro inesperado em /api/composer")
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


# Mount static files LAST so API routes take precedence. Using html=True serves
# index.html for the root path and any unmatched path that does not match a file.
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Iniciando servidor IPEIA VIBE CODING em %s:%s",
        settings.app_host,
        settings.app_port,
    )
    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=True)
