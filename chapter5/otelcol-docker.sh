OTELCOL_VER=${OTELCOL_VER:-"0.95.0"}
echo $OTELCOL_VER

#docker run -p 127.0.0.1:4317:4317 \
#  otel/opentelemetry-collector-contrib:${OTELCOL_VER} 

docker run -p 127.0.0.1:4317:4317 \
  -v $(pwd)/otelcol-config.yaml:/etc/otelcol-contrib/config.yaml \
  otel/opentelemetry-collector-contrib:${OTELCOL_VER}

