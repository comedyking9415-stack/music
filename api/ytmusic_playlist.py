from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from ytmusicapi import YTMusic


yt = YTMusic()


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

            playlist = yt.get_playlist(
                playlist_id,
                limit=limit
            )

            songs = []

            for item in playlist.get("tracks", []):

                if not item:
                    continue

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
                "type": "playlist",
                "playlist_id": playlist_id,
                "title": playlist.get("title"),
                "description": playlist.get("description"),
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
