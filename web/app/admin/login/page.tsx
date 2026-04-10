'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AdminLogin() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Simple password check (in production, use proper auth)
    if (password === 'luxura2024') {
      // Set cookie
      document.cookie = 'luxura_admin_token=authenticated; path=/; max-age=86400'
      router.push('/admin')
    } else {
      setError('Mot de passe incorrect')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-luxura-dark p-4">
      <div className="w-full max-w-md">
        <div className="bg-luxura-gray rounded-2xl p-8 shadow-xl border border-gray-800">
          {/* Logo */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gold-gradient">Luxura</h1>
            <p className="text-gray-400 mt-2">Dashboard Administrateur</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Mot de passe
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-luxura-dark border border-gray-700 rounded-lg text-white focus:border-luxura-gold focus:outline-none transition"
                placeholder="Entrez le mot de passe"
                required
              />
            </div>

            {error && (
              <p className="text-red-500 text-sm text-center">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-luxura-gold text-black font-semibold rounded-lg hover:bg-yellow-500 transition disabled:opacity-50"
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
