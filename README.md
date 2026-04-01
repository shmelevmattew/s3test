# S3 demo (Python)

Минимальный пример работы с S3:
- загрузка файла в бакет
- просмотр списка объектов
- скачивание файла из бакета
- веб-интерфейс (FastAPI)

## 1) Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Настройка доступа

Экспортируйте переменные окружения:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

Опционально для S3-совместимых облаков (например, MinIO/Selectel/другие):

```bash
export S3_ENDPOINT_URL="https://your-s3-endpoint.example.com"
```

## 3) Примеры запуска

Загрузить файл:

```bash
python s3_tool.py upload --bucket my-bucket --file ./local.txt --key docs/local.txt
```

Посмотреть список:

```bash
python s3_tool.py list --bucket my-bucket --prefix docs/
```

Скачать файл:

```bash
python s3_tool.py download --bucket my-bucket --key docs/local.txt --out ./downloads/local.txt
```

## 4) Веб-версия с UI

Запуск:

```bash
uvicorn web_app:app --reload --host 0.0.0.0 --port 8000
```

Открой в браузере:

`http://localhost:8000`

В UI доступны:
- загрузка файла в S3
- просмотр объектов бакета (с prefix)
- скачивание объектов кнопкой "Скачать"
# s3test
