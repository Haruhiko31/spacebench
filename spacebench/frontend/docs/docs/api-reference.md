# API Reference

The SpaceBench backend exposes a REST API built with [FastAPI](https://fastapi.tiangolo.com/).
Interactive documentation is automatically generated and available at the following endpoints once the backend is running.

---

## Interactive docs

### Swagger UI

Full interactive interface — try any endpoint directly from the browser, inspect request/response schemas, and view parameter descriptions.

[http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### ReDoc

Clean, read-only reference documentation. Better suited for reading than for testing.

[http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

!!! note "Offline ReDoc"
    ReDoc is served from a local static file (`redoc.standalone.js`) — it works without an internet connection.
