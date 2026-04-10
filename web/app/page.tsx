import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-gold-gradient mb-4">
          Luxura Distribution
        </h1>
        <p className="text-gray-400 mb-8">
          Extensions capillaires haut de gamme
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link 
            href="/admin"
            className="px-8 py-4 bg-luxura-gold text-black font-semibold rounded-lg hover:bg-yellow-500 transition"
          >
            Accéder au Dashboard
          </Link>
        </div>
      </div>
    </main>
  )
}
