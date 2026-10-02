package com.mymusicapp.app;

import androidx.annotation.Nullable;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.C;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;

import android.os.Handler;
import android.os.Looper;

public final class MusicPlaybackService extends MediaSessionService {
    private static MusicPlaybackService instance;
    private final Handler playerHandler = new Handler(Looper.getMainLooper());
    private ExoPlayer player;
    private MediaSession mediaSession;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        AudioAttributes audioAttributes = new AudioAttributes.Builder()
            .setUsage(C.USAGE_MEDIA)
            .setContentType(C.AUDIO_CONTENT_TYPE_MUSIC)
            .build();
        player = new ExoPlayer.Builder(this)
            .setAudioAttributes(audioAttributes, true)
            .setHandleAudioBecomingNoisy(true)
            .build();
        player.setWakeMode(C.WAKE_MODE_NETWORK);
        mediaSession = new MediaSession.Builder(this, player).build();
    }

    static void setAutoplayEnabled(boolean enabled) {
        MusicPlaybackService service = instance;
        if (service == null) return;
        service.playerHandler.post(() -> {
            if (service.player != null) {
                service.player.setPauseAtEndOfMediaItems(!enabled);
            }
        });
    }

    @Nullable
    @Override
    public MediaSession onGetSession(MediaSession.ControllerInfo controllerInfo) {
        return mediaSession;
    }

    @Override
    public void onDestroy() {
        if (mediaSession != null) mediaSession.release();
        if (player != null) player.release();
        if (instance == this) instance = null;
        super.onDestroy();
    }
}