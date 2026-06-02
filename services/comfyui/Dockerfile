FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# v0.3.27 pins comfyui-frontend-package==1.14.5 (yanked on PyPI) — use newer tag
ARG COMFYUI_REF=v0.3.49
WORKDIR /opt
RUN git clone --depth 1 --branch "${COMFYUI_REF}" https://github.com/comfyanonymous/ComfyUI.git

WORKDIR /opt/ComfyUI
# Patch any yanked exact pins if PyPI removed them (headless API still needs the package)
RUN sed -i 's/comfyui-frontend-package==1.14.5/comfyui-frontend-package==1.14.6/' requirements.txt 2>/dev/null || true

RUN pip install --upgrade pip \
    && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt \
    && pip install requests

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8188

HEALTHCHECK --interval=15s --timeout=10s --start-period=120s --retries=10 \
    CMD curl -sf http://localhost:8188/system_stats || exit 1

ENTRYPOINT ["/entrypoint.sh"]
