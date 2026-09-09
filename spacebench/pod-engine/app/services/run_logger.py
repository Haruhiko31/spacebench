from app.core.database import SessionLocal
from ..models import Run, RunLog
from ..enums import *


''' This helper is used to write log to the database '''
class RunLogger:
    def __init__(self, run_id: str):
        self.run_id = run_id

    async def write_log(
            self,
            message: str,
            phase: str = "",
            level: str = LogLevel.info
    ) -> None:
        async with SessionLocal() as session:
            run = await session.get(Run, self.run_id)

            if not run:
                print(f"[RunLogger] Run not found : {self.run_id}")
                return


            session.add(RunLog(
                    run_id = run.id,
                    level = level,
                    phase = phase.upper(),
                    message = message

                )
            )

            await session.commit()

    async def set_status(self, status: str) -> None:
        async with SessionLocal() as session:
            run = await session.get(Run, self.run_id)

            if not run:
                print(f"[RunLogger] Run not found : {self.run_id}")
                return

            run.status = status
            await session.commit()

