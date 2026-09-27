import os
import subprocess


if __name__ == "__main__":
    backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
    subprocess.run(
        [
            'python', '-m', 'uvicorn', 'main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ],
        cwd=backend_dir,
        check=False,
    )
