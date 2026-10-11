FROM python:3.12.15-slim-bookworm
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home oddcurrent
COPY --chown=10001:10001 server server
COPY --chown=10001:10001 profiles profiles
COPY --chown=10001:10001 web web
RUN mkdir /data && chown oddcurrent:oddcurrent /data
USER 10001:10001
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/healthz', timeout=2)"
CMD ["python","-m","server","--config","/run/secrets/runtime.json"]
