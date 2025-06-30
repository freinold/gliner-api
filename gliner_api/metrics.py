from prometheus_client import Counter, Enum, Histogram, Info, make_asgi_app

from gliner_api.datamodel import InfoResponse

failed_auth_metric: Counter = Counter(
    name="failed_auth",
    documentation="Failed authentication attempts",
)
requests_metric: Counter = Counter(
    name="requests",
    documentation="Requests to the API",
    labelnames=["method", "endpoint"],
)
failed_inference_metric: Counter = Counter(
    name="failed_inference",
    documentation="Failed inference attempts",
    labelnames=["method", "endpoint"],
)
inference_time_metric: Histogram = Histogram(
    name="inference_time",
    documentation="Time taken for inference",
    labelnames=["method", "endpoint"],
    unit="seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)
info_metric: Info = Info(
    name="app_info",
    documentation="Information about the GLiNER API",
)
app_state_metric: Enum = Enum(
    name="app_state",
    documentation="Current state of the application",
    states=["starting", "running", "stopping"],
)

# Observe info by using the InfoResponse model
info_metric.info({k: str(v) for k, v in InfoResponse().model_dump().items()})

metrics_app = make_asgi_app()
