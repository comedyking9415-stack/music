from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
from ytmusicapi import YTMusic
import urllib.request
import urllib.error
import json


yt = YTMusic()


class handler(BaseHTTPRequestHandler):

    # =========================================
    # OPTIONS / CORS
    # =========================================

    def do_OPTIONS(self):
        self.send_json({
            "success": True
        })

    # =========================================
    # GET
    # =========================================

    def do_GET(self):

        try:

            parsed = urlparse(self.path)

            path = parsed.path.rstrip("/")

            params = parse_qs(
                parsed.query
            )

            # =================================
            # HOME
            # =================================

            if path in ("", "/api"):

                return self.send_json({
                    "success": True,
                    "name": "Music API",
                    "version": "2.0.0",

                    "endpoints": {

                        "ytmusic_search":
                            "/api/ytmusic/search?q=SONG&limit=20",

                        "ytmusic_playlist":
                            "/api/ytmusic/playlist?id=PLAYLIST_ID&limit=100",

                        "jiosaavn_search":
                            "/api/jiosaavn/search?q=SONG&limit=20",

                        "jiosaavn_playlist":
                            "/api/jiosaavn/playlist?id=PLAYLIST_ID&limit=100"
                    }
                })

            # =================================
            # YOUTUBE MUSIC SEARCH
            # =================================

            if path == "/api/ytmusic/search":

                query = params.get(
                    "q",
                    [""]
                )[0]

                limit = self.get_limit(
                    params,
                    default=20,
                    maximum=100
                )

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

                songs = []

                for item in results:

                    if item:

                        songs.append(
                            self.format_yt_song(
                                item
                            )
                        )

                return self.send_json({

                    "success": True,

                    "source": "ytmusic",

                    "type": "search",

                    "query": query,

                    "total": len(songs),

                    "items": songs
                })

            # =================================
            # YOUTUBE MUSIC PLAYLIST
            # =================================

            if path == "/api/ytmusic/playlist":

                playlist_id = params.get(
                    "id",
                    [""]
                )[0]

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

                for item in playlist.get(
                    "tracks",
                    []
                ):

                    if item:

                        songs.append(
                            self.format_yt_song(
                                item
                            )
                        )

                return self.send_json({

                    "success": True,

                    "source": "ytmusic",

                    "type": "playlist",

                    "playlist_id":
                        playlist_id,

                    "title":
                        playlist.get("title"),

                    "description":
                        playlist.get("description"),

                    "total":
                        len(songs),

                    "items":
                        songs
                })

            # =================================
            # JIOSAAVN SEARCH
            # =================================

            if path == "/api/jiosaavn/search":

                query = params.get(
                    "q",
                    [""]
                )[0]

                limit = self.get_limit(
                    params,
                    default=20,
                    maximum=100
                )

                if not query.strip():

                    return self.send_json({
                        "success": False,
                        "error": "q is required"
                    }, 400)

                endpoint = (
                    "/result/?query="
                    + quote(query)
                )

                data = self.jiosaavn_request(
                    endpoint
                )

                # API returns an array
                if not isinstance(
                    data,
                    list
                ):

                    return self.send_json({
                        "success": False,
                        "error":
                            "Invalid JioSaavn response"
                    }, 502)

                data = data[:limit]

                songs = []

                for item in data:

                    if item:

                        songs.append(
                            self.format_jio_song(
                                item
                            )
                        )

                return self.send_json({

                    "success": True,

                    "source": "jiosaavn",

                    "type": "search",

                    "query": query,

                    "total": len(songs),

                    "items": songs
                })

            # =================================
            # JIOSAAVN PLAYLIST
            # =================================

            if path == "/api/jiosaavn/playlist":

                playlist_id = params.get(
                    "id",
                    [""]
                )[0]

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

                # Playlist ID को URL में use करने के लिए
                # JioSaavn playlist URL बनाते हैं.
                playlist_url = (
                    "https://www.jiosaavn.com/featured/"
                    + quote(
                        playlist_id,
                        safe=""
                    )
                )

                endpoint = (
                    "/playlist/?query="
                    + quote(
                        playlist_url,
                        safe=""
                    )
                )

                data = self.jiosaavn_request(
                    endpoint
                )

                # अलग-अलग deployments में
                # response list या object हो सकता है.

                songs_data = []

                title = None
                description = None

                if isinstance(
                    data,
                    list
                ):

                    songs_data = data

                elif isinstance(
                    data,
                    dict
                ):

                    title = data.get(
                        "title"
                    )

                    description = data.get(
                        "description"
                    )

                    songs_data = (
                        data.get("songs")
                        or data.get("data")
                        or []
                    )

                songs_data = songs_data[:limit]

                songs = []

                for item in songs_data:

                    if isinstance(
                        item,
                        dict
                    ):

                        songs.append(
                            self.format_jio_song(
                                item
                            )
                        )

                return self.send_json({

                    "success": True,

                    "source": "jiosaavn",

                    "type": "playlist",

                    "playlist_id":
                        playlist_id,

                    "title":
                        title,

                    "description":
                        description,

                    "total":
                        len(songs),

                    "items":
                        songs
                })

            # =================================
            # 404
            # =================================

            return self.send_json({

                "success": False,

                "error":
                    "Endpoint not found",

                "path":
                    path

            }, 404)

        except Exception as e:

            return self.send_json({

                "success": False,

                "error":
                    str(e)

            }, 500)

    # =========================================
    # YOUTUBE MUSIC FORMATTER
    # =========================================

    def format_yt_song(
        self,
        item
    ):

        artists = []

        for artist in item.get(
            "artists",
            []
        ):

            name = artist.get(
                "name"
            )

            if name:

                artists.append(
                    name
                )

        thumbnails = item.get(
            "thumbnails",
            []
        )

        thumbnail = None

        if thumbnails:

            thumbnail = thumbnails[
                -1
            ].get("url")

        video_id = item.get(
            "videoId"
        )

        return {

            "id":
                video_id,

            "title":
                item.get("title"),

            "artists":
                artists,

            "album":
                (
                    item.get(
                        "album",
                        {}
                    ).get("name")
                    if item.get("album")
                    else None
                ),

            "duration":
                item.get("duration"),

            "duration_seconds":
                item.get(
                    "duration_seconds"
                ),

            "thumbnail":
                thumbnail,

            "url":
                (
                    "https://music.youtube.com/watch?v="
                    + video_id
                    if video_id
                    else None
                )
        }

    # =========================================
    # JIOSAAVN FORMATTER
    # =========================================

    def format_jio_song(
        self,
        item
    ):

        artists = []

        primary_artists = item.get(
            "primary_artists",
            ""
        )

        if primary_artists:

            artists = [

                x.strip()

                for x in primary_artists.split(",")

                if x.strip()
            ]

        # fallback
        if not artists:

            singers = item.get(
                "singers",
                ""
            )

            if singers:

                artists = [

                    x.strip()

                    for x in singers.split(",")

                    if x.strip()
                ]

        duration_raw = item.get(
            "duration"
        )

        try:

            duration_seconds = int(
                duration_raw
            )

        except (
            TypeError,
            ValueError
        ):

            duration_seconds = None

        duration = None

        if duration_seconds is not None:

            minutes = (
                duration_seconds // 60
            )

            seconds = (
                duration_seconds % 60
            )

            duration = (
                f"{minutes}:"
                f"{seconds:02d}"
            )

        return {

            "id":
                item.get("id"),

            "title":
                item.get("song")
                or item.get("title"),

            "artists":
                artists,

            "album":
                item.get("album"),

            "duration":
                duration,

            "duration_seconds":
                duration_seconds,

            "thumbnail":
                item.get("image")
                or item.get("image_url"),

            "url":
                item.get("perma_url")
                or item.get("tiny_url")
        }

    # =========================================
    # JIOSAAVN REQUEST
    # =========================================

    def jiosaavn_request(
        self,
        endpoint
    ):

        base_url = (
            "https://saavnapi-nine.vercel.app"
        )

        url = (
            base_url
            + endpoint
        )

        request = urllib.request.Request(

            url,

            headers={

                "User-Agent":
                    "Mozilla/5.0",

                "Accept":
                    "application/json",

                "Connection":
                    "close"
            }
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=20
            ) as response:

                body = response.read()

                if not body:

                    raise Exception(
                        "Empty JioSaavn response"
                    )

                return json.loads(
                    body.decode("utf-8")
                )

        except urllib.error.HTTPError as e:

            raise Exception(
                "JioSaavn API HTTP "
                + str(e.code)
            )

        except urllib.error.URLError as e:

            raise Exception(
                "JioSaavn API connection error: "
                + str(e.reason)
            )

    # =========================================
    # LIMIT
    # =========================================

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
                min(
                    value,
                    maximum
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return default

    # =========================================
    # JSON RESPONSE
    # =========================================

    def send_json(
        self,
        data,
        status=200
    ):

        body = json.dumps(

            data,

            ensure_ascii=False

        ).encode("utf-8")

        self.send_response(
            status
        )

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
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(
            body
        )
