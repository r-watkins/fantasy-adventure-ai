import { useMutation } from '@tanstack/react-query'
import { useId, useState, type FormEvent, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { describeApiError } from '@/lib/api-client'

import type { AuthenticatedUser } from './types'

interface AuthFormProps {
  title: string
  description: string
  submitLabel: string
  pendingLabel: string
  passwordAutoComplete: 'new-password' | 'current-password'
  passwordHelpText?: string
  errorFallback: string
  footer?: ReactNode
  mutationFn: (email: string, password: string) => Promise<AuthenticatedUser>
  onSuccess: (user: AuthenticatedUser) => void
}

export function AuthForm({
  title,
  description,
  submitLabel,
  pendingLabel,
  passwordAutoComplete,
  passwordHelpText,
  errorFallback,
  footer,
  mutationFn,
  onSuccess,
}: AuthFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const emailId = useId()
  const passwordId = useId()
  const errorId = useId()

  const mutation = useMutation({
    mutationFn: () => mutationFn(email, password),
    // Wrapped rather than passed directly: react-query calls onSuccess
    // with (data, variables, context), and the public onSuccess prop's
    // contract is a single-argument (user) => void callback.
    onSuccess: (user) => onSuccess(user),
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    mutation.mutate()
  }

  const errorMessage = mutation.isError
    ? describeApiError(mutation.error, errorFallback)
    : null

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit} noValidate>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor={emailId}>Email</Label>
            <Input
              id={emailId}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              aria-invalid={errorMessage ? true : undefined}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor={passwordId}>Password</Label>
            <Input
              id={passwordId}
              type="password"
              autoComplete={passwordAutoComplete}
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-invalid={errorMessage ? true : undefined}
              aria-describedby={errorMessage ? errorId : undefined}
            />
            {passwordHelpText && (
              <p className="text-xs text-muted-foreground">{passwordHelpText}</p>
            )}
          </div>
          {errorMessage && (
            <p id={errorId} role="alert" className="text-sm text-destructive">
              {errorMessage}
            </p>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? pendingLabel : submitLabel}
          </Button>
          {footer}
        </CardFooter>
      </form>
    </Card>
  )
}
