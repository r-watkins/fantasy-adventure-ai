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
