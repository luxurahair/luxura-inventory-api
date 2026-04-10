import Link from 'next/link'
import { 
  SwatchIcon, 
  PhotoIcon, 
  DocumentTextIcon,
  ArrowTrendingUpIcon 
} from '@heroicons/react/24/outline'

const stats = [
  { name: 'Produits', value: '67', change: '+12%' },
  { name: 'Couleurs', value: '25', change: '+5' },
  { name: 'Articles Blog', value: '18', change: '+3' },
  { name: 'Visiteurs', value: '1,247', change: '+22%' },
]

const quickActions = [
  { 
    name: 'Color Engine', 
    description: 'Créer des images produits avec watermarks',
    href: '/admin/color-engine',
    icon: SwatchIcon,
    color: 'bg-purple-500'
  },
  { 
    name: 'Gérer Images', 
    description: 'Répertoire de couleurs et gabarits',
    href: '/admin/images',
    icon: PhotoIcon,
    color: 'bg-blue-500'
  },
  { 
    name: 'Blog', 
    description: 'Gérer les articles du blog',
    href: '/admin/blog',
    icon: DocumentTextIcon,
    color: 'bg-green-500'
  },
]

export default function AdminDashboard() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Bienvenue dans l'espace administrateur Luxura</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-luxura-gray rounded-xl p-6 border border-gray-800">
            <p className="text-gray-400 text-sm">{stat.name}</p>
            <p className="text-3xl font-bold text-white mt-2">{stat.value}</p>
            <p className="text-green-500 text-sm mt-1 flex items-center gap-1">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              {stat.change}
            </p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Actions rapides</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              href={action.href}
              className="bg-luxura-gray rounded-xl p-6 border border-gray-800 hover:border-luxura-gold transition group"
            >
              <div className={`${action.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4`}>
                <action.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white group-hover:text-luxura-gold transition">
                {action.name}
              </h3>
              <p className="text-gray-400 text-sm mt-1">{action.description}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Activité récente</h2>
        <div className="bg-luxura-gray rounded-xl border border-gray-800 divide-y divide-gray-800">
          <div className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
              <SwatchIcon className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-white">Nouvelle couleur ajoutée: <span className="text-luxura-gold">Aurore Boréale</span></p>
              <p className="text-gray-500 text-sm">Il y a 2 heures</p>
            </div>
          </div>
          <div className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
              <DocumentTextIcon className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <p className="text-white">Article publié: <span className="text-luxura-gold">Guide extensions Genius</span></p>
              <p className="text-gray-500 text-sm">Il y a 5 heures</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
