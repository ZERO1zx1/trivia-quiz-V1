"""Security Response Headers

Applies defense-in-depth headers to every response (FIX-015):
- Strict-Transport-Security (HTTPS only)
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
- Content-Security-Policy (relaxed enough for SocketIO; tighten as needed)
"""


def init_security_headers(app):
    """Register an after_request handler that injects security headers."""

    @app.after_request
    def _add_security_headers(response):
        if app.config.get('PREFERRED_URL_SCHEME') == 'https' or not app.debug:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains')
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), interest-cohort=()')
        response.headers['X-XSS-Protection'] = '0'  # modern browsers; CSP below
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com 'unsafe-inline'; "
            "style-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'self'"
        )
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app
