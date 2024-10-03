import argparse
from datetime import datetime as Datetime, timezone
from pathlib import Path

import exifread
import pytz
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata


def get_image_creation_date(file_path) -> Datetime | None:
    """Извлекает дату создания изображения из EXIF данных."""
    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
        if raw_date := tags.get("EXIF DateTimeOriginal"):
            date_string = str(raw_date)
            pattern = "%Y:%m:%d %H:%M:%S"

            if raw_tz := tags.get("EXIF OffsetTimeOriginal"):
                date_string += str(raw_tz).replace(":", "")
                pattern += "%z"

            return Datetime.strptime(date_string, pattern).astimezone(pytz.UTC)

    return None

def get_video_creation_date(file_path) -> Datetime | None:
    """Извлекает дату создания видео из метаданных."""
    with createParser(str(file_path)) as parser:
        metadata = extractMetadata(parser)
        if metadata and metadata.has("creation_date"):
            return metadata.get("creation_date")

    return None


def rename_files_based_on_creation_date(dir_: Path, dt_format: str) -> None:
    """Переименовывает файлы в директории на основе их даты создания."""
    for file_path in dir_.iterdir():
        if not file_path.is_file():
            continue

        file_extension = file_path.suffix

        match file_extension.lower():
            case '.jpg' | '.jpeg' | '.png':
                creation_dt = get_image_creation_date(file_path)
            case '.mp4' | '.mov' | '.avi' | '.mkv':
                creation_dt = get_video_creation_date(file_path)
            case _:
                continue

        if not creation_dt:
            continue

        new_file_path = dir_ / (creation_dt.strftime(dt_format) + file_extension)
        if not new_file_path.exists():
            file_path.rename(new_file_path)
            print(f"Файл {file_path.name} переименован в {new_file_path.name}")
        else:
            print(f"Файл с именем {new_file_path.name} уже существует. Пропускаем.")


def main():
    parser = argparse.ArgumentParser(description="Переименовывание изображений и видео на основе даты создания")
    parser.add_argument('dir', type=str, help="Путь к директории с файлами", default=".")
    parser.add_argument('--format', type=str, help="Формат даты", default="%Y%m%d_%H%M%S")

    args = parser.parse_args()

    directory = Path(args.dir)
    if directory.is_dir():
        rename_files_based_on_creation_date(directory, args.format)
    else:
        print(f"Ошибка: Директория {directory} не найдена.")

if __name__ == "__main__":
    main()
