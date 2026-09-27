# Sequence Diagrams

## Login flow

1. User submits username and password.
2. API validates credentials.
3. JWT is issued and returned.
4. Client stores token for future requests.

## Play song flow

1. User selects a song.
2. Frontend requests song metadata.
3. Backend fetches the song record.
4. Media file is served or streamed.
