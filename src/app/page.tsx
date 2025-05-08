import { Navbar } from '@/components/Navbar';
import { OfertasCarousel } from '@/components/OfertasCarousel';
import Image from 'next/image';

const productosDestacados = [
  {
    id: 1,
    nombre: 'Taladro Percutor 750W',
    descripcion: 'Potente taladro para todo tipo de superficies',
    precio: 89.99,
    imagen: '/images/products/Taladro Percutor 750W.jpeg'
  },
  {
    id: 2,
    nombre: 'Martillo de Acero 16oz',
    descripcion: 'Martillo profesional de alta resistencia',
    precio: 24.99,
    imagen: '/images/products/Martillo de Acero 16oz.jpeg'
  },
  {
    id: 3,
    nombre: 'Casco de Seguridad',
    descripcion: 'Protección certificada para construcción',
    precio: 19.99,
    imagen: '/images/products/casco_de_seguirdad.jpeg'
  },
  {
    id: 4,
    nombre: 'Cemento Polpaico 25kg',
    descripcion: 'Cemento de alta calidad y resistencia',
    precio: 15.99,
    imagen: '/images/products/Cemento Polpaico 25kg.jpeg'
  }
];

export default function Home() {
  return (
    <main>
      <Navbar />
      <OfertasCarousel />
      
      {/* Categorías Destacadas */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-poppins font-bold text-neutral mb-8">
            Categorías Destacadas
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {['Herramientas', 'Construcción', 'Jardinería', 'Electricidad'].map((categoria) => (
              <div key={categoria} className="group relative overflow-hidden rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                <div className="aspect-square bg-primary-light relative">
                  {/* Aquí irían las imágenes de las categorías cuando estén disponibles */}
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex items-end p-4">
                  <h3 className="text-white font-poppins font-semibold text-lg group-hover:text-secondary transition-colors">
                    {categoria}
                  </h3>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Productos Destacados */}
      <section className="py-12 bg-neutral-light">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-poppins font-bold text-neutral mb-8">
            Productos Destacados
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {productosDestacados.map((producto) => (
              <div key={producto.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow overflow-hidden">
                <div className="aspect-square relative">
                  <Image
                    src={producto.imagen}
                    alt={producto.nombre}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="p-4">
                  <h3 className="font-poppins font-semibold text-lg mb-2">
                    {producto.nombre}
                  </h3>
                  <p className="text-neutral text-sm mb-3">
                    {producto.descripcion}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-primary font-bold text-xl">
                      ${producto.precio}
                    </span>
                    <button className="bg-secondary hover:bg-secondary-dark text-white px-4 py-2 rounded transition-colors">
                      Agregar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Banner de Beneficios */}
      <section className="bg-primary text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 mb-4 relative">
                <Image
                  src="/images/products/R.jpeg"
                  alt="Envío Gratis"
                  fill
                  className="object-contain"
                />
              </div>
              <h3 className="font-poppins font-semibold mb-2">Envío Gratis</h3>
              <p className="text-sm">En compras mayores a $500</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 mb-4 relative">
                <Image
                  src="/images/products/casco_de_seguirdad.jpeg"
                  alt="Seguridad"
                  fill
                  className="object-contain"
                />
              </div>
              <h3 className="font-poppins font-semibold mb-2">Pago Seguro</h3>
              <p className="text-sm">Transacciones 100% seguras</p>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 mb-4 relative">
                <Image
                  src="/images/products/Destornillador Phillips.jpeg"
                  alt="Soporte"
                  fill
                  className="object-contain"
                />
              </div>
              <h3 className="font-poppins font-semibold mb-2">Soporte 24/7</h3>
              <p className="text-sm">Atención personalizada</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
} 