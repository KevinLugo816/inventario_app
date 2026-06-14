"use client";

import "./globals.css";
import type { ReactNode } from "react";
import Sidebar from "../components/Sidebar";
import { ChatProvider } from "@/context/ChatContext";
import { useEffect, useState } from "react";

export const metadata = {
  title: "Bell IA",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  const [fechaActual, setFechaActual] = useState("");

  useEffect(() => {
    const actualizarFecha = () => {
      const fecha = new Date();
      const opciones: Intl.DateTimeFormatOptions = {
        day: "2-digit",
        month: "short",
        year: "numeric",
      };

      const formateada = fecha
        .toLocaleDateString("es-ES", opciones)
        .replace(".", "");

      setFechaActual(formateada);
    };

    actualizarFecha();

    // Calcular tiempo hasta medianoche
    const ahora = new Date();
    const mañana = new Date(ahora);
    mañana.setHours(24, 0, 0, 0);

    const msHastaMedianoche = mañana.getTime() - ahora.getTime();

    // Actualizar justo a medianoche y luego cada 24h
    const timeout = setTimeout(() => {
      actualizarFecha();
      setInterval(actualizarFecha, 24 * 60 * 60 * 1000);
    }, msHastaMedianoche);

    return () => clearTimeout(timeout);
  }, []);

  return (
    <html lang="es">
      <body className="flex h-screen bg-[#0f0f0f] text-white">

        {/* ChatProvider envuelve TODO el dashboard */}
        <ChatProvider>

          {/* Sidebar moderno */}
          <Sidebar />

          {/* Contenido principal */}
          <div className="flex-1 flex flex-col">

            {/* Topbar */}
            <header className="w-full h-16 bg-[#141414] border-b border-[#2a2a2a] flex items-center px-8 shadow-md justify-between">
              
              {/* Título */}
              <h2 className="text-2xl font-semibold text-orange-400">
                Gestión de Inventario
              </h2>

              {/* Fecha con ícono */}
              <div className="flex items-center gap-2 text-orange-500">
                <span className="text-xl">📅</span>
                <span className="text-lg font-semibold tracking-wide">
                  {fechaActual}
                </span>
              </div>

            </header>

            {/* Contenido dinámico */}
            <main className="flex-1 p-10 overflow-y-auto bg-[#0f0f0f]">
              {children}
            </main>

          </div>

        </ChatProvider>

      </body>
    </html>
  );
}
