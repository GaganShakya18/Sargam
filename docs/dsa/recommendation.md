# Recommendation System

## Goal

Recommend songs based on user listening patterns and content similarity.

## Basic model

- Store recent plays and user preferences
- Compare against genres, artists, and mood
- Rank candidate songs by similarity score

## Early implementation

Use a weighted score:

score = 0.5 * genre_match + 0.3 * artist_similarity + 0.2 * popularity
