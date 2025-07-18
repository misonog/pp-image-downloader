import argparse
import os
import requests
import piexif
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

# --- Selenium関連のライブラリをインポート ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def setup_parser():
    """コマンドライン引数を設定し、解析する"""
    parser = argparse.ArgumentParser(description="Download images from Palette Plaza.")
    parser.add_argument("url", help="Target site URL")
    parser.add_argument("access_code", help="Access code for the site")
    parser.add_argument("-d", "--directory", default=".", help="Directory to save images (default: current directory)")
    parser.add_argument("--exif", action="store_true", help="Add Exif datetime to images")
    return parser.parse_args()

def create_download_directory(base_dir: str) -> Path:
    """日付に基づいたダウンロードディレクトリを作成する"""
    today_str = datetime.now().strftime("%Y%m%d")
    save_path = Path(base_dir)
    
    dir_path = save_path / today_str
    
    if dir_path.exists():
        counter = 1
        while True:
            new_dir_path = save_path / f"{today_str}_{counter}"
            if not new_dir_path.exists():
                dir_path = new_dir_path
                break
            counter += 1
            
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        return dir_path
    except OSError as e:
        print(f"Error: Failed to create directory {dir_path}. {e}")
        exit(1)

def login_and_get_image_urls(url: str, access_code: str) -> list[str]:
    """[Selenium版] ブラウザを操作してサイトにログインし、画像のURLリストを取得する"""
    print("Initializing browser...")
    image_urls = []
    
    # Chromeのオプション設定 (ヘッドレスモードなど)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # GUIなしで実行したい場合はこの行を有効化
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = None
    try:
        # WebDriverを自動でインストール・セットアップ
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print(f"Navigating to {url}")
        driver.get(url)
        
        # パスワード入力フォームが表示されるまで最大10秒待機
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "passwd"))
        )
        
        print("Entering access code...")
        password_field.send_keys(access_code)
        
        # ログインボタンをクリック (ここでは一般的な'submit'タイプのボタンを検索)
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        login_button.click()
        
        print("Login submitted. Waiting for image links to load...")
        # ログイン後、画像リンクが表示されるまで最大10秒待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.jpg']"))
        )
        
        # ページのHTMLをBeautifulSoupで解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.lower().endswith('.jpg'):
                full_url = urljoin(driver.current_url, href)
                image_urls.append(full_url)
        
        if not image_urls:
            print("Warning: No image links found after login.")
        else:
            print(f"Found {len(image_urls)} images.")
        
    except Exception as e:
        print(f"An error occurred during browser automation: {e}")
        exit(1)
    finally:
        if driver:
            driver.quit() # ブラウザを閉じる
            
    return image_urls

def download_images(image_urls: list[str], save_dir: Path) -> list[Path]:
    """画像のURLリストから画像をダウンロードする"""
    downloaded_files = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    for i, img_url in enumerate(image_urls):
        try:
            filename = os.path.basename(img_url)
            save_path = save_dir / filename
            
            # 画像のダウンロードにはrequestsを使用する
            response = requests.get(img_url, stream=True, headers=headers)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded ({i+1}/{len(image_urls)}): {filename}")
            downloaded_files.append(save_path)
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to download {img_url}. {e}")
            continue
    return downloaded_files

def add_exif_datetime(image_paths: list[Path]):
    """ダウンロードした画像にExif撮影日時を付与する"""
    if not image_paths:
        return
        
    print("Adding Exif datetime...")
    image_paths.sort(key=lambda p: p.name)
    
    start_time = datetime.now() - timedelta(hours=1)
    
    for i, img_path in enumerate(image_paths):
        try:
            current_time = start_time + timedelta(seconds=i)
            time_str = current_time.strftime("%Y:%m:%d %H:%M:%S")
            
            try:
                exif_dict = piexif.load(str(img_path))
            except piexif.InvalidImageDataError:
                exif_dict = {"Exif": {}}
            
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = time_str.encode('utf-8')
            exif_bytes = piexif.dump(exif_dict)
            
            piexif.insert(exif_bytes, str(img_path))
            print(f"  Set datetime for {img_path.name}: {time_str}")
        except Exception as e:
            print(f"Error: Failed to add Exif to {img_path.name}. {e}")

def main():
    """メイン処理"""
    args = setup_parser()
    save_directory = create_download_directory(args.directory)
    
    image_urls = login_and_get_image_urls(args.url, args.access_code)
    
    if image_urls:
        # ログインしてURLを取得した後は、元のrequestsで画像をダウンロード
        import requests 
        downloaded_files = download_images(image_urls, save_directory)
        
        if args.exif and downloaded_files:
            add_exif_datetime(downloaded_files)
            
    print("Download process finished.")

if __name__ == "__main__":
    main()
