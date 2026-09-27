from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import urllib.request
import json


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            params = parse_qs(urlparse(self.path).query)

            query = params.get("q", [""])[0]
            limit = int(params.get("limit", ["20"])[0])

            if not query.strip():
                self.send_json({
                    "success": False,
                    "error": "q is required"
                }, 400)
                return

            # Safe limit
            limit = max(1, min(limit, 100))

            api_url = (
                "https://saavn.dev/api/search/songs"
                f"?query={quote(query)}"
                f"&page=1"
                f"&limit={limit}"
            )

            request = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=15
            ) as response:

                raw_data = response.read().decode("utf-8")
                data = json.loads(raw_data)

            results = (
                data.get("data", {})
                .get("results", [])
            )

            songs = []

            for item in results:

                # Artists
                artists = []

                primary_artists = (
                    item.get("artists", {})
                    .get("primary", [])
                )

                for artist in primary_artists:
                    name = artist.get("name")

                    if name:
                        artists.append(name)

                # Thumbnail
                images = item.get("image", [])

                thumbnail = None

                if images:
                    thumbnail = images[-1].get("url")

                # Duration
                duration_raw = item.get("duration")

                try:
                    duration_seconds = int(
                        duration_raw
                    )
                except (TypeError, ValueError):
                    duration_seconds = None

                songs.append({
                    "id": item.get("id"),
                    "title": item.get("name"),
                    "artists": artists,
                    "album": (
                        item.get("album", {})
                        .get("name")
                    ),
                    "duration": duration_raw,
                    "duration_seconds": duration_seconds,
                    "thumbnail": thumbnail,
                    "url": item.get("url")
                })

            self.send_json({
                "success": True,
                "source": "jiosaavn",
                "type": "search",
                "query": query,
                "total": len(songs),
                "items": songs
            })

        except ValueError:
            self.send_json({
                "success": False,
                "error": "limit must be a number"
            }, 400)

        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            }, 500)

    def send_json(self, data, status=200):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.end_headers()

        self.wfile.write(body)
