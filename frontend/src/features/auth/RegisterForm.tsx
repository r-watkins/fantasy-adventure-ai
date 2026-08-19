import { registerRequest } from './api'
import { AuthForm } from './AuthForm'
import type { AuthenticatedUser } from './types'

interface RegisterFormProps {
  onRegistered: (user: AuthenticatedUser) => void
  onSwitchToLogin?: () => void
}

export function RegisterForm({ onRegistered, onSwitchToLogin }: RegisterFormProps) {
  return (
    <AuthForm
      title="Create an account"
      description="Begin your adventure in the Ashfen Realm."
      submitLabel="Create account"
      pendingLabel="Creating account…"
      passwordAutoComplete="new-password"
      passwordHelpText="At least 8 characters."
      errorFallback="Please check your email and password."
      mutationFn={registerRequest}
      onSuccess={onRegistered}
      footer={
        onSwitchToLogin && (
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            Already have an account? Sign in
          </button>
        )
      }
    />
  )
}
