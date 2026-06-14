"use client";

import "./globals.css";
import type { ReactNode } from "react";
import Sidebar from "../components/Sidebar";
import { ChatProvider } from "@/context/ChatContext";
import { useEffect, useState } from "react";
import { CalendarIcon } from "@heroicons/react/24/outline";

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

    const ahora = new Date();
    const mañana = new Date(ahora);
    mañana.setHours(24, 0, 0, 0);

    const msHastaMedianoche = mañana.getTime() - ahora.getTime();

    const timeout = setTimeout(() => {
      actualizarFecha();
      setInterval(actualizarFecha, 24 * 60 * 60 * 1000);
    }, msHastaMedianoche);

    return () => clearTimeout(timeout);
  }, []);

  return (
    <html lang="es">
      <body className="flex h-screen bg-[#0f0f0f] text-white">

        <ChatProvider>
          <Sidebar />

          <div className="flex-1 flex flex-col">

            <header className="w-full h-16 bg-[#141414] border-b border-[#2a2a2a] flex items-center px-8 shadow-md justify-between">
              <h2 className="text-2xl font-semibold text-orange-400">
                Gestión de Inventario
              </h2>

              {/* Fecha con panel y Heroicon */}
              <div className="flex items-center gap-2 bg-gradient-to-br from-[#1b1b1b] to-[#141414] px-4 py-2 rounded-xl border border-[#2a2a2a] shadow-md">
                <CalendarIcon className="w-6 h-6 text-orange-500" />
                <span className="text-lg font-semibold text-orange-500 tracking-wide">
                  {fechaActual}
                </span>
              </div>
            </header>

            <main className="flex-1 p-10 overflow-y-auto bg-[#0f0f0f]">
              {children}
            </main>

          </div>
        </ChatProvider>

      </body>
    </html>
  );
}
