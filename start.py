from pathlib import Path
import subprocess

project_dir = Path("/Users/papi71/PycharmProjects/book_scareglia/booking-agent")

subprocess.run(
    [
        "uv",
        "run",
        "streamlit",
        "run",
        str(project_dir / "app.py"),
    ],
    cwd=project_dir,
    check=True,
)