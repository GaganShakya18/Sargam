import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.mymusicapp.app',
  appName: 'MyMusicApp',
  webDir: 'dist',
  bundledWebRuntime: false,
  server: {
    url: 'http://192.168.137.1:5175',
    androidScheme: 'http',
    cleartext: true,
  },
};

export default config;
