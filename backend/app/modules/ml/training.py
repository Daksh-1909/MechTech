"""Bounded, local background execution for administrator-requested training."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.enums import ModelType, TrainingJobStatus
from app.models.training_job import MLTrainingJob
from app.models.user import User
from app.modules.ml import service as ml_service

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml-training")
_submission_lock = threading.Lock()


def _active_job(db: Session) -> MLTrainingJob | None:
    return db.scalar(
        select(MLTrainingJob)
        .where(MLTrainingJob.status.in_(["queued", "running"]))
        .order_by(MLTrainingJob.created_at)
    )


def submit_job(
    db: Session, *, actor: User, model_type: ModelType, parameters: dict
) -> MLTrainingJob:
    with _submission_lock:
        if _active_job(db) is not None:
            raise AppError(
                "A model training job is already queued or running.",
                code="TRAINING_BUSY",
                status_code=409,
            )
        job = MLTrainingJob(
            id=str(uuid4()),
            submitted_by_user_id=actor.id,
            model_type=model_type.value,
            model_name=parameters["model_name"],
            model_version=parameters["model_version"],
            parameters_json=parameters,
            status=TrainingJobStatus.QUEUED.value,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        _executor.submit(_run_job, job.id)
        return job


def get_job(db: Session, job_id: str) -> MLTrainingJob:
    job = db.get(MLTrainingJob, job_id)
    if job is None:
        raise AppError("Training job not found.", code="NOT_FOUND", status_code=404)
    return job


def _run_job(job_id: str) -> None:
    with SessionLocal() as db:
        job = db.get(MLTrainingJob, job_id)
        if job is None:
            return
        job.status = TrainingJobStatus.RUNNING.value
        job.started_at = utcnow()
        db.commit()
        try:
            params = job.parameters_json
            output = settings.data_root / "models" / "jobs" / f"{job.id}.joblib"
            output.parent.mkdir(parents=True, exist_ok=True)
            if job.model_type == ModelType.CLASSIFICATION.value:
                from scripts.train_random_forest import train_and_evaluate

                report_path, report = train_and_evaluate(
                    runs=params["runs"],
                    test_runs=params["test_runs"],
                    samples_per_scenario=params["samples_per_scenario"],
                    seed=params["seed"],
                    minimum_score=params["minimum_score"],
                    output=output,
                    model_name=job.model_name,
                    model_version=job.model_version,
                )
            else:
                from scripts.train_isolation_forest import train_and_evaluate

                report_path, report = train_and_evaluate(
                    train_runs=params["runs"],
                    evaluation_runs=params["test_runs"],
                    samples_per_scenario=params["samples_per_scenario"],
                    seed=params["seed"],
                    contamination=params["contamination"],
                    output=output,
                    model_name=job.model_name,
                    model_version=job.model_version,
                )
            actor = db.get(User, job.submitted_by_user_id) if job.submitted_by_user_id else None
            if actor is None:
                raise RuntimeError("Submitting administrator no longer exists.")
            model = ml_service.register_model(
                db,
                actor=actor,
                model_name=job.model_name,
                model_version=job.model_version,
                model_type=ModelType(job.model_type),
                artifact_path=str(output),
                training_dataset_description="Run-separated synthetic training job",
                evaluation_metrics_json=report,
                training_dataset_version="1.0",
                activate=False,
            )
            job.model_registry_id = model.id
            job.result_json = {"report": report, "report_file": str(Path(report_path).name)}
            job.status = TrainingJobStatus.SUCCEEDED.value
            job.finished_at = utcnow()
            db.commit()
        except Exception:
            logger.exception("ML training job %s failed", job_id)
            db.rollback()
            job = db.get(MLTrainingJob, job_id)
            if job is not None:
                job.status = TrainingJobStatus.FAILED.value
                job.error_message = "Training failed. Check the server log using the job ID."
                job.finished_at = utcnow()
                db.commit()
