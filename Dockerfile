FROM python:3.13-slim AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data APP_BASE_URL=https://shifts.quigspace.com
COPY --from=dependencies /install /usr/local
RUN groupadd --gid 10001 crewline && useradd --uid 10001 --gid 10001 --create-home crewline && mkdir /data /app && chown -R crewline:crewline /data /app
WORKDIR /app
COPY --chown=crewline:crewline app/ /app/
COPY --chown=crewline:crewline docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod 755 /app/docker-entrypoint.sh
USER 10001:10001
EXPOSE 3000
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/healthz/', timeout=4)" || exit 1
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runservice", "--port", "3000"]
