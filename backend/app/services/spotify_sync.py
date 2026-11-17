# backend/app/services/spotify_sync.py
import os
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from ..models import StreamHistory
from .parser import build_entity_caches, get_or_create_cached

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN", "")

async def sync_recent_spotify_streams(db: Session) -> dict:
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN):
        return {"status": "skipped", "reason": "Spotify credentials not configured"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Exchange refresh_token for a fresh access_token
        token_resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": SPOTIFY_REFRESH_TOKEN,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        # 2. Fetch the last 50 recently played tracks
        recent_resp = await client.get(
            "https://api.spotify.com/v1/me/player/recently-played?limit=50",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        recent_resp.raise_for_status()
        items = recent_resp.json().get("items", [])

    caches = build_entity_caches(db)
    existing_streams = set(db.query(StreamHistory.track_id, StreamHistory.played_at).all())
    new_streams = []

    for item in items:
        track_data = item.get("track") or {}
        played_at_str = item.get("played_at")
        if not track_data or not played_at_str:
            continue

        track_title = track_data.get("name", "Unknown Track")
        artists = track_data.get("artists") or []
        artist_name = artists[0].get("name", "Unknown Artist") if artists else "Unknown Artist"
        album_data = track_data.get("album") or {}
        album_title = album_data.get("name", "Unknown Album")
        duration_ms = int(track_data.get("duration_ms") or 0)

        played_at = datetime.fromisoformat(played_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
        artist, album, track = get_or_create_cached(db, caches, artist_name, album_title, track_title, duration_ms)

        # Save Spotify's high-res album cover immediately if our album doesn't have one yet!
        images = album_data.get("images") or []
        if images and not album.artwork_url:
            album.artwork_url = images[0].get("url")

        stream_key = (track.id, played_at)
        if stream_key not in existing_streams:
            existing_streams.add(stream_key)
            new_streams.append(
                StreamHistory(
                    track_id=track.id,
                    played_at=played_at,
                    duration_played_ms=duration_ms,
                    end_reason="SPOTIFY_API_SYNC",
                    source="SPOTIFY_API",
                )
            )

    if new_streams:
        db.bulk_save_objects(new_streams)
        db.commit()
    return {"status": "success", "new_streams_added": len(new_streams)}