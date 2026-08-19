import { loginRequest } from './api'
import { AuthForm } from './AuthForm'
import type { AuthenticatedUser } from './types'

interface LoginFormProps {
  onLoggedIn: (user: AuthenticatedUser) => void
  onSwitchToRegister?: () => void
}

export function LoginForm({ onLoggedIn, onSwitchToRegister }: LoginFormProps) {
  return (
    <AuthForm
      title="Sign in"
      description="Return to your saved adventures."
      submitLabel="Sign in"
      pendingLabel="Signing in…"
      passwordAutoComplete="current-password"
      errorFallback="Invalid email or password."
      mutationFn={loginRequest}
      onSuccess={onLoggedIn}
      footer={
        onSwitchToRegister && (
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            Need an account? Register
          </button>
        )
      }
    />
  )
}
