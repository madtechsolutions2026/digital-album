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
        self.username = (username or "photographer").encode("utf-8")
        self.password = (password or "").encode("utf-8")

    def _expected_cookie(self) -> bytes:
        return hmac.new(
            self.password,
            b"dg-studio:" + self.username,
            hashlib.sha256,
        ).hexdigest().encode("ascii")

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

        if path == "/admin/logout":
            response = RedirectResponse("/", status_code=303)
            response.delete_cookie(self.COOKIE_NAME, path="/", secure=scope.get("scheme") == "https")
            return await response(scope, receive, send)

        if path == "/admin/login":
            if not self.password:
                return await HTMLResponse(
                    "Studio access is not configured. Set ADMIN_PASSWORD in the service environment.",
                    status_code=503,
                    headers={"Cache-Control": "no-store"},
                )(scope, receive, send)

            error = ""
            cookie_valid = hmac.compare_digest(
                cookies.get(self.COOKIE_NAME.encode(), b""), self._expected_cookie()
            )
            if scope.get("method") == "GET" and cookie_valid:
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
                supplied_user = form.get("username", [""])[0].encode("utf-8")
                supplied_password = form.get("password", [""])[0].encode("utf-8")
                if (hmac.compare_digest(supplied_user, self.username)
                        and hmac.compare_digest(supplied_password, self.password)):
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

            html = """<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>DG Album Studio</title><style>*{box-sizing:border-box}body{margin:0;min-height:100svh;display:grid;place-items:center;background:#f4f0eb;color:#352820;font:16px/1.6 system-ui;padding:24px}main{width:min(100%,440px);padding:36px;background:#fff;border:1px solid #e9dfd4;border-radius:20px}small{letter-spacing:2px;color:#aa7953}h1{font:38px/1.15 Georgia;margin:20px 0}p{color:#786d64;font-size:14px}label{display:block;margin-top:20px;font-size:14px}input{display:block;width:100%;padding:14px;font:16px system-ui;border:1px solid #cdbbad;border-radius:8px;margin-top:7px}button{width:100%;padding:16px;border:0;border-radius:8px;background:#704c36;color:#fff;font:16px system-ui;margin-top:25px;cursor:pointer}.error{color:#a32b2b}footer{margin-top:25px;font-size:12px;color:#8b8078}</style></head><body><main><small>SHOOT AT SIGHT / PHOTOGRAPHER STUDIO</small><h1>Your album.<br>Beautifully delivered.</h1><p>Sign in to manage wedding events, upload photographs, and prepare private galleries for your clients.</p><form method="post" action="/admin/login"><label>Studio username<input name="username" required autocomplete="username"></label><label>Studio password<input name="password" type="password" required autocomplete="current-password"></label><p class="error">ERROR_TEXT</p><button type="submit">Sign in to your studio</button></form><footer>DG Album · Photographer workspace</footer></main></body></html>"""
            return await HTMLResponse(
                html.replace("ERROR_TEXT", error),
                headers={"Cache-Control": "no-store"},
            )(scope, receive, send)

        if self._requires_studio(path):
            expected = self._expected_cookie()
            valid_cookie = hmac.compare_digest(cookies.get(self.COOKIE_NAME.encode(), b""), expected)
            if not self.password or not valid_cookie:
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
