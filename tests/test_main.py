import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime
from pp_image_downloader import main as cli_main

# --- create_download_directoryのテスト ---
def test_create_download_directory_new(tmp_path):
    """新しいディレクトリが正しく作成されるかテストする"""
    today_str = datetime.now().strftime("%Y%m%d")
    expected_dir = tmp_path / today_str
    
    result_path = cli_main.create_download_directory(str(tmp_path))
    
    assert result_path == expected_dir
    assert expected_dir.is_dir()

def test_create_download_directory_existing(tmp_path):
    """同名のディレクトリが既に存在する場合、連番が付与されるかテストする"""
    today_str = datetime.now().strftime("%Y%m%d")
    (tmp_path / today_str).mkdir()
    
    expected_dir = tmp_path / f"{today_str}_1"
    result_path = cli_main.create_download_directory(str(tmp_path))
    
    assert result_path == expected_dir
    assert expected_dir.is_dir()

# --- add_exif_datetimeのテスト ---
@patch('pp_image_downloader.main.piexif.load')
@patch('pp_image_downloader.main.piexif.dump')
@patch('pp_image_downloader.main.piexif.insert')
def test_add_exif_datetime(mock_insert, mock_dump, mock_load, tmp_path):
    """Exif情報が正しく付与されるかテストする"""
    # テスト用のダミーファイルを作成
    file1 = tmp_path / "001.jpg"
    file2 = tmp_path / "002.jpg"
    file1.touch()
    file2.touch()
    
    image_paths = [file1, file2]

    # piexif.loadが空のExif辞書を返すように設定
    mock_load.return_value = {"Exif": {}}
    mock_dump.return_value = b'exif_bytes'

    cli_main.add_exif_datetime(image_paths)

    # piexif.insertが正しい引数で呼び出されたか検証
    assert mock_insert.call_count == 2
    
    # 1回目の呼び出し検証
    args1, _ = mock_insert.call_args_list[0]
    assert args1[0] == b'exif_bytes'
    assert args1[1] == str(file1)

    # 2回目の呼び出し検証
    args2, _ = mock_insert.call_args_list[1]
    assert args2[0] == b'exif_bytes'
    assert args2[1] == str(file2)
