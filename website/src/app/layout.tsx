import type { Metadata } from 'next'
import { Providers } from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'ISRO AQI Monitoring System',
  description: 'AI-Based Nationwide Surface PM2.5 and AQI Mapping Using Satellite Observations and Meteorological Data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-950 text-white antialiased">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
