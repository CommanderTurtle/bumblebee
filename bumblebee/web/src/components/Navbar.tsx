import { Link, useLocation } from 'react-router-dom';
import { Music2, Search, Link2, Info } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();

  const navLink = (to: string, label: string, icon: React.ReactNode) => (
    <Link
      to={to}
      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        location.pathname === to
          ? 'bg-slate-800 text-amber-400'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
      }`}
    >
      {icon}
      {label}
    </Link>
  );

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-900 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5">
          <Music2 className="w-6 h-6 text-amber-400" />
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-extrabold text-amber-400 tracking-tight">
              BUMBLEBEE
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">
              Speak Through Song
            </span>
          </div>
        </Link>

        {/* Nav Links */}
        <div className="flex items-center gap-1">
          {navLink('/', 'Search', <Search className="w-4 h-4" />)}
          {navLink('/chain', 'Chain Builder', <Link2 className="w-4 h-4" />)}
          {navLink('/about', 'About', <Info className="w-4 h-4" />)}
        </div>
      </div>
    </nav>
  );
}
