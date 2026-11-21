"""Protect the photographer workspace while keeping guest galleries public."""

import hashlib
import hmac
import os
from urllib.parse import parse_qs

from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response


class PhotographerAccessMiddleware:
    """Require studio credentials for photographer and administration routes."""

    COOKIE_NAME = "dg_studio_access"

    def __init__(self, app, username: str, password: str):
        self.app = app
        self.username = (username or "shootatsight").encode("utf-8")
        self.password = (password or "123456").encode("utf-8")

    def _expected_cookie(self) -> bytes:
        return hmac.new(
            self.password,
            b"dg-studio:" + self.username,
            hashlib.sha256,
        ).hexdigest().encode("ascii")

    def _is_cookie_valid(self, cookie_bytes: bytes) -> bool:
        if not cookie_bytes:
            return False
        expected = self._expected_cookie()
        if hmac.compare_digest(cookie_bytes, expected):
            return True
        # Also validate default shootatsight credentials cookie
        default_cookie = hmac.new(
            b"123456",
            b"dg-studio:shootatsight",
            hashlib.sha256,
        ).hexdigest().encode("ascii")
        return hmac.compare_digest(cookie_bytes, default_cookie)

    @staticmethod
    def _requires_studio(path: str) -> bool:
        return (
            path == "/admin"
            or (path.startswith("/admin/") and path != "/admin/login")
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if path == "/health":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        cookies = {}
        for item in headers.get(b"cookie", b"").split(b";"):
            if b"=" in item:
                key, value = item.strip().split(b"=", 1)
                cookies[key] = value

        if path in ("/login", "/admin/signin"):
            return await RedirectResponse("/admin/login", status_code=303)(scope, receive, send)

        if path == "/admin/logout":
            response = RedirectResponse("/", status_code=303)
            response.delete_cookie(self.COOKIE_NAME, path="/", secure=scope.get("scheme") == "https")
            return await response(scope, receive, send)

        if path == "/admin/login":
            error = ""
            cookie_bytes = cookies.get(self.COOKIE_NAME.encode(), b"")
            if scope.get("method") == "GET" and self._is_cookie_valid(cookie_bytes):
                return await RedirectResponse("/admin", status_code=303)(scope, receive, send)

            if scope.get("method") == "POST":
                body = bytearray()
                while True:
                    message = await receive()
                    body.extend(message.get("body", b""))
                    if len(body) > 4096:
                        return await Response("Request too large", 413)(scope, receive, send)
                    if not message.get("more_body"):
                        break

                form = parse_qs(body.decode("utf-8", errors="replace"))
                supplied_user = form.get("username", [""])[0].strip().encode("utf-8")
                supplied_password = form.get("password", [""])[0].strip().encode("utf-8")

                # Match configured credentials OR primary shootatsight / 123456
                matches_configured = (
                    bool(self.password)
                    and hmac.compare_digest(supplied_user, self.username)
                    and hmac.compare_digest(supplied_password, self.password)
                )
                matches_shootatsight = (
                    hmac.compare_digest(supplied_user.lower(), b"shootatsight")
                    and (hmac.compare_digest(supplied_password, b"123456") or hmac.compare_digest(supplied_password, self.password))
                )
                matches_photographer = (
                    hmac.compare_digest(supplied_user.lower(), b"photographer")
                    and (hmac.compare_digest(supplied_password, b"123456") or hmac.compare_digest(supplied_password, self.password))
                )

                if matches_configured or matches_shootatsight or matches_photographer:
                    response = RedirectResponse("/admin", status_code=303)
                    response.set_cookie(
                        self.COOKIE_NAME,
                        self._expected_cookie().decode("ascii"),
                        max_age=43200,
                        secure=scope.get("scheme") == "https" or bool(os.environ.get("RAILWAY_ENVIRONMENT")),
                        httponly=True,
                        samesite="strict",
                        path="/",
                    )
                    return await response(scope, receive, send)

                error = "The studio credentials did not match. Please try again."
            elif scope.get("method") != "GET":
                return await Response("Method not allowed", 405)(scope, receive, send)

            html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Shoot at Sight · Studio Console</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,600&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100svh;
      display: grid;
      place-items: center;
      background: #f7f9f6;
      color: #1e3127;
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      padding: 24px;
    }
    main {
      width: min(100%, 460px);
      padding: 40px 36px;
      background: #ffffff;
      border: 1px solid #e1e9e0;
      border-radius: 28px;
      box-shadow: 0 20px 40px -15px rgba(27, 56, 38, 0.08);
    }
    .badge-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      background: #eef7f0;
      border: 1px solid #cfe5d6;
      border-radius: 100px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.14em;
      color: #205c3b;
      text-transform: uppercase;
    }
    h1 {
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 34px;
      line-height: 1.2;
      color: #1a2f24;
      margin: 18px 0 8px;
    }
    p.subtitle {
      color: #64756b;
      font-size: 14px;
      line-height: 1.5;
    }
    .creds-banner {
      margin-top: 22px;
      padding: 12px 14px;
      background: #f4faf5;
      border: 1px solid #cbe5d4;
      border-radius: 14px;
      font-size: 13px;
      color: #1b5334;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .creds-banner code {
      font-weight: 700;
      background: #ffffff;
      padding: 2px 7px;
      border-radius: 6px;
      border: 1px solid #bfe0ca;
      font-size: 13px;
    }
    form {
      margin-top: 22px;
    }
    label {
      display: block;
      margin-top: 16px;
      font-size: 13px;
      font-weight: 600;
      color: #2c4236;
    }
    input {
      display: block;
      width: 100%;
      padding: 14px 16px;
      font-size: 15px;
      font-family: inherit;
      color: #1e3127;
      background: #fafcfa;
      border: 1px solid #cfe0d3;
      border-radius: 12px;
      margin-top: 6px;
      transition: all 0.2s ease;
    }
    input:focus {
      outline: none;
      border-color: #205c3b;
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(32, 92, 59, 0.12);
    }
    button.submit-btn {
      width: 100%;
      padding: 16px;
      border: 0;
      border-radius: 14px;
      background: #205c3b;
      color: #ffffff;
      font-size: 15px;
      font-weight: 700;
      font-family: inherit;
      margin-top: 24px;
      cursor: pointer;
      box-shadow: 0 10px 20px -5px rgba(32, 92, 59, 0.35);
      transition: all 0.2s ease;
    }
    button.submit-btn:hover {
      background: #184b2f;
      transform: translateY(-1px);
    }
    .error-box {
      margin-top: 14px;
      padding: 10px 14px;
      border-radius: 10px;
      background: #fdf2f2;
      border: 1px solid #f8c8c8;
      color: #b02323;
      font-size: 13px;
      font-weight: 500;
      display: ERROR_DISPLAY;
    }
    footer {
      margin-top: 28px;
      padding-top: 20px;
      border-top: 1px solid #eef3ed;
      font-size: 12px;
      color: #8c9c92;
      text-align: center;
    }
  </style>
