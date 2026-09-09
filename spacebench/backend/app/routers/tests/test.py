import json
import subprocess
from fastapi import APIRouter
import asyncio

from starlette.responses import StreamingResponse

from app.core.settings import settings

router = APIRouter(prefix="/api/tests", tags=["Tests"])


# ════════════ DEBUG MODE ══════════════════════════════════════════════════════════════════════════════════════════════
DEBUG_MODE = settings.DEBUG_MODE


@router.get("/run")
async def run_tests():

    async def stream():

        loop = asyncio.get_event_loop()

        process = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                ["pytest", "-vv", "--tb=line", "--no-header", "--color=no"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        )

        passed = 0
        failed = 0
        error = 0
        failure_logs = {}

        # retrieve stdout
        while True:
            raw = await loop.run_in_executor(None, process.stdout.readline)
            if not raw:
                break

            line = raw.decode().strip()
            if not line:
                continue

            # only get PASSED and FAILED line
            # e.g. app/tests/test_run_endpoints.py::test_get_run_logs_non_existing PASSED
            if ("PASSED" in line or "FAILED" in line or "ERROR" in line) and not line.startswith("FAILED") and not line.startswith("PASSED") and not line.startswith("ERROR"):
                parts = line.split('::')
                if len(parts) == 2:
                    file = parts[0].strip()         # app/tests/test_run_endpoints.py
                    rest = parts[1].strip()         # test_get_run_logs_non_existing PASSED
                    name = "[BACKEND] " + rest.split()[0]          # test_get_run_logs_non_existing
                    status = rest.split()[1]        # PASSED / FAILED

                    if status == "PASSED":
                        passed += 1
                    elif status == "FAILED":
                        failed += 1
                    elif status == "ERROR":
                        error += 1

                    test = {"type": "result", "file": file, "name": name, "status": status}
                    yield f"data: {json.dumps(test)}\n\n"

            if (line.startswith("FAILED") or line.startswith("ERROR")) and "::" in line and " - " in line:
                print(line)
                test_name = "[BACKEND] " + line.split("::")[1].split(" - ")[0].strip()
                error_msg = line.split(" - ", 1)[1].strip()
                yield f"data: {json.dumps({'type': 'failure', 'name': test_name, 'log': error_msg})}\n\n"

        # Send failure
        for name, log in failure_logs.items():
            yield f"data: {json.dumps({'type': 'failure_log', 'name': name, 'log': log.strip()})}\n\n"

        process.wait()
        yield f"data: {json.dumps({'type': 'done', 'passed': passed, 'failed': failed})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
