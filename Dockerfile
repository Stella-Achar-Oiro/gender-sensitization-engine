FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Patch gradio oauth.py: HfFolder was removed in huggingface-hub>=0.20 but gradio 4.44.x still imports it
RUN python3 - <<'EOF'
import re, pathlib
p = pathlib.Path("/usr/local/lib/python3.11/site-packages/gradio/oauth.py")
src = p.read_text()
src = src.replace(
    "from huggingface_hub import HfFolder, whoami",
    "from huggingface_hub import whoami\n"
    "class HfFolder:\n"
    "    get_token = staticmethod(lambda: __import__('os').environ.get('HF_TOKEN'))\n"
    "    save_token = staticmethod(lambda t: None)\n"
    "    delete_token = staticmethod(lambda: None)"
)
p.write_text(src)
print("Patched gradio/oauth.py OK")
EOF

COPY gradio_app.py config.py ./
COPY eval/ ./eval/
COPY api/ ./api/
COPY rules/ ./rules/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GRADIO_ANALYTICS_ENABLED=False

EXPOSE 7860

CMD ["python", "gradio_app.py"]
