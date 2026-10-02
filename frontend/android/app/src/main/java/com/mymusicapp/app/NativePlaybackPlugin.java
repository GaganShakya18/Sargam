package com.mymusicapp.app;

import android.Manifest;
import android.content.ComponentName;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Looper;

import androidx.core.content.ContextCompat;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.Player;
import androidx.media3.session.MediaController;
import androidx.media3.session.SessionToken;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.PermissionState;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import com.google.common.util.concurrent.ListenableFuture;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

@CapacitorPlugin(
    name = "NativePlayback",
    permissions = @Permission(alias = "notifications", strings = { Manifest.permission.POST_NOTIFICATIONS })
)
public final class NativePlaybackPlugin extends Plugin {
    private MediaController controller;
    private ListenableFuture<MediaController> controllerFuture;
    private boolean autoplayEnabled = true;
    private boolean shuffleEnabled;

    private final Player.Listener playerListener = new Player.Listener() {
        @Override
        public void onEvents(Player player, Player.Events events) {
            if (controller != null) notifyListeners("playbackState", buildState(controller));
        }
    };

    @PluginMethod
    public void playQueue(PluginCall call) {
        if (Build.VERSION.SDK_INT >= 33 && getPermissionState("notifications") != PermissionState.GRANTED) {
            requestPermissionForAlias("notifications", call, "playQueuePermissionCallback");
            return;
        }
        startQueue(call);
    }

    @PermissionCallback
    private void playQueuePermissionCallback(PluginCall call) {
        startQueue(call);
    }

    private void startQueue(PluginCall call) {
        try {
            JSONArray sourceQueue = call.getArray("queue");
            List<MediaItem> items = new ArrayList<>();
            if (sourceQueue != null) {
                for (int index = 0; index < sourceQueue.length(); index++) {
                    JSONObject source = sourceQueue.getJSONObject(index);
                    String id = source.optString("id");
                    String streamUrl = source.optString("streamUrl");
                    if (id.isEmpty() || streamUrl.isEmpty()) continue;

                    MediaMetadata.Builder metadata = new MediaMetadata.Builder()
                        .setTitle(source.optString("title", "Unknown title"))
                        .setArtist(source.optString("artist", "Unknown Artist"));
                    String artworkUrl = source.optString("artworkUrl");
                    if (!artworkUrl.isEmpty()) metadata.setArtworkUri(Uri.parse(artworkUrl));
                    Bundle extras = new Bundle();
                    extras.putString("artist_name", source.optString("artist", "Unknown Artist"));
                    extras.putString("album_title", source.optString("album", ""));
                    extras.putString("cover_url", artworkUrl);
                    extras.putLong("duration_seconds", source.optLong("durationSeconds", 0));
                    extras.putString("audio_format", source.optString("audioFormat", ""));
                    metadata.setExtras(extras);
                    items.add(new MediaItem.Builder()
                        .setMediaId(id)
                        .setUri(Uri.parse(streamUrl))
                        .setMediaMetadata(metadata.build())
                        .build());
                }
            }
            if (items.isEmpty()) {
                call.reject("Song could not be played.");
                return;
            }

            int startIndex = Math.max(0, Math.min(call.getInt("index", 0), items.size() - 1));
            autoplayEnabled = call.getBoolean("autoplay", true);
            shuffleEnabled = call.getBoolean("shuffleEnabled", false);
            int repeatMode = call.getInt("repeatMode", Player.REPEAT_MODE_OFF);
            withController(call, connected -> {
                connected.setMediaItems(items, startIndex, 0L);
                connected.setShuffleModeEnabled(shuffleEnabled);
                connected.setRepeatMode(repeatMode);
                MusicPlaybackService.setAutoplayEnabled(autoplayEnabled);
                connected.prepare();
                connected.play();
                call.resolve(buildState(connected));
            });
        } catch (JSONException exception) {
            call.reject("Song could not be played.", exception);
        }
    }

    @PluginMethod
    public void getState(PluginCall call) {
        withController(call, connected -> call.resolve(buildState(connected)));
    }

    @PluginMethod
    public void play(PluginCall call) {
        withController(call, connected -> {
            connected.play();
            call.resolve(buildState(connected));
        });
    }

    @PluginMethod
    public void pause(PluginCall call) {
        withController(call, connected -> {
            connected.pause();
            call.resolve(buildState(connected));
        });
    }

    @PluginMethod
    public void next(PluginCall call) {
        withController(call, connected -> {
            if (connected.hasNextMediaItem()) connected.seekToNextMediaItem();
            else connected.pause();
            call.resolve(buildState(connected));
        });
    }

