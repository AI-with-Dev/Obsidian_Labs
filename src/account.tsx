import { FormEvent, useEffect, useState } from 'react'
import { Account, changePassword, exportCsv, exportPdf, saveProfile, signIn, signUp } from './api'
import { Lang, useI18n } from './i18n'
import { VyaparMitraLogo } from './components/VyaparMitraLogo'

const panel = 'rounded-2xl border border-stone-200 bg-white p-5 shadow-xs sm:p-7'
const input = 'mt-1.5 min-h-12 w-full rounded-xl border border-stone-300 bg-white px-3.5 text-base text-stone-900 focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600'
const button = 'inline-flex min-h-12 items-center justify-center rounded-xl bg-emerald-700 px-5 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50'
const secondaryButton = 'inline-flex min-h-12 items-center justify-center rounded-xl border border-stone-300 bg-white px-5 font-semibold text-stone-800 transition hover:bg-stone-50 disabled:opacity-50'
const label = 'block text-sm font-semibold text-stone-800'

type AuthPageProps = {
  error: string
  onRetry: () => void
  onAuthenticated: (account: Account) => void
}

export function AuthPage({ error, onRetry, onAuthenticated }: AuthPageProps) {
  const { t, lang, setLang } = useI18n()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState('')
  const [login, setLogin] = useState({ email: '', password: '' })
  const [setup, setSetup] = useState({
    fullName: '',
    email: '',
    businessName: '',
    phone: '',
    address: '',
    gstin: '',
    password: '',
    passwordConfirmation: '',
    language: lang,
    currency: 'INR',
  })

  useEffect(() => setSetup(current => ({ ...current, language: lang })), [lang])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')
    setBusy(true)
    try {
      const result = mode === 'login'
        ? await signIn(login.email, login.password)
        : await signUp(setup)
      onAuthenticated(result.account)
    } catch (cause) {
      setFormError(cause instanceof Error ? cause.message : t('auth.error'))
    } finally {
      setBusy(false)
    }
  }

  const updateSetup = (key: keyof typeof setup, value: string) =>
    setSetup(current => ({ ...current, [key]: value }))

  const switchMode = (nextMode: 'login' | 'signup') => {
    setMode(nextMode)
    setFormError('')
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#FAF7F2] px-4 py-8 text-stone-900">
      <section className="w-full max-w-xl space-y-5">
        <div className="text-center">
          <div className="mx-auto mb-4 flex justify-center">
            <VyaparMitraLogo className="w-16 h-16 drop-shadow-md hover:scale-105 transition-transform" />
          </div>
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-800">{t('app.name')}</p>
          <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
            {mode === 'login' ? t('auth.loginTitle') : t('auth.setupTitle')}
          </h1>
          <p className="mx-auto mt-2 max-w-lg text-stone-600">
            {mode === 'login' ? t('auth.loginHelp') : t('auth.setupHelp')}
          </p>
        </div>

        <form className={`${panel} space-y-4`} onSubmit={submit}>
          {mode === 'signup' && (
            <>
              <label className={label}>{t('auth.fullName')}
                <input className={input} autoComplete="name" maxLength={100} required value={setup.fullName} onChange={e => updateSetup('fullName', e.target.value)} />
              </label>
              <label className={label}>{t('auth.businessName')}
                <input className={input} autoComplete="organization" maxLength={120} required value={setup.businessName} onChange={e => updateSetup('businessName', e.target.value)} />
              </label>
              <label className={label}>{t('auth.phone')}
                <input className={input} type="tel" autoComplete="tel" maxLength={40} value={setup.phone} onChange={e => updateSetup('phone', e.target.value)} />
              </label>
            </>
          )}

          <label className={label}>{t('auth.email')}
            <input
              className={input}
              type="email"
              autoComplete="email"
              maxLength={254}
              required
              value={mode === 'login' ? login.email : setup.email}
              onChange={e => mode === 'login'
                ? setLogin(current => ({ ...current, email: e.target.value }))
                : updateSetup('email', e.target.value)}
            />
          </label>
          {mode === 'signup' && (
            <>
              <label className={label}>{t('auth.language')}
                <select className={input} value={setup.language} onChange={e => {
                  const language=e.target.value as Lang
                  updateSetup('language',language)
                  setLang(language)
                }}>
                  <option value="en">{t('auth.english')}</option>
                  <option value="hi">{t('auth.hindi')}</option>
                </select>
              </label>
              <label className={label}>{t('auth.currency')}
                <select className={input} value={setup.currency} onChange={e => updateSetup('currency', e.target.value)}>
                  <option value="INR">INR — Indian Rupee</option>
                  <option value="USD">USD — US Dollar</option>
                  <option value="EUR">EUR — Euro</option>
                  <option value="GBP">GBP — British Pound</option>
                </select>
                <span className="mt-1 block text-xs font-normal text-stone-500">{t('settings.currencyNote')}</span>
              </label>
            </>
          )}
          <label className={label}>{t('auth.password')}
            <input
              className={input}
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              minLength={mode === 'login' ? 1 : 12}
              maxLength={128}
              required
              value={mode === 'login' ? login.password : setup.password}
              onChange={e => mode === 'login'
                ? setLogin(current => ({ ...current, password: e.target.value }))
                : updateSetup('password', e.target.value)}
            />
          </label>
          {mode === 'signup' && (
            <>
              <p className="text-sm leading-6 text-stone-600">{t('auth.passwordHelp')}</p>
              <label className={label}>{t('auth.confirmPassword')}
                <input
                  className={input}
                  type="password"
                  autoComplete="new-password"
                  minLength={12}
                  maxLength={128}
                  required
                  value={setup.passwordConfirmation}
                  onChange={e => updateSetup('passwordConfirmation', e.target.value)}
                />
              </label>
              {setup.passwordConfirmation && setup.password !== setup.passwordConfirmation && (
                <p className="text-sm font-medium text-rose-700">{t('auth.passwordMismatch')}</p>
              )}
            </>
          )}

          {(formError || error) && (
            <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-medium text-rose-800">
              {formError || error}
              {error && <button className="ml-2 underline" type="button" onClick={onRetry}>{t('auth.retry')}</button>}
            </div>
          )}
          <button
            className={`${button} w-full`}
            type="submit"
            disabled={busy || !!error || (mode === 'signup' && !!setup.passwordConfirmation && setup.password !== setup.passwordConfirmation)}
          >
            {busy ? t('auth.working') : mode === 'login' ? t('auth.signIn') : t('auth.createAccount')}
          </button>
          <p className="text-center text-sm text-stone-600">
            {mode === 'login' ? (
              <>
                {t('auth.noAccount')}{' '}
                <button className="font-semibold text-emerald-800 underline underline-offset-2 hover:text-emerald-950" type="button" onClick={() => switchMode('signup')}>
                  {t('auth.createAccountLink')}
                </button>
              </>
            ) : (
              <>
                {t('auth.haveAccount')}{' '}
                <button className="font-semibold text-emerald-800 underline underline-offset-2 hover:text-emerald-950" type="button" onClick={() => switchMode('login')}>
                  {t('auth.signIn')}
                </button>
              </>
            )}
          </p>
          <p className="text-center text-xs leading-5 text-stone-500">{t('auth.privacy')}</p>
        </form>
        <div className="text-center">
          <button
            className={secondaryButton}
            type="button"
            onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}
          >
            {lang === 'en' ? 'हिन्दी' : 'English'}
          </button>
        </div>
      </section>
    </main>
  )
}

