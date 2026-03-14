'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  WalletIcon,
  MagnifyingGlassIcon,
  LinkIcon,
  SparklesIcon,
  UsersIcon,
  ClockIcon,
  CubeTransparentIcon,
} from '@heroicons/react/24/outline'

const NAV_GROUPS = [
  {
    label: 'Explore',
    items: [
      { label: 'Discover',       href: '/dashboard/discover',            icon: MagnifyingGlassIcon },
      { label: 'Search Product', href: '/dashboard/search-product',      icon: HomeIcon            },
      { label: 'Product Link',   href: '/dashboard/product-link',        icon: LinkIcon            },
      { label: 'AI Results',     href: '/dashboard/ai-results',          icon: SparklesIcon        },
    ],
  },
  {
    label: 'Deals',
    items: [
      { label: 'Negotiation Room',     href: '/dashboard/negotiation-room',     icon: UsersIcon           },
      { label: 'Deal History',         href: '/dashboard/deal-history',         icon: ClockIcon           },
      { label: 'Blockchain Contracts', href: '/dashboard/blockchain-contracts', icon: CubeTransparentIcon },
    ],
  },
  {
    label: 'Other',
    items: [
      { label: 'Buyer',        href: '/dashboard/buyer',  icon: ChatBubbleLeftRightIcon },
      { label: 'Seller',       href: '/dashboard/seller', icon: DocumentTextIcon        },
      { label: 'Wallet',       href: '/dashboard/wallet', icon: WalletIcon              },
    ],
  },
]

export default function Sidebar() {
  const path = usePathname()
  return (
    <aside className="w-56 min-h-screen bg-[#12121f] border-r border-[#2a2a45] flex flex-col pt-6 px-3 shrink-0 overflow-y-auto">
      <div className="px-3 mb-6">
        <span className="text-xl font-bold bg-linear-to-r from-violet-500 to-blue-500 bg-clip-text text-transparent">
          🤖 DealBot AI
        </span>
      </div>
      <nav className="flex flex-col gap-0.5">
        {NAV_GROUPS.map(group => (
          <div key={group.label} className="mb-3">
            <p className="px-3 mb-1 text-[10px] text-zinc-600 uppercase tracking-widest font-semibold">
              {group.label}
            </p>
            {group.items.map(({ label, href, icon: Icon }) => {
              const active = path === href || path.startsWith(href + '/')
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all
                    ${active
                      ? 'bg-violet-600/20 text-violet-400 border border-violet-500/30'
                      : 'text-zinc-400 hover:bg-white/5 hover:text-white'}`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {label}
                </Link>
              )
            })}
          </div>
        ))}
      </nav>
    </aside>
  )
}
