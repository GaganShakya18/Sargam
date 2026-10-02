import { Capacitor, registerPlugin } from '@capacitor/core';

const NativePlayback = registerPlugin('NativePlayback');

export const hasNativePlayback = () => (
  Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android'
);

export default NativePlayback;