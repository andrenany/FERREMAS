import type { Metadata } from 'next'
import { Poppins, Open_Sans } from 'next/font/google'
import './globals.css'

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-poppins',
})

const openSans = Open_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '600'],
  variable: '--font-open-sans',
})

export const metadata: Metadata = {
  title: 'FERREMAS - Tu Ferretería de Confianza',
  description: 'Encuentra todo lo que necesitas para tus proyectos de construcción y mejoras del hogar en FERREMAS.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" className={`${poppins.variable} ${openSans.variable}`}>
      <body className="font-open-sans bg-neutral-light min-h-screen">
        {children}
      </body>
    </html>
  )
} 