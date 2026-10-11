FROM python:3.12.12-slim-bookworm
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home oddcurrent
COPY server server
COPY profiles profiles
COPY web web
RUN mkdir /data && chown oddcurrent:oddcurrent /data
USER 10001:10001
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/healthz', timeout=2)"
CMD ["python","-m","server","--config","/run/secrets/runtime.json"]
