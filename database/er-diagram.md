# ER Diagram

```text
users ───< playlists
users ───< listening_history
artists ───< songs
artists ───< albums
albums ───< songs
songs ───< listening_history
```

## Notes

- One user can have many playlists.
- One user can have many listening history records.
- One artist can have many songs and albums.
- One album can contain many songs.
- One song may appear in many listening history events.
