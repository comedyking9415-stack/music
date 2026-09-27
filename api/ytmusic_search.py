from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from ytmusicapi import YTMusic

yt = YTMusic()


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            query = parse_qs(urlparse(self.path).query).get("q", [""])[0]
            limit = int(parse_qs(urlparse(self.path).query).get("limit", ["20"])[0])

            if not query:
                self.send_json({
                    "success": False,
                    "error": "q is required"
                }, 400)
                return

            limit = max(1, min(limit, 100))

            results = yt.search(query, filter="songs", limit=limit)

            songs = []

            for item in results:
                artists = [
                    artist.get("name")
                    for artist in item.get("artists", [])
                    if artist.get("name")
                ]

                songs.append({
                    "videoId": item.get("videoId"),
                    "title": item.get("title"),
                    "artists": artists,
                    "album": (
                        item.get("album", {}).get("name")
                        if item.get("album")
                        else None
                    ),
                    "duration": item.get("duration"),
                    "duration_seconds": item.get("duration_seconds"),
                    "thumbnail": (
                        item.get("thumbnails", [])[-1].get("url")
                        if item.get("thumbnails")
                        else None
                    ),
                    "url": (
                        f"https://music.youtube.com/watch?v={item.get('videoId')}"
                        if item.get("videoId")
                        else None
                    )
                })

            self.send_json({
                "success": True,
                "source": "ytmusic",
                "type": "search",
                "query": query,
                "total": len(songs),
                "items": songs
            })

        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            }, 500)

    def send_json(self, data, status=200):
        import json

        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(body)
