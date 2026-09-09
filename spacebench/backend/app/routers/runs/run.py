import os

from typing import Optional

from app.services.runs.run import LaunchRunService
from app.core.settings import settings
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from app.models import Run
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_session, SessionLocal
from app.models.pod import Run, UploadedFile, RunRsoFile, RunLog
from app.schemas.pod import RunCreate, RunResponse, RunLogsResponse
from app.enums import RunStatus
from app.core.settings import settings

# ════════════ DEBUG MODE ══════════════════════════════════════════════════════════════════════════════════════════════
DEBUG_MODE = settings.DEBUG_MODE

router = APIRouter(prefix="/api/runs", tags=["Runs"])


async def log(run_id: str, lines: list[str]) -> None:
    async with SessionLocal() as session:
        run = await session.get(Run, run_id)
        for line in lines:
            run.logs += line + "\n"
        await session.commit()


# Run an analysis.
async def run_analysis(run_id: str) -> None:
    # logService = RunLogger(run_id)

    async with SessionLocal() as session:
        run = await session.get(Run, run_id)

        if run:
            if DEBUG_MODE: print("Run fields =>", {
                column.name: getattr(run, column.name)
                for column in run.__table__.columns
            })
        else:
            if DEBUG_MODE: print("Run not found")

        # get the rso files
        result = await session.execute(
            select(RunRsoFile.file_id).where(RunRsoFile.run_id == run_id)
        )
        rso_file_ids = result.scalars().all()


        rso_metadata = []
        rso_paths = []

        for file_id in rso_file_ids:
            rso_file = await session.get(UploadedFile, file_id)
            rso_paths.append(rso_file.stored_path)
            rso_metadata.append(rso_file.validation_metadata)

        # get the other files
        rinex_file = await session.get(UploadedFile, run.rinex_file_id)
        gnss_sp3_file = await session.get(UploadedFile, run.gnss_sp3_file_id)
        clk_file = await session.get(UploadedFile, run.gnss_clk_file_id)

        # custom estimator
        estimator_path = None

        if run.estimator_file_id:
            estimator_file = await session.get(UploadedFile, run.estimator_file_id)
            if estimator_file:
                estimator_path = estimator_file.stored_path

        # Get pre-validation Metadata
        metadata = {
            "rinex": rinex_file.validation_metadata,
            "gnss_sp3": gnss_sp3_file.validation_metadata,
            "rso_sp3": rso_metadata,
            "clk": clk_file.validation_metadata
        }

        estimator_file_id = None


        config = {
            "rinex_file_id": run.rinex_file_id,
            "gnss_sp3_file_id": run.gnss_sp3_file_id,
            "gnss_clk_file_id": run.gnss_clk_file_id,
            "rso_file_ids": rso_file_ids,
            "rinex_path": rinex_file.stored_path,
            "gnss_sp3_path": gnss_sp3_file.stored_path,
            "gnss_clk_path": clk_file.stored_path,
            "rso_sp3_paths": rso_paths,
            "orbital_model": run.orbital_model,
            "estimator_type": run.estimator_type,
            "estimator_file_id": estimator_file_id,
            "estimator_path": estimator_path,
            "max_iteration": run.max_iteration,
            "tolerance": run.tolerance
        }

        analysis_service = LaunchRunService()
        await analysis_service.launch(
            run_id=run_id,
            config=config,
            metadata=metadata
        )

        # logService.write_log('Pipeline completed successfully.', RunPhase.init)
        # logService.set_status(RunStatus.done)

        await session.commit()


async def organize_run_files(run: Run, rso_file_ids: list[str], session: AsyncSession):
    run_dir = os.path.join(settings.UPLOAD_DIR, run.id)
    os.makedirs(run_dir, exist_ok=True)

    all_files_ids = [run.rinex_file_id, run.gnss_sp3_file_id, run.gnss_clk_file_id]

    if run.estimator_file_id:
        all_files_ids.append(run.estimator_file_id)

    all_files_ids.extend(rso_file_ids)

    for file_id in all_files_ids:
        record = await session.get(UploadedFile, file_id)
        old_path = record.stored_path
        new_path = os.path.join(run_dir, os.path.basename(old_path))
        os.rename(old_path, new_path)
        record.stored_path = new_path

    if DEBUG_MODE: print(f"Files moved to {run_dir}")

    # Then, we remove any unwanted files.
    await clean_every_other_files(session)

    await session.flush()



# Remove any remaining files in UPLOAD_DIR.
async def clean_every_other_files(session: AsyncSession):

    upload_dir = settings.UPLOAD_DIR

    for file in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, file)


        if os.path.isfile(file_path):
            # Remove from database
            result = await session.execute(
                select(UploadedFile).where(UploadedFile.stored_path == file_path)
            )
            record = result.scalar_one_or_none()

            if record:
                await session.delete(record)

            # Remove from disk
            os.remove(file_path)









# ══ Endpoints ═════════════════════════════════════════════════════════════════

@router.post("", response_model=RunResponse, status_code=201)
async def create_run(
        payload: RunCreate,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_session),
):
    data = payload.model_dump()
    rso_file_ids = data.pop("rso_file_ids", [])

    if DEBUG_MODE: print(f"Payload to commit => {payload}")

    run = Run(**data)

    session.add(run)
    await session.flush()

    for file_id in rso_file_ids:
        session.add(RunRsoFile(run_id=run.id, file_id=file_id))

    # Before launching the run, move the files to the /{run_id} folder.
    await organize_run_files(run, rso_file_ids, session)

    await session.commit()

    result = await session.execute(
        select(Run).options(selectinload(Run.rso_files)).where(Run.id == run.id)
    )

    run = result.scalar_one()

    # print(f"This is the payload received => {payload}")

    background_tasks.add_task(run_analysis, run.id)

    return run


@router.get("/count")
async def count_runs(
        statuses: Optional[list[RunStatus]] = Query(default=None),
        session: AsyncSession = Depends(get_session),
):
    query = select(func.count()).select_from(Run)

    if statuses:
        query = query.where(Run.status.in_(statuses))

    result = await session.execute(query)

    return {"count": result.scalar()}


SORTABLE_FIELDS = {"id", "name", "orbital_model", "estimator_type", "status", "created_at", "rms_3d", "rms_radial",
                   "rms_along", "rms_cross"}


@router.get("", response_model=list[RunResponse])
async def list_runs(
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        statuses: Optional[list[RunStatus]] = Query(default=None),
        session: AsyncSession = Depends(get_session),
):
    if sort_by not in SORTABLE_FIELDS:
        sort_by = "created_at"

    col = getattr(Run, sort_by)

    order_expr = col.asc() if sort_order == "asc" else col.desc()

    #query = select(Run).order_by(order_expr)
    query = select(Run).options(selectinload(Run.rso_files)).order_by(order_expr)

    if statuses:
        query = query.where(Run.status.in_(statuses))

    result = await session.execute(query.offset(skip).limit(limit))

    return result.scalars().all()


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    #run = await session.get(Run, run_id)

    result = await session.execute(
        select(Run).options(selectinload(Run.rso_files)).where(Run.id == run_id)
    )
    run = result.scalar_one_or_none()


    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return run


@router.get("/{run_id}/logs", response_model=list[RunLogsResponse])
async def get_runlogs(run_id: str, session: AsyncSession = Depends(get_session)):

    result = await session.execute(select(RunLog).where(RunLog.run_id == run_id).order_by(RunLog.created_at.asc()))
    logs = result.scalars().all()

    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")

    return logs
