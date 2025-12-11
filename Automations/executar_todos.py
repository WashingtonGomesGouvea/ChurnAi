"""
Run all lab pipelines sequentially at 17:00 every day.

If the script starts after 17:00, it checks whether today's run is already
finished (via the pipeline flag files). If anything is pending, it runs the
missing pipelines immediately; otherwise, it waits until 17:00 on the next day.
The window stays open and keeps scheduling future runs and shows the next run.
"""

from __future__ import annotations

import getpass
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable


RUN_HOUR = 17
RUN_MINUTE = 0
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _hostname_username() -> tuple[str, str]:
    return socket.gethostname().lower(), getpass.getuser().lower()


def _detect_base_dir(job_key: str) -> Path:
    """
    Mirror the per-script machine detection so the orchestrator reads the same
    flag files the pipelines create.
    """
    hostname, username = _hostname_username()

    if job_key == "cunha":
        if username == "washington.gouvea" or "synvia" in hostname or "washington" in hostname:
            return Path(r"C:\Users\washington.gouvea\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\cunha")
        return Path(r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\cunha")

    if job_key == "db":
        if username == "washington.gouvea" or "synvia" in hostname or "washington" in hostname:
            return Path(r"C:\Users\washington.gouvea\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\db")
        if username == "washi" or "washi" in hostname:
            return Path(r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\db")
        return PROJECT_ROOT / "Automations" / "dbLabV2" / "arquivos"

    if job_key == "sodre":
        if username == "washington.gouvea" or "synvia" in hostname or "washington" in hostname:
            return Path(r"C:\Users\washington.gouvea\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\sodre")
        if username == "washi" or "washi" in hostname:
            return Path(r"D:\OneDrive - Synvia Group\Data Analysis\Churn PCLs\Automations\sodre")
        return PROJECT_ROOT / "Automations" / "sodreLabV2" / "arquivos"

    raise ValueError(f"Unknown job key: {job_key}")


def _next_run_time(reference: datetime) -> datetime:
    target = reference.replace(hour=RUN_HOUR, minute=RUN_MINUTE, second=0, microsecond=0)
    if reference < target:
        return target
    return target + timedelta(days=1)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


@dataclass
class ScriptJob:
    key: str
    name: str
    script_path: Path
    flag_style: str  # "per_file" or "consolidated"

    @property
    def base_dir(self) -> Path:
        return _detect_base_dir(self.key)

    def has_run_for(self, date_str: str) -> bool:
        if self.flag_style == "per_file":
            return (self.base_dir / f".pipeline_completo_{date_str}.flag").exists()

        flag_file = self.base_dir / ".pipeline_completo.flag"
        if not flag_file.exists():
            return False

        prefix = f"{date_str}:"
        try:
            with flag_file.open(encoding="utf-8") as handle:
                return any(line.startswith(prefix) for line in handle)
        except OSError:
            return False

    def run(self) -> bool:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] Running {self.name} ...")
        if not self.script_path.exists():
            print(f"  !! Script not found: {self.script_path}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(self.script_path)],
                cwd=PROJECT_ROOT,
                check=False,
            )
        except Exception as exc:  # pragma: no cover - defensive
            print(f"  !! Failed to launch {self.name}: {exc}")
            return False

        if result.returncode != 0:
            print(f"  !! {self.name} exited with code {result.returncode}")
            return False

        print(f"  -> {self.name} finished successfully.")
        return True


def _build_jobs() -> list[ScriptJob]:
    return [
        ScriptJob(
            key="cunha",
            name="Cunha (Gralab)",
            script_path=PROJECT_ROOT / "Automations" / "cunha" / "cunhaLabV2.py",
            flag_style="per_file",
        ),
        ScriptJob(
            key="sodre",
            name="Sodre",
            script_path=PROJECT_ROOT / "Automations" / "sodreLabV2" / "sodreLabV2.py",
            flag_style="consolidated",
        ),
        ScriptJob(
            key="db",
            name="DB Tox",
            script_path=PROJECT_ROOT / "Automations" / "dbLabV2" / "dbLabV2.py",
            flag_style="consolidated",
        ),
    ]


def _print_status(jobs: Iterable[ScriptJob], date_str: str) -> None:
    parts = []
    for job in jobs:
        state = "OK" if job.has_run_for(date_str) else "PENDING"
        parts.append(f"{job.name}: {state}")
    joined = " | ".join(parts)
    print(f"[Status {date_str}] {joined}")


def _run_pending(jobs: Iterable[ScriptJob], date_str: str) -> bool:
    for job in jobs:
        if job.has_run_for(date_str):
            print(f"[{job.name}] already completed for {date_str}, skipping.")
            continue

        ok = job.run()
        if not ok:
            print(f"Stopped chain after {job.name}.")
            return False

    return True


def main() -> None:
    jobs = _build_jobs()
    now = datetime.now()
    today_str = now.date().isoformat()
    current_target = now.replace(hour=RUN_HOUR, minute=RUN_MINUTE, second=0, microsecond=0)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Daily run time: {RUN_HOUR:02d}:{RUN_MINUTE:02d}")
    for job in jobs:
        print(f"- {job.name} flags in: {job.base_dir}")

    _print_status(jobs, today_str)

    if now >= current_target:
        if any(not job.has_run_for(today_str) for job in jobs):
            print("After scheduled time and there are pending runs -> executing now.")
            if not _run_pending(jobs, today_str):
                print("Chain stopped due to failure; fix and restart to reschedule.")
            else:
                _print_status(jobs, today_str)
        else:
            print("After scheduled time but all jobs already done for today.")
        next_run = _next_run_time(now)
    else:
        print(f"Waiting until {RUN_HOUR:02d}:{RUN_MINUTE:02d} today.")
        next_run = current_target

    print(f"Next run scheduled for {_fmt(next_run)} (keep this window open).")

    try:
        while True:
            sleep_seconds = max(0, (next_run - datetime.now()).total_seconds())
            if sleep_seconds > 0:
                time.sleep(min(sleep_seconds, 60))
                continue

            run_date = datetime.now().date().isoformat()
            _run_pending(jobs, run_date)
            _print_status(jobs, run_date)
            next_run = _next_run_time(datetime.now())
            print(f"Next run scheduled for {_fmt(next_run)} (keep this window open).")
    except KeyboardInterrupt:
        print("\nScheduler stopped by user.")


if __name__ == "__main__":
    main()
