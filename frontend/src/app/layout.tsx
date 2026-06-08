import "./globals.css";
import type { ReactNode } from "react";
import Sidebar from "../components/Sidebar";
import { ChatProvider } from "@/context/ChatContext";

export const metadata = {
  title: "Bell IA",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
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
            <header className="w-full h-16 bg-[#141414] border-b border-[#2a2a2a] flex items-center px-8 shadow-md">
              <h2 className="text-2xl font-semibold text-orange-400">Gestión de Inventario</h2>
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
