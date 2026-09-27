
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
from ytmusicapi import YTMusic
import urllib.request
import json


yt = YTMusic()


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            params = parse_qs(parsed.query)

            # =========================
            # YOUTUBE MUSIC SEARCH
            # =========================

            if path == "/api/ytmusic/search":

                query = params.get("q", [""])[0]
                limit = self.get_limit(params)

                if not query.strip():
                    return self.send_json({
                        "success": False,
                        "error": "q is required"
                    }, 400)

                results = yt.search(
                    query,
                    filter="songs",
                    limit=limit
                )

                songs = [
                    self.format_yt_song(item)
                    for item in results
                ]

                return self.send_json({
                    "success": True,
                    "source": "ytmusic",
                    "type": "search",
                    "query": query,
                    "total": len(songs),
                    "items": songs
                })

            # =========================
            # YOUTUBE MUSIC PLAYLIST
            # =========================

            if path == "/api/ytmusic/playlist":

                playlist_id = params.get("id", [""])[0]
                limit = self.get_limit(
                    params,
                    default=100,
                    maximum=500
                )

                if not playlist_id:
                    return self.send_json({
                        "success": False,
                        "error": "id is required"
                    }, 400)

                playlist = yt.get_playlist(
                    playlist_id,
                    limit=limit
                )

                songs = []

                for item in playlist.get("tracks", []):
                    if item:
                        songs.append(
                            self.format_yt_song(item)
                        )

                return self.send_json({
                    "success": True,
                    "source": "ytmusic",
                    "type": "playlist",
                    "playlist_id": playlist_id,
                    "title": playlist.get("title"),
                    "description": playlist.get("description"),
                    "total": len(songs),
                    "items": songs
                })

            # =========================
            # JIOSAAVN SEARCH
            # =========================

            if path == "/api/jiosaavn/search":

                query = params.get("q", [""])[0]
                limit = self.get_limit(params)

                if not query.strip():
                    return self.send_json({
                        "success": False,
                        "error": "q is required"
                    }, 400)

                data = self.jiosaavn_request(
                    "/api/search/songs"
                    f"?query={quote(query)}"
                    f"&page=1"
                    f"&limit={limit}"
                )

                results = (
                    data.get("data", {})
                    .get("results", [])
                )

                songs = [
                    self.format_jio_song(item)
                    for item in results
                ]

                return self.send_json({
                    "success": True,
                    "source": "jiosaavn",
                    "type": "search",
                    "query": query,
                    "total": len(songs),
                    "items": songs
                })

            # =========================
            # JIOSAAVN PLAYLIST
            # =========================

            if path == "/api/jiosaavn/playlist":

                playlist_id = params.get("id", [""])[0]

                limit = self.get_limit(
                    params,
                    default=100,
                    maximum=500
                )

                if not playlist_id:
                    return self.send_json({
                        "success": False,
                        "error": "id is required"
                    }, 400)

                data = self.jiosaavn_request(
                    "/api/playlists/"
                    f"{quote(playlist_id)}"
                )

                playlist = data.get("data", {})

                raw_songs = playlist.get(
                    "songs",
                    []
                )

                songs = [
                    self.format_jio_song(item)
                    for item in raw_songs[:limit]
                ]

                return self.send_json({
                    "success": True,
                    "source": "jiosaavn",
                    "type": "playlist",
                    "playlist_id": playlist_id,
                    "title": playlist.get("name"),
                    "description": playlist.get("description"),
                    "total": len(songs),
                    "items": songs
                })

            # =========================
            # API HOME
            # =========================

            if path in ("", "/api"):

                return self.send_json({
                    "success": True,
                    "name": "Music API",
                    "version": "1.0.0",
                    "endpoints": {
                        "ytmusic_search":
                            "/api/ytmusic/search?q=SONG",
                        "ytmusic_playlist":
                            "/api/ytmusic/playlist?id=PLAYLIST_ID",
                        "jiosaavn_search":
                            "/api/jiosaavn/search?q=SONG",
                        "jiosaavn_playlist":
                            "/api/jiosaavn/playlist?id=PLAYLIST_ID"
                    }
                })

            return self.send_json({
                "success": False,
                "error": "Endpoint not found",
                "path": path
            }, 404)

        except Exception as e:

            return self.send_json({
                "success": False,
                "error": str(e)
            }, 500)

    # ==================================
    # YOUTUBE MUSIC FORMATTER
    # ==================================

    def format_yt_song(self, item):

        artists = []

        for artist in item.get("artists", []):
            name = artist.get("name")

            if name:
                artists.append(name)

        thumbnails = item.get(
            "thumbnails",
            []
        )

        thumbnail = (
            thumbnails[-1].get("url")
            if thumbnails
            else None
        )

        video_id = item.get("videoId")

        return {
            "id": video_id,
            "title": item.get("title"),
            "artists": artists,
            "album": (
                item.get("album", {}).get("name")
                if item.get("album")
                else None
            ),
            "duration": item.get("duration"),
            "duration_seconds":
                item.get("duration_seconds"),
            "thumbnail": thumbnail,
            "url": (
                f"https://music.youtube.com/watch?v={video_id}"
                if video_id
                else None
            )
        }

    # ==================================
    # JIOSAAVN FORMATTER
    # ==================================

    def format_jio_song(self, item):

        artists = []

        primary = (
            item.get("artists", {})
            .get("primary", [])
        )

        for artist in primary:

            name = artist.get("name")

            if name:
                artists.append(name)

        images = item.get(
            "image",
            []
        )

        thumbnail = (
            images[-1].get("url")
            if images
            else None
        )

        duration_raw = item.get(
            "duration"
        )

        try:
            duration_seconds = int(
                duration_raw
            )
        except (TypeError, ValueError):
            duration_seconds = None

        return {
            "id": item.get("id"),
            "title": item.get("name"),
            "artists": artists,
            "album": (
                item.get("album", {})
                .get("name")
            ),
            "duration": duration_raw,
            "duration_seconds":
                duration_seconds,
            "thumbnail": thumbnail,
            "url": item.get("url")
        }

    # ==================================
    # JIOSAAVN REQUEST
    # ==================================

    def jiosaavn_request(self, endpoint):

        url = (
            "https://saavn.dev"
            + endpoint
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    # ==================================
    # LIMIT
    # ==================================

    def get_limit(
        self,
        params,
        default=20,
        maximum=100
    ):

        try:
            value = int(
                params.get(
                    "limit",
                    [str(default)]
                )[0]
            )

            return max(
                1,
                min(value, maximum)
            )

        except (TypeError, ValueError):

            return default

    # ==================================
    # JSON RESPONSE
    # ==================================

    def send_json(
        self,
        data,
        status=200
    ):

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
