FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

RUN addgroup --system django && adduser --system --ingroup django django

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev curl && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

COPY --chown=django:django . /app
WORKDIR /app

USER django

CMD ["gunicorn", "--bind", "0.0.0.0:7000", "--workers", "3", "image_analysis_web.wsgi:application"]