type SettingsPageProps = {
  account: Account
  onAccountUpdated: (account: Account) => void
  onSignOut: () => Promise<void>
}

export function SettingsPage({ account, onAccountUpdated, onSignOut }: SettingsPageProps) {
  const { t, setLang } = useI18n()
  const [profile, setProfile] = useState(account)
  const [currentPassword, setCurrentPassword] = useState('')
  const [emailPassword, setEmailPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [exportBusy, setExportBusy] = useState(false)

  useEffect(() => setProfile(account), [account])

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setBusy(true)
    setNotice('')
    setError('')
    try {
      const updated = await saveProfile(profile, profile.email !== account.email ? emailPassword : undefined)
      onAccountUpdated(updated)
      setLang(updated.language)
      setEmailPassword('')
      setNotice(t('settings.saved'))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('settings.saveError'))
    } finally {
      setBusy(false)
    }
  }

  const savePassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setBusy(true)
    setNotice('')
    setError('')
    try {
      await changePassword(currentPassword, newPassword, passwordConfirmation)
      setCurrentPassword('')
      setNewPassword('')
      setPasswordConfirmation('')
      setNotice(t('settings.passwordSaved'))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('settings.saveError'))
    } finally {
      setBusy(false)
    }
  }

  const update = <K extends keyof Account>(key: K, value: Account[K]) =>
    setProfile(current => ({ ...current, [key]: value }))

  const download = async (format: 'csv' | 'pdf') => {
    setExportBusy(true)
    setNotice('')
    setError('')
    try {
      if (format === 'csv') await exportCsv()
      else await exportPdf()
      setNotice(t('settings.exported'))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t('settings.exportError'))
    } finally {
      setExportBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-extrabold tracking-tight text-stone-900 sm:text-3xl">{t('settings.title')}</h1>
        <p className="mt-1 text-stone-600">{t('settings.help')}</p>
      </header>

      {(notice || error) && (
        <div role={error ? 'alert' : 'status'} className={`rounded-xl border p-3 text-sm font-medium ${error ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'}`}>
          {error || notice}
        </div>
      )}

      <form className={`${panel} space-y-4`} onSubmit={save}>
        <div>
          <h2 className="text-lg font-bold text-stone-900">{t('settings.businessTitle')}</h2>
          <p className="mt-1 text-sm text-stone-600">{t('settings.businessHelp')}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className={label}>{t('auth.fullName')}
            <input className={input} autoComplete="name" maxLength={100} required value={profile.fullName} onChange={e => update('fullName', e.target.value)} />
          </label>
          <label className={label}>{t('auth.businessName')}
            <input className={input} autoComplete="organization" maxLength={120} required value={profile.businessName} onChange={e => update('businessName', e.target.value)} />
          </label>
        </div>
        <label className={label}>{t('auth.email')}
          <input className={input} type="email" autoComplete="email" maxLength={254} required value={profile.email} onChange={e => update('email', e.target.value)} />
        </label>
        {profile.email !== account.email && (
          <label className={label}>{t('settings.confirmEmailChange')}
            <input className={input} type="password" autoComplete="current-password" required value={emailPassword} onChange={e => setEmailPassword(e.target.value)} />
          </label>
        )}
        <label className={label}>{t('auth.phone')}
          <input className={input} type="tel" autoComplete="tel" maxLength={40} value={profile.phone} onChange={e => update('phone', e.target.value)} />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className={label}>{t('auth.language')}
            <select className={input} value={profile.language} onChange={e => update('language', e.target.value as Lang)}>
              <option value="en">{t('auth.english')}</option>
              <option value="hi">{t('auth.hindi')}</option>
            </select>
          </label>
          <label className={label}>{t('auth.currency')}
            <select className={input} value={profile.currency} onChange={e => update('currency', e.target.value)}>
              <option value="INR">INR — Indian Rupee</option>
              <option value="USD">USD — US Dollar</option>
              <option value="EUR">EUR — Euro</option>
              <option value="GBP">GBP — British Pound</option>
            </select>
            <span className="mt-1 block text-xs font-normal text-stone-500">{t('settings.currencyNote')}</span>
          </label>
        </div>
        <button className={button} type="submit" disabled={busy}>{busy ? t('auth.working') : t('settings.save')}</button>
      </form>

      <form className={`${panel} space-y-4`} onSubmit={savePassword}>
        <div>
          <h2 className="text-lg font-bold text-stone-900">{t('settings.securityTitle')}</h2>
          <p className="mt-1 text-sm text-stone-600">{t('settings.securityHelp')}</p>
        </div>
        <label className={label}>{t('settings.currentPassword')}
          <input className={input} type="password" autoComplete="current-password" required value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className={label}>{t('settings.newPassword')}
            <input className={input} type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={newPassword} onChange={e => setNewPassword(e.target.value)} />
          </label>
          <label className={label}>{t('auth.confirmPassword')}
            <input className={input} type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={passwordConfirmation} onChange={e => setPasswordConfirmation(e.target.value)} />
          </label>
        </div>
        <p className="text-sm text-stone-600">{t('auth.passwordHelp')}</p>
        {passwordConfirmation && newPassword !== passwordConfirmation && <p className="text-sm font-medium text-rose-700">{t('auth.passwordMismatch')}</p>}
        <button className={secondaryButton} type="submit" disabled={busy || newPassword !== passwordConfirmation}>{t('settings.updatePassword')}</button>
      </form>

      <section className={`${panel} space-y-4`}>
        <div>
          <h2 className="text-lg font-bold text-stone-900">{t('settings.dataTitle')}</h2>
          <p className="mt-1 text-sm text-stone-600">{t('settings.dataHelp')}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button className={secondaryButton} type="button" disabled={exportBusy} onClick={() => void download('csv')}>{t('settings.exportCsv')}</button>
          <button className={secondaryButton} type="button" disabled={exportBusy} onClick={() => void download('pdf')}>{t('settings.exportPdf')}</button>
        </div>
        <p className="text-xs leading-5 text-stone-500">{t('settings.dataNote')}</p>
      </section>

      <section className={`${panel} flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between`}>
        <div>
          <h2 className="font-bold text-stone-900">{t('settings.sessionTitle')}</h2>
          <p className="mt-1 text-sm text-stone-600">{t('settings.sessionHelp')}</p>
        </div>
        <button className="inline-flex min-h-12 items-center justify-center rounded-xl border border-rose-300 px-5 font-semibold text-rose-800 hover:bg-rose-50" type="button" onClick={() => void onSignOut()}>
          {t('settings.signOut')}
        </button>
      </section>
    </div>
  )
}
