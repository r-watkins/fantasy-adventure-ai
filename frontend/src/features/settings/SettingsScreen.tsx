import { useMutation } from '@tanstack/react-query'

import { type Theme, useTheme } from '@/components/theme-provider'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { logoutRequest } from '@/features/auth/api'
import { describeApiError } from '@/lib/api-client'

import { updateThemeSetting } from './api'

interface SettingsScreenProps {
  onLoggedOut: () => void
}

const THEME_OPTIONS: { value: Theme; label: string }[] = [
  { value: 'system', label: 'System' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
]

export function SettingsScreen({ onLoggedOut }: SettingsScreenProps) {
  const { theme, setTheme } = useTheme()

  const themeMutation = useMutation({
    mutationFn: (next: Theme) => updateThemeSetting(next),
  })

  const logoutMutation = useMutation({
    mutationFn: logoutRequest,
    onSuccess: () => onLoggedOut(),
  })

  function handleThemeChange(next: Theme) {
    // Applied locally right away (ThemeProvider also caches it in
    // localStorage as a fast pre-hydration value); PUT persists it
    // server-side so it follows the account across devices/logins.
    setTheme(next)
    themeMutation.mutate(next)
  }

  const themeErrorMessage = themeMutation.isError
    ? describeApiError(themeMutation.error, 'Could not save your theme preference.')
    : null

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Settings</CardTitle>
        <CardDescription>Appearance and account.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <Label id="theme-label">Theme</Label>
          <div className="flex gap-2" role="radiogroup" aria-labelledby="theme-label">
            {THEME_OPTIONS.map((option) => (
              <Button
                key={option.value}
                type="button"
                variant={theme === option.value ? 'default' : 'outline'}
                role="radio"
                aria-checked={theme === option.value}
                onClick={() => handleThemeChange(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
          {themeErrorMessage && (
            <p role="alert" className="text-sm text-destructive">
              {themeErrorMessage}
            </p>
          )}
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={() => logoutMutation.mutate()}
          disabled={logoutMutation.isPending}
        >
          {logoutMutation.isPending ? 'Signing out…' : 'Sign out'}
        </Button>
      </CardContent>
    </Card>
  )
}
