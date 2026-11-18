// The public path the app is served under, from Vite's `base` option (set
// at build time via VITE_BASE_PATH). Returned without a trailing slash, so
// the domain root yields '' and a subdirectory yields e.g.
// '/fantasy-adventure-ai' - ready to prepend to an absolute path.
export function getBasePath(): string {
  return import.meta.env.BASE_URL.replace(/\/+$/, '')
}
