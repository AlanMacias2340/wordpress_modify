from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
import pathlib
import requests

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    html_path = pathlib.Path(__file__).parent.parent / "frontend" / "index.html"
    return HTMLResponse(html_path.read_text())

@router.get("/login", response_class=HTMLResponse)
async def login_form():
    html_path = pathlib.Path(__file__).parent.parent / "frontend" / "login.html"
    return HTMLResponse(html_path.read_text())

@router.post("/login")
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
            wc_resp = wcapi.get("products")
            wc_body = wc_resp.json() if wc_resp.ok else wc_resp.text
            result["woocommerce"] = {
                "status_code": wc_resp.status_code,
                "body": wc_body,
            }
        except Exception as e:
            result["woocommerce_error"] = str(e)

    return result

@router.get("/products_html", response_class=HTMLResponse)
async def products_page():
    # serve the static products.html page
    html_path = pathlib.Path(__file__).parent.parent / "frontend" / "products.html"
    return HTMLResponse(html_path.read_text())

@router.get("/categories")
async def get_categories(
    wp_url: str,
    consumer_key: str | None = None,
    consumer_secret: str | None = None,
):
    response = {"woocommerce": {}}
    if consumer_key and consumer_secret:
        try:
            from woocommerce import API as WCAPI
            wcapi = WCAPI(
                url=wp_url.rstrip("/"),
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3",
            )
            per_page = 100
            page = 1
            all_items = []
            wc_status = None
            while True:
                wc_resp = wcapi.get("products/categories", params={"per_page": per_page, "page": page})
                wc_status = wc_resp.status_code
                wc_body = wc_resp.json() if wc_resp.ok else wc_resp.text
                if not isinstance(wc_body, list):
                    all_items = wc_body
                    break
                all_items.extend(wc_body)
                if len(wc_body) < per_page:
                    break
                page += 1
            response["woocommerce"] = {"status_code": wc_status, "body": all_items}
        except Exception as e:
            response["woocommerce_error"] = str(e)
    else:
        response["error"] = "Missing WooCommerce credentials"
    return response

@router.get("/search", response_class=HTMLResponse)
async def search_page():
    # serve a dedicated product search page
    html_path = pathlib.Path(__file__).parent.parent / "frontend" / "search.html"
    return HTMLResponse(html_path.read_text())

@router.get("/products")
async def get_products(
    wp_url: str,
    consumer_key: str | None = None,
    consumer_secret: str | None = None,
    sku: str | None = None,
    category: str | None = None,
):
    # call WooCommerce API to list products or filter by SKU/category
    response = {"woocommerce": {}}
    if consumer_key and consumer_secret:
        try:
            from woocommerce import API as WCAPI
            wcapi = WCAPI(
                url=wp_url.rstrip("/"),
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version="wc/v3",
            )
            params = {}
            if sku:
                params["sku"] = sku
            if category:
                params["category"] = category
            # WooCommerce defaults to 10 items per page; iterate pages to collect all products
            per_page = 100
            page = 1
            all_items = []
            wc_status = None
            while True:
                p = params.copy()
                p.update({"per_page": per_page, "page": page})
                wc_resp = wcapi.get("products", params=p)
                wc_status = wc_resp.status_code
                wc_body = wc_resp.json() if wc_resp.ok else wc_resp.text
                if not isinstance(wc_body, list):
                    # some error or single object returned; just return as-is
                    all_items = wc_body
                    break
                all_items.extend(wc_body)
                if len(wc_body) < per_page:
                    break
                page += 1
            response["woocommerce"] = {"status_code": wc_status, "body": all_items}
        except Exception as e:
            response["woocommerce_error"] = str(e)
    else:
        response["error"] = "Missing WooCommerce credentials"
    return response
