import { useState, useEffect } from 'react';
import Image from 'next/image';

const ofertas = [
  {
    id: 1,
    titulo: '¡Gran Venta de Herramientas!',
    descripcion: 'Hasta 40% de descuento en herramientas eléctricas',
    imagen: '/images/ofertas/herramientas.jpg',
    color: 'bg-primary'
  },
  {
    id: 2,
    titulo: 'Promoción Especial',
    descripcion: '2x1 en productos de jardinería',
    imagen: '/images/ofertas/jardineria.jpg',
    color: 'bg-secondary'
  },
  {
    id: 3,
    titulo: 'Oferta Limitada',
    descripcion: 'Descuentos especiales en materiales de construcción',
    imagen: '/images/ofertas/construccion.jpg',
    color: 'bg-neutral'
  }
];

export const OfertasCarousel = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % ofertas.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative h-[400px] overflow-hidden">
      {ofertas.map((oferta, index) => (
        <div
          key={oferta.id}
          className={`absolute w-full h-full transition-transform duration-500 ease-in-out ${
            index === currentSlide ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          <div className={`${oferta.color} w-full h-full relative flex items-center`}>
            <div className="absolute inset-0">
              <Image
                src={oferta.imagen}
                alt={oferta.titulo}
                fill
                className="object-cover opacity-50"
              />
            </div>
            <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-white">
              <h2 className="font-poppins font-bold text-4xl md:text-5xl mb-4 animate-slide-up">
                {oferta.titulo}
              </h2>
              <p className="text-xl md:text-2xl mb-8 animate-fade-in">
                {oferta.descripcion}
              </p>
              <button className="bg-secondary hover:bg-secondary-dark text-white font-semibold py-3 px-8 rounded-lg transition-colors animate-fade-in">
                Ver Oferta
              </button>
            </div>
          </div>
        </div>
      ))}
      
      {/* Indicadores */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
        {ofertas.map((_, index) => (
          <button
            key={index}
            className={`w-3 h-3 rounded-full transition-colors ${
              index === currentSlide ? 'bg-secondary' : 'bg-white bg-opacity-50'
            }`}
            onClick={() => setCurrentSlide(index)}
          />
        ))}
      </div>
    </div>
  );
}; 