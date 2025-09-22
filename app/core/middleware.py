import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.infrastructure.logging import logger

class RequestIDLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = Response("Internal Server Error", status_code=500)  # <-- default seguro
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception("Unhandled error req_id=%s path=%s: %s", rid, request.url.path, e)
            return response
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "req_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                rid, request.method, request.url.path,
                getattr(response, "status_code", "NA"), elapsed
            )
