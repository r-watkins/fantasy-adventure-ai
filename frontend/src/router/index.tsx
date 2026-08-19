import { useQuery } from '@tanstack/react-query'
import {
  createRootRoute,
  createRoute,
  createRouter,
  Link,
  Outlet,
  redirect,
  useNavigate,
  useRouteContext,
  useRouter,
} from '@tanstack/react-router'
import { useState } from 'react'

import { ModeToggle } from '@/components/mode-toggle'
import { buttonVariants } from '@/components/ui/button'
import { LoginForm } from '@/features/auth/LoginForm'
import { RegisterForm } from '@/features/auth/RegisterForm'
import type { AuthenticatedUser } from '@/features/auth/types'
import { OriginSelect } from '@/features/setup/OriginSelect'
import { SaveSlotSelect } from '@/features/setup/SaveSlotSelect'
import { getSave } from '@/features/setup/saves-api'
import { SettingsScreen } from '@/features/settings/SettingsScreen'

import { fetchCurrentUser } from './auth-guard'

interface RouterContext {
  user: AuthenticatedUser | null
}

const rootRoute = createRootRoute({
  beforeLoad: async (): Promise<RouterContext> => ({ user: await fetchCurrentUser() }),
  component: RootLayout,
})

function RootLayout() {
  const { user } = useRouteContext({ from: rootRoute.id })

  return (
    <div className="flex min-h-svh flex-col items-center gap-8 p-6">
      <header className="fixed top-4 right-4 z-50 flex items-center gap-2">
        {user && (
          <Link to="/settings" className={buttonVariants({ variant: 'ghost', size: 'sm' })}>
            Settings
          </Link>
        )}
        <ModeToggle />
      </header>
      <main className="flex w-full flex-1 flex-col items-center justify-center gap-8">
        <Outlet />
      </main>
    </div>
  )
}

const welcomeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: ({ context }) => {
    if (context.user) {
      throw redirect({ to: '/saves' })
    }
  },
  component: WelcomeScreen,
})

function WelcomeScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const navigate = useNavigate()
  const router = useRouter()

  async function handleAuthenticated() {
    await router.invalidate()
    await navigate({ to: '/saves' })
  }

  return (
    <>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-semibold">Fantasy AI Adventure</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          A grounded high-fantasy text adventure set in the Ashfen Realm.
        </p>
      </div>
      {mode === 'login' ? (
        <LoginForm
          onLoggedIn={handleAuthenticated}
          onSwitchToRegister={() => setMode('register')}
        />
      ) : (
        <RegisterForm
          onRegistered={handleAuthenticated}
          onSwitchToLogin={() => setMode('login')}
        />
      )}
    </>
  )
}

const savesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/saves',
  beforeLoad: ({ context }) => {
    if (!context.user) {
      throw redirect({ to: '/' })
    }
  },
  component: SavesScreen,
})

function SavesScreen() {
  const navigate = useNavigate()

  return (
    <SaveSlotSelect
      onContinue={(saveId) => navigate({ to: '/game/$saveId', params: { saveId } })}
      onNewGame={() => navigate({ to: '/new-game' })}
    />
  )
}

const newGameRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/new-game',
  beforeLoad: ({ context }) => {
    if (!context.user) {
      throw redirect({ to: '/' })
    }
  },
  component: NewGameScreen,
})

function NewGameScreen() {
  const navigate = useNavigate()

  return (
    <OriginSelect
      onCreated={(saveId) => navigate({ to: '/game/$saveId', params: { saveId } })}
      onBack={() => navigate({ to: '/saves' })}
    />
  )
}

const gameRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/game/$saveId',
  beforeLoad: ({ context }) => {
    if (!context.user) {
      throw redirect({ to: '/' })
    }
  },
  component: GameScreenPlaceholder,
})

function GameScreenPlaceholder() {
  const { saveId } = gameRoute.useParams()
  const saveQuery = useQuery({ queryKey: ['saves', saveId], queryFn: () => getSave(saveId) })

  if (saveQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading your adventure…</p>
  }

  if (saveQuery.isError || !saveQuery.data) {
    return <p role="alert" className="text-sm text-destructive">Could not load this save.</p>
  }

  const { name, game_state_json: state, messages } = saveQuery.data

  return (
    <div className="flex w-full max-w-lg flex-col gap-4">
      <h1 className="text-lg font-medium">{name}</h1>
      <p className="text-sm text-muted-foreground">
        Playing as {state.player.name} at {state.player.location_id}.
      </p>
      {messages.map((message) => (
        <p key={message.turn_number} className="text-sm">
          {message.content}
        </p>
      ))}
      <p className="text-xs text-muted-foreground">
        The full game screen arrives in Phase 3 - this confirms the save loaded correctly.
      </p>
    </div>
  )
}

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  beforeLoad: ({ context }) => {
    if (!context.user) {
      throw redirect({ to: '/' })
    }
  },
  component: SettingsRouteComponent,
})

function SettingsRouteComponent() {
  const navigate = useNavigate()
  const router = useRouter()

  async function handleLoggedOut() {
    await router.invalidate()
    await navigate({ to: '/' })
  }

  return <SettingsScreen onLoggedOut={handleLoggedOut} />
}

const routeTree = rootRoute.addChildren([
  welcomeRoute,
  savesRoute,
  newGameRoute,
  gameRoute,
  settingsRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