    @PluginMethod
    public void previous(PluginCall call) {
        withController(call, connected -> {
            if (connected.getCurrentPosition() > 3000) connected.seekToDefaultPosition();
            else if (connected.hasPreviousMediaItem()) connected.seekToPreviousMediaItem();
            call.resolve(buildState(connected));
        });
    }

    @PluginMethod
    public void seekTo(PluginCall call) {
        long positionMs = Math.max(0L, (long) (call.getDouble("position", 0.0) * 1000));
        withController(call, connected -> {
            connected.seekTo(positionMs);
            call.resolve(buildState(connected));
        });
    }

    @PluginMethod
    public void setOptions(PluginCall call) {
        autoplayEnabled = call.getBoolean("autoplay", autoplayEnabled);
        shuffleEnabled = call.getBoolean("shuffleEnabled", shuffleEnabled);
        int repeatMode = call.getInt("repeatMode", Player.REPEAT_MODE_OFF);
        withController(call, connected -> {
            connected.setShuffleModeEnabled(shuffleEnabled);
            connected.setRepeatMode(repeatMode);
            MusicPlaybackService.setAutoplayEnabled(autoplayEnabled);
            call.resolve(buildState(connected));
        });
    }

    private void withController(PluginCall call, ControllerAction action) {
        if (controller != null) {
            ContextCompat.getMainExecutor(getContext()).execute(() -> {
                try {
                    action.run(controller);
                } catch (Exception exception) {
                    call.reject("Playback service unavailable.", exception);
                }
            });
            return;
        }
        if (controllerFuture == null) {
            SessionToken token = new SessionToken(
                getContext(),
                new ComponentName(getContext(), MusicPlaybackService.class)
            );
            controllerFuture = new MediaController.Builder(getContext(), token)
                .setApplicationLooper(Looper.getMainLooper())
                .buildAsync();
        }
        controllerFuture.addListener(() -> {
            try {
                controller = controllerFuture.get();
                controller.addListener(playerListener);
                action.run(controller);
            } catch (Exception exception) {
                call.reject("Playback service unavailable.", exception);
            }
        }, ContextCompat.getMainExecutor(getContext()));
    }

    private JSObject buildState(MediaController mediaController) {
        JSObject state = new JSObject();
        MediaItem currentItem = mediaController.getCurrentMediaItem();
        state.put("currentSong", currentItem == null ? null : songFrom(currentItem));
        List<JSObject> queue = new ArrayList<>();
        for (int index = 0; index < mediaController.getMediaItemCount(); index++) {
            queue.add(songFrom(mediaController.getMediaItemAt(index)));
        }
        state.put("queue", queue);
        state.put("currentIndex", mediaController.getCurrentMediaItemIndex());
        state.put("position", Math.max(0L, mediaController.getCurrentPosition()) / 1000.0);
        long duration = mediaController.getDuration();
        state.put("duration", duration < 0 ? 0 : duration / 1000.0);
        state.put("isPlaying", mediaController.isPlaying());
        state.put("shuffleEnabled", mediaController.getShuffleModeEnabled());
        state.put("repeatMode", mediaController.getRepeatMode());
        state.put("autoplayEnabled", autoplayEnabled);
        state.put("error", mediaController.getPlayerError() == null ? "" : "Song could not be played.");
        return state;
    }

    private JSObject songFrom(MediaItem item) {
        MediaMetadata metadata = item.mediaMetadata;
        JSObject song = new JSObject();
        song.put("id", item.mediaId);
        song.put("title", metadata.title == null ? "Unknown title" : metadata.title.toString());
        song.put("artist_name", metadata.artist == null ? "Unknown Artist" : metadata.artist.toString());
        song.put("cover_url", metadata.artworkUri == null ? "" : metadata.artworkUri.toString());
        if (metadata.extras != null) {
            song.put("album_title", metadata.extras.getString("album_title", ""));
            song.put("duration_seconds", metadata.extras.getLong("duration_seconds", 0));
            song.put("audio_format", metadata.extras.getString("audio_format", ""));
        }
        return song;
    }

    @Override
    protected void handleOnDestroy() {
        if (controller != null) controller.removeListener(playerListener);
        if (controllerFuture != null) MediaController.releaseFuture(controllerFuture);
        controller = null;
        controllerFuture = null;
        super.handleOnDestroy();
    }

    private interface ControllerAction {
        void run(MediaController controller);
    }
}