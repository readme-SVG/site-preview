import json
import os
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request, send_file
from .card import generate_svg

app = Flask(__name__)

def fetch_website_info(url: str) -> dict:
    try:
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        title = ""
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']
        else:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text

        image_url = ""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image['content']
            if image_url.startswith('/'):
                parsed_uri = urlparse(url)
                base = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
                image_url = urljoin(base, image_url)

        return {
            "title": title.strip()[:100] if title else "Website Link",
            "image_url": image_url,
            "url": url
        }
    except Exception as e:
        return {
            "title": "Error fetching info",
            "image_url": "",
            "url": url
        }

@app.route("/")
def index():
    html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    return send_file(os.path.abspath(html_path))

@app.route("/styles.css")
def styles():
    css_path = os.path.join(os.path.dirname(__file__), "..", "styles.css")
    return send_file(os.path.abspath(css_path), mimetype="text/css")

@app.route("/app.js")
def script():
    js_path = os.path.join(os.path.dirname(__file__), "..", "app.js")
    return send_file(os.path.abspath(js_path), mimetype="application/javascript")

@app.route("/badge")
def badge():
    url_param = request.args.get("url")
    if not url_param:
        return Response("Missing 'url' parameter", status=400)

    width = min(max(int(request.args.get("width", 320)), 200), 600)
    radius = min(max(int(request.args.get("radius", 10)), 0), 30)
    bg = "#" + request.args.get("bg", "0f1117").lstrip("#")
    title_color = "#" + request.args.get("title_color", "ffffff").lstrip("#")
    title_opacity = min(max(float(request.args.get("title_opacity", 1)), 0), 1)
    plate_color = "#" + request.args.get("plate_color", "0f1117").lstrip("#")
    plate_opacity = min(max(float(request.args.get("plate_opacity", 0.78)), 0), 1)
    title_position = request.args.get("title_position", "overlay_bottom").lower()
    
    title_position_aliases = {
        "top": "overlay_top", "bottom": "overlay_bottom",
        "overlay_top": "overlay_top", "overlay_bottom": "overlay_bottom",
        "outside_top": "outside_top", "outside_bottom": "outside_bottom",
    }
    title_position = title_position_aliases.get(title_position, "overlay_bottom")
    border_width = min(max(int(request.args.get("border_width", 1)), 0), 10)
    border_color = "#" + request.args.get("border_color", "ffffff").lstrip("#")
    embed = request.args.get("embed", "true").lower() != "false"

    info = fetch_website_info(url_param)

    svg = generate_svg(
        title=info["title"],
        image_url=info["image_url"],
        width=width,
        background_color=bg,
        title_color=title_color,
        title_opacity=title_opacity,
        title_plate_opacity=plate_opacity,
        title_plate_color=plate_color,
        title_position=title_position,
        border_radius=radius,
        border_width=border_width,
        border_color=border_color,
        embed_thumbnail=embed,
    )

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )

@app.route("/info")
def info():
    url_param = request.args.get("url")
    if not url_param:
        return Response("Missing 'url' parameter", status=400)

    info_data = fetch_website_info(url_param)
    return Response(
        json.dumps(info_data),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
