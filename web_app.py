#!/usr/bin/env python3
import os
from typing import List

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse


def load_dotenv_if_present(dotenv_path: str = ".env"):
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def create_s3_client():
    load_dotenv_if_present()
    region = os.getenv("AWS_REGION", "us-east-1")
    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    return boto3.client("s3", region_name=region, endpoint_url=endpoint_url)


app = FastAPI(title="S3 Web UI")


def list_bucket_objects(bucket: str, prefix: str) -> List[dict]:
    client = create_s3_client()
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return response.get("Contents", [])


@app.get("/", response_class=HTMLResponse)
def index(request: Request, bucket: str = "", prefix: str = "", message: str = ""):
    objects = []
    error = ""
    if bucket:
        try:
            objects = list_bucket_objects(bucket, prefix)
        except ClientError as exc:
            error = str(exc)

    rows = "".join(
        f"""
        <tr>
          <td>{obj["Key"]}</td>
          <td>{obj["Size"]}</td>
          <td>
            <form method="get" action="/download" style="margin:0;">
              <input type="hidden" name="bucket" value="{bucket}" />
              <input type="hidden" name="key" value="{obj["Key"]}" />
              <button type="submit">Скачать</button>
            </form>
          </td>
        </tr>
        """
        for obj in objects
    )
    table = (
        f"""
        <table>
          <thead><tr><th>Key</th><th>Size</th><th>Action</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        """
        if objects
        else "<p>Объектов не найдено.</p>"
    )

    html = f"""
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>S3 Web UI</title>
      <style>
        body {{ font-family: sans-serif; max-width: 900px; margin: 32px auto; padding: 0 16px; }}
        .card {{ border: 1px solid #ddd; border-radius: 10px; padding: 16px; margin-bottom: 16px; }}
        label {{ display: block; font-size: 14px; margin-bottom: 4px; }}
        input {{ width: 100%; padding: 8px; margin-bottom: 10px; box-sizing: border-box; }}
        button {{ padding: 8px 12px; cursor: pointer; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border-bottom: 1px solid #eee; text-align: left; padding: 8px; }}
        .ok {{ color: #0a7d2c; }}
        .err {{ color: #b00020; white-space: pre-wrap; }}
      </style>
    </head>
    <body>
      <h1>S3 Web UI</h1>
      <p>Простой интерфейс для загрузки, просмотра и скачивания файлов из S3.</p>

      <div class="card">
        <h2>Загрузка файла</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
          <label>Bucket</label>
          <input name="bucket" value="{bucket}" required />
          <label>Object key (например: docs/file.txt)</label>
          <input name="key" required />
          <label>Файл</label>
          <input type="file" name="file" required />
          <button type="submit">Загрузить</button>
        </form>
      </div>

      <div class="card">
        <h2>Список объектов</h2>
        <form method="get" action="/">
          <label>Bucket</label>
          <input name="bucket" value="{bucket}" required />
          <label>Prefix (необязательно)</label>
          <input name="prefix" value="{prefix}" />
          <button type="submit">Показать</button>
        </form>
        {f'<p class="ok">{message}</p>' if message else ''}
        {f'<p class="err">{error}</p>' if error else ''}
        {table}
      </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.post("/upload")
async def upload_file(
    bucket: str = Form(...),
    key: str = Form(...),
    file: UploadFile = File(...),
):
    client = create_s3_client()
    try:
        client.upload_fileobj(file.file, bucket, key)
    except ClientError as exc:
        message = f"Ошибка загрузки: {exc}"
    else:
        message = f"Загружено: {key}"

    url = f"/?bucket={bucket}&message={message}"
    return RedirectResponse(url=url, status_code=303)


@app.get("/download")
def download(bucket: str, key: str):
    client = create_s3_client()

    try:
        s3_obj = client.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        return HTMLResponse(f"<h1>Ошибка скачивания</h1><pre>{exc}</pre>", status_code=400)

    filename = key.split("/")[-1] or "file.bin"
    return StreamingResponse(
        s3_obj["Body"].iter_chunks(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
