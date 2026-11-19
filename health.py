"""Container healthcheck for the Musigree application.

Docker runs this until it exits 0. The process must fail while application
startup is still in progress so the container stays unready.
"""

import sys
import urllib.error
import urllib.request

# 127.0.0.1 avoids localhost resolving to IPv6 ::1. Gunicorn listens on IPv4.
HEALTHCHECK_URL = "http://127.0.0.1:5000/health"
# Finish inside Docker's probe timeout so a not-ready response is reported
# here instead of the probe being killed.
HEALTHCHECK_TIMEOUT_SECONDS = 3


def main() -> int:
    """Return 0 when /health reports that application startup has finished.

    Returns:
        0 when the endpoint returns HTTP 200, otherwise 1.
    """
    request = urllib.request.Request(HEALTHCHECK_URL, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=HEALTHCHECK_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                print(f"health status {response.status}", file=sys.stderr)
                return 1
    except urllib.error.HTTPError as error:
        # 503 while health_ok is false. urlopen raises instead of returning.
        print(f"health status {error.code}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"health check failed: {error.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
