#!/usr/bin/env python3
import json
import os
import re
import smtplib
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CONFIG_PATH = os.path.expanduser("~/newsletter/config.json")
CALENDAR_PATH = os.path.expanduser("~/Vault/newsletter-calendar.md")


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OpenClawNewsletter/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def fetch_text(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 OpenClawNewsletter/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse_cnn_articles(rss_url, limit=3):
    xml = fetch_text(rss_url)
    root = ET.fromstring(xml)
    items = root.findall(".//item")[:limit]
    out = []
    for it in items:
        title = (it.findtext("title") or "Untitled").strip()
        link = (it.findtext("link") or "").strip()
        desc = re.sub(r"<[^>]+>", "", (it.findtext("description") or "")).strip()
        desc = re.sub(r"\s+", " ", desc)
        if len(desc) > 220:
            desc = desc[:217] + "..."
        image = None
        media = it.find('{http://search.yahoo.com/mrss/}content')
        if media is not None:
            image = media.attrib.get('url')
        if not image and link:
            try:
                html = fetch_text(link, timeout=10)
                m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
                if m:
                    image = m.group(1)
            except Exception:
                pass
        out.append({"title": title, "link": link, "desc": desc, "image": image})
    return out


def weather_milwaukee():
    # Milwaukee approx
    lat, lon = 43.0389, -87.9065
    url = (
        "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&current=temperature_2m,weather_code&timezone=America%%2FChicago"
    ) % (lat, lon)
    data = fetch_json(url)
    cur = data.get("current", {})
    daily = data.get("daily", {})
    return {
        "current_temp": cur.get("temperature_2m"),
        "max": (daily.get("temperature_2m_max") or [None])[0],
        "min": (daily.get("temperature_2m_min") or [None])[0],
        "precip": (daily.get("precipitation_probability_max") or [None])[0],
    }


def daily_quote():
    # fallback chain
    for url, parser in [
        ("https://zenquotes.io/api/today", lambda j: f"{j[0]['q']} — {j[0]['a']}"),
        ("https://api.quotable.io/random", lambda j: f"{j['content']} — {j['author']}"),
    ]:
        try:
            j = fetch_json(url)
            return parser(j)
        except Exception:
            continue
    return "Keep going. Small steps still move you forward."


def parse_calendar(path):
    today = datetime.now().strftime("%Y-%m-%d")
    events = []
    if not os.path.exists(path):
        return events
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Format: YYYY-MM-DD HH:MM - Event name
            if line.startswith(today):
                events.append(line[len(today):].strip(" -"))
    return events


def build_html(articles, weather, reminders, quote, date_str):
    cards = []
    for a in articles:
        img_html = f'<img src="{a["image"]}" alt="article image" style="width:100%;max-width:560px;border-radius:10px;display:block;margin-bottom:8px;"/>' if a.get("image") else ""
        cards.append(
            f"""
            <div style=\"background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;padding:14px;margin:14px 0;\">
              {img_html}
              <h3 style=\"margin:0 0 8px 0;font-family:Arial,sans-serif;\">{a['title']}</h3>
              <p style=\"margin:0 0 8px 0;color:#374151;font-family:Arial,sans-serif;\">{a['desc']}</p>
              <a href=\"{a['link']}\" style=\"font-family:Arial,sans-serif;\">Read full article</a>
            </div>
            """
        )

    reminders_html = "<li>No events found for today.</li>" if not reminders else "".join([f"<li>{r}</li>" for r in reminders])

    return f"""
    <html><body style=\"background:#f3f4f6;padding:18px;\">
      <div style=\"max-width:680px;margin:0 auto;background:#f9fafb;padding:20px;border-radius:14px;\">
        <h1 style=\"font-family:Arial,sans-serif;margin-top:0;\">☀️ Good Morning — Daily Brief</h1>
        <p style=\"font-family:Arial,sans-serif;color:#4b5563;\">{date_str}</p>

        <h2 style=\"font-family:Arial,sans-serif;\">🌤️ Milwaukee Weather</h2>
        <div style=\"background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;\">
          <p style=\"font-family:Arial,sans-serif;margin:0;\">
            Current: <b>{weather['current_temp']}°C</b> · High: <b>{weather['max']}°C</b> · Low: <b>{weather['min']}°C</b> · Precip Chance: <b>{weather['precip']}%</b>
          </p>
        </div>

        <h2 style=\"font-family:Arial,sans-serif;\">📰 Top CNN Stories</h2>
        {''.join(cards)}

        <h2 style=\"font-family:Arial,sans-serif;\">📅 Today's Reminders</h2>
        <div style=\"background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;\">
          <ul style=\"font-family:Arial,sans-serif;\">{reminders_html}</ul>
        </div>

        <h2 style=\"font-family:Arial,sans-serif;\">✨ Quote of the Day</h2>
        <div style=\"background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:12px;\">
          <p style=\"font-family:Georgia,serif;margin:0;\">{quote}</p>
        </div>
      </div>
    </body></html>
    """


def send_email(cfg, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = cfg["subject"]
    msg["From"] = cfg["from_email"]
    msg["To"] = cfg["to_email"]
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(cfg["smtp_user"], cfg["smtp_pass"])
        server.sendmail(cfg["from_email"], [cfg["to_email"]], msg.as_string())


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    articles = parse_cnn_articles(cfg.get("cnn_rss", "http://rss.cnn.com/rss/edition.rss"), cfg.get("article_count", 3))
    weather = weather_milwaukee()
    reminders = parse_calendar(cfg.get("calendar_file", CALENDAR_PATH))
    quote = daily_quote()
    html = build_html(articles, weather, reminders, quote, date_str)
    send_email(cfg, html)
    print("newsletter sent")


if __name__ == "__main__":
    main()
