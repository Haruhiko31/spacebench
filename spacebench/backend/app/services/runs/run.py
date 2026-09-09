import httpx
from app.core.settings import settings


class LaunchRunService:
    def __init__(self) -> None:
        self.pod_engine_url = settings.POD_ENGINE_URL

    async def launch(self, run_id: str, config: dict, metadata: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.pod_engine_url}/runs",
                json={
                    "run_id": run_id,
                    "config": config,
                    "metadata": metadata,
                }
            )

            # if the response has not been accepted by POD Engine.
            if response.status_code != 200:
                raise Exception(f"Pod engine error : {response.text}")


