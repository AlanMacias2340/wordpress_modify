from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import pathlib
import requests

app = FastAPI()

# mount static files directory so index.html and login.html can be served
app.mount("/static", StaticFiles(directory=pathlib.Path(__file__).parent), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    html_path = pathlib.Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())

@app.get("/login", response_class=HTMLResponse)
async def login_form():
    html_path = pathlib.Path(__file__).parent / "login.html"
    return HTMLResponse(html_path.read_text())

@app.post("/login")
async def login(
    wp_url: str = Form(...),
    consumer_key: str | None = Form(None),
    consumer_secret: str | None = Form(None)
):
    # base result
    result = {"status": "ok", "url": wp_url}
    # optionally try a simple GET to verify the site responds
    try:
        r = requests.get(wp_url, timeout=10)
        result["site_status"] = r.status_code
    except Exception as e:
        result["site_error"] = str(e)

    # if WooCommerce credentials provided, configure client
    if consumer_key and consumer_secret:
        try:
            from woocommerce import API as WCAPI
            wcapi = WCAPI(
                url=wp_url.rstrip("/"),
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3",
            )
            # Example call to list products to verify connection
            wc_resp = wcapi.get("products")
            result["woocommerce"] = {
                "status_code": wc_resp.status_code,
                "body": wc_resp.json() if wc_resp.ok else wc_resp.text,
            }
        except Exception as e:
            result["woocommerce_error"] = str(e)

    return result
