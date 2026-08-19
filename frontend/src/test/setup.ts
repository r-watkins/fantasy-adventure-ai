import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

import '@testing-library/jest-dom/vitest'

// RTL's automatic cleanup registration relies on detecting a global
// `afterEach`, which isn't present since vite.config.ts doesn't set
// `test.globals: true` - without this, unmounted component trees from
// earlier tests in the same file stack up in the DOM.
afterEach(() => {
  cleanup()
})

// jsdom doesn't implement matchMedia - anything rendering ThemeProvider
// (which queries prefers-color-scheme for the 'system' theme) throws
// without this.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })
}
