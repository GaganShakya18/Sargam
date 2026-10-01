import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.mymusicapp.app',
  appName: 'MyMusicApp',
  webDir: 'dist',
  bundledWebRuntime: false,
  server: {
    ...(process.env.CAPACITOR_DEV_SERVER_URL
      ? { url: process.env.CAPACITOR_DEV_SERVER_URL }
      : {}),
    androidScheme: 'http',
    cleartext: true,
  },
};

export default config;
