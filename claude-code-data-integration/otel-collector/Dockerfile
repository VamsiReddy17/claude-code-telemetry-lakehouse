FROM otel/opentelemetry-collector-contrib:0.120.0

COPY config.yaml /etc/otelcol-contrib/config.yaml

EXPOSE 4317 4318 8888 13133

ENTRYPOINT ["/otelcol-contrib"]
CMD ["--config=/etc/otelcol-contrib/config.yaml"]