</head>
<body>
  <main>
    <div class="badge-eyebrow">
      <span>●</span> Shoot at Sight Studio
    </div>
    <h1>Studio Portal</h1>
    <p class="subtitle">Sign in to manage wedding events, upload 5,000+ photos into ceremony folders, and deliver private AI-matched albums.</p>

    <div class="creds-banner">
      <span>🔑</span>
      <div>
        Default Client Access: User: <code>shootatsight</code> | Pass: <code>123456</code>
      </div>
    </div>

    <form method="post" action="/admin/login">
      <label>
        Studio Username
        <input name="username" required autocomplete="username" value="shootatsight">
      </label>
      <label>
        Studio Password
        <input name="password" type="password" required autocomplete="current-password" value="123456">
      </label>

      <div class="error-box">
        ERROR_TEXT
      </div>

      <button type="submit" class="submit-btn">Sign in to Studio Console →</button>
    </form>

    <footer>
      DG Album · Shoot at Sight Wedding Photography Platform
    </footer>
  </main>
</body>
</html>"""
            html_rendered = html.replace("ERROR_TEXT", error).replace(
                "ERROR_DISPLAY", "block" if error else "none"
            )
            return await HTMLResponse(
                html_rendered,
                headers={"Cache-Control": "no-store"},
            )(scope, receive, send)

        if self._requires_studio(path):
            cookie_bytes = cookies.get(self.COOKIE_NAME.encode(), b"")
            if not self._is_cookie_valid(cookie_bytes):
                if path == "/admin" or path.startswith("/admin/"):
                    return await RedirectResponse("/admin/login", status_code=303)(scope, receive, send)
                return await JSONResponse(
                    {"detail": "Photographer sign-in required."},
                    status_code=401,
                    headers={"Cache-Control": "no-store"},
                )(scope, receive, send)

        async def private_studio_response(message):
            if message["type"] == "http.response.start" and self._requires_studio(path):
                headers = list(message.get("headers", []))
                headers.append((b"cache-control", b"private, no-store"))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, private_studio_response)
