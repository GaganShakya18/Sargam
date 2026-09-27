from pathlib import Path


root = Path(__file__).resolve().parent.parent
music_dir = root / 'storage' / 'music'

for file in music_dir.rglob('*'):
    if file.is_file():
        print(file.relative_to(root))
