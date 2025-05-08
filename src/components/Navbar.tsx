import Link from 'next/link';
import { ShoppingCart, Search, Menu } from 'lucide-react';

export const Navbar = () => {
  return (
    <nav className="bg-primary text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link href="/" className="font-poppins font-bold text-2xl">
              FERREMAS
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/categorias" className="hover:text-secondary transition-colors">
              Categorías
            </Link>
            <Link href="/ofertas" className="hover:text-secondary transition-colors">
              Ofertas
            </Link>
            <Link href="/marcas" className="hover:text-secondary transition-colors">
              Marcas
            </Link>
            <Link href="/contacto" className="hover:text-secondary transition-colors">
              Contacto
            </Link>
          </div>

          {/* Search and Cart */}
          <div className="flex items-center space-x-4">
            <button className="hover:text-secondary transition-colors">
              <Search className="h-6 w-6" />
            </button>
            <Link href="/carrito" className="hover:text-secondary transition-colors relative">
              <ShoppingCart className="h-6 w-6" />
              <span className="absolute -top-2 -right-2 bg-secondary text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                0
              </span>
            </Link>
            <button className="md:hidden hover:text-secondary transition-colors">
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}; 