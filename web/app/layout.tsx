import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Luxura Dashboard',
  description: 'Dashboard administrateur Luxura Distribution',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-luxura-dark">
        {children}
      </body>
    </html>
  )
}
