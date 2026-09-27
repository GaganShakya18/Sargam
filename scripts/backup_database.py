from datetime import datetime
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
backup_dir = root / 'database' / 'backups'
backup_dir.mkdir(exist_ok=True)

source_file = root / 'database' / 'schema.sql'
backup_path = backup_dir / f"schema_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
shutil.copy2(source_file, backup_path)

print(f"Backup created: {backup_path}")
