# pp-image-downloader

## 概要

`pp-image-downloader`は、パレットプラザ（Palette Plaza）のスマートフォン写真転送サービスのウェブサイトから、画像をまとめてダウンロードするためのコマンドラインツールです。

`pp`は **P**alette **P**laza を指します。

## 機能

- 指定されたURLとアクセスコードを使用してサイトにログインします。
- サイト上にあるすべてのJPEG画像を検索し、ダウンロードします。
- 日付に基づいたフォルダ（例: `20250718`）を自動で作成し、その中に画像を保存します。
- オプションで、ダウンロードした画像にExif形式の撮影日時情報を付与できます。
  - これはGoogle フォトなどで撮影順に写真を並べるための機能です。

## CLIの使い方

### 基本的な使い方

```
pp-image-downloader <URL> <アクセスコード>
```

### 保存先ディレクトリを指定する

`-d` または `--directory` オプションで、画像を保存する親ディレクトリを指定できます。

```
pp-image-downloader <URL> <アクセスコード> -d /path/to/my_pictures
```

### Exif撮影日時を付与する

`--exif` オプションを付けると、ダウンロードした画像に撮影日時が記録されます。日時は、ファイル名順に1秒ずつ加算されて設定されます。

```
pp-image-downloader <URL> <アクセスコード> --exif
```

## 開発者向けセットアップ

1.  **リポジトリをクローンします**

    ```
    git clone https://github.com/your-username/pp-image-downloader.git
    cd pp-image-downloader
    ```

2.  **Poetryをインストールします**

    Poetryがインストールされていない場合は、[公式ドキュメント](https://python-poetry.org/docs/#installation)に従ってインストールしてください。

3.  **ローカル仮想環境の設定**

    Poetryがプロジェクト内に仮想環境を作成するように設定します。

    ```
    poetry config virtualenvs.in-project true
    ```

4.  **依存関係をインストールします**

    ```
    poetry install
    ```

5.  **テストを実行します**

    ```
    poetry run pytest
    ```
```
