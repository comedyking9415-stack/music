from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import urllib.request
import json


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            params = parse_qs(urlparse(self.path).query)

            playlist_id = params.get("id", [""])[0]
            limit = int(params.get("limit", ["100"])[0])

            if not playlist_id:
                self.send_json({
                    "success": False,
                    "error": "id is required"
                }, 400)
                return

            limit = max(1, min(limit, 500))

            api_url = (
                "https://saavn.dev/api/playlists/"
                f"{quote(playlist_id)}"
            )

            request = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urllib.request.urlopen(
                request,
                timeout=20
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )

            playlist = data.get("data", {})

            raw = playlist.get("songs", [])

            songs = []

            for item in raw[:limit]:

                artists = []

                primary = item.get(
                    "artists",
                    {}
                ).get("primary", [])

                for artist in primary:
                    if artist.get("name"):
                        artists.append(
                            artist["name"]
                        )

                images = item.get("image", [])

                thumbnail = (
                    images[-1].get("url")
                    if images
                    else None
                )

                songs.append({
                    "id": item.get("id"),
                    "title": item.get("name"),
                    "artists": artists,
                    "album": item.get(
                        "album",
                        {}
                    ).get("name"),
                    "duration": item.get(
                        "duration"
                    ),
                    "duration_seconds": (
                        int(item.get("duration"))
                        if str(
                            item.get(
                                "duration",
                                ""
                            )
                        ).isdigit()
                        else None
                    ),
                    "thumbnail": thumbnail,
                    "url": item.get("url")
                })

            self.send_json({
                "success": True,
                "source": "jiosaavn",
                "type": "playlist",
                "playlist_id": playlist_id,
                "title": playlist.get("name"),
                "description": playlist.get(
                    "description"
                ),
                "total": len(songs),
                "items": songs
            })

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
        self.end_headers()

        self.wfile.write(body)
