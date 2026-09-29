export function resolveApiBaseUrl(
  location = typeof window !== 'undefined' ? window.location : { hostname: 'localhost', protocol: 'http:' },
  configuredBaseUrl = import.meta.env?.VITE_API_BASE_URL,
  isNativePlatform = typeof window !== 'undefined' && window.Capacitor?.isNativePlatform?.(),
) {
  const hostname = location.hostname || 'localhost';
  const protocol = location.protocol || 'http:';

  if (configuredBaseUrl) {
    const configuredUrl = new URL(configuredBaseUrl);
    const isLoopbackHost = ['localhost', '127.0.0.1', '::1'].includes(hostname);
    const isCapacitorWebView = hostname === 'localhost' && isNativePlatform;
    if (isLoopbackHost && !isCapacitorWebView) {
      configuredUrl.hostname = hostname;
      return configuredUrl.toString().replace(/\/+$/, '');
    }
    return configuredUrl.toString().replace(/\/+$/, '');
  }

  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
    return 'http://localhost:8000/api';
  }

  return `${protocol}//${hostname}:8000/api`;
}

export const API_BASE_URL = resolveApiBaseUrl();
