FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get update && apt-get install -y curl python3 && rm -rf /var/lib/apt/lists/*

COPY fardrun /usr/local/bin/fardrun
RUN chmod +x /usr/local/bin/fardrun

WORKDIR /app
COPY src/ src/
COPY vendor/ vendor/
COPY policies/ policies/

RUN mkdir -p out/escs

EXPOSE 7700 7701 7702

HEALTHCHECK --interval=5s --timeout=3s --retries=5 --start-period=10s \
  CMD curl -f http://localhost:7700/health || exit 1

CMD ["fardrun", "run", "--program", "src/services/gatewayd.fard", "--out", "out/escs"]
