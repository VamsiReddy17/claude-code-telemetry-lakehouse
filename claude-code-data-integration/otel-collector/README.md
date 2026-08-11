# OTel collector notes

## Local

`docker compose up -d` mounts `config.local.yaml` → writes JSONL under
`otel-collector/local-file-fallback/`.

## Production (ADLS Gen2)

1. Mount `config.yaml` instead of `config.local.yaml` in compose/K8s.
2. Confirm your `otel/opentelemetry-collector-contrib` version supports the
   `azureblob` exporter options you use (`connection_string`, encodings).
   Schemas change between releases — validate with:

   ```bash
   docker run --rm -v $PWD/otel-collector/config.yaml:/config.yaml \
     otel/opentelemetry-collector-contrib:0.120.0 validate --config=/config.yaml
   ```

3. Prefer managed identity over connection strings.
4. If `azureblob` exporter options differ in your version, fall back to:
   - `file` exporter on a PVC, then `azcopy sync` to ADLS, or
   - Kafka / Event Hub exporter → Azure Function → ADLS.

## Claude Code client

Point managed settings `OTEL_EXPORTER_OTLP_ENDPOINT` at the collector
(internal LB / private DNS). Enable content flags as in
`managed-settings/settings.json`.
