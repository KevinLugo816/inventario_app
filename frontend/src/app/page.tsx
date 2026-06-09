"use client";

import { useIsClient } from "@/hooks/useIsClient";
import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

export default function Home() {
  type Producto = { cantidad: number; tipo?: string };
  const isClient = useIsClient();
  const [productos, setProductos] = useState<Producto[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/inventario`)
      .then((res) => res.json())
      .then((data) => setProductos(data.productos));
  }, []);

  const totalInventario = productos.reduce((acc, p) => acc + p.cantidad, 0);
  const productosRegistrados = productos.length;

  const consultasIA = 0;

  const categoriasMap: Record<string, number> = {};
  productos.forEach((p) => {
    const tipo = p.tipo ?? "Sin categoría";
    categoriasMap[tipo] = (categoriasMap[tipo] || 0) + p.cantidad;
  });

  const dataCategorias = Object.entries(categoriasMap).map(([tipo, cantidad]) => ({
    tipo,
    cantidad,
  }));

  const colores = ["#f97316", "#fb923c", "#fdba74", "#fed7aa", "#ffedd5"];

  return (
    <div className="space-y-10">

      {/* Título principal */}
      <h1 className="text-4xl font-bold tracking-tight text-orange-400">
        Panel Principal
      </h1>

      {/* Tarjetas de métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Tarjeta 1 */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] hover:scale-[1.02] transition-transform">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400 text-lg">Total Inventario</h3>
            <span className="text-orange-500 text-3xl">📦</span>
          </div>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {totalInventario}
          </p>
        </div>

        {/* Tarjeta 2 */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] hover:scale-[1.02] transition-transform">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400 text-lg">Productos Registrados</h3>
            <span className="text-orange-500 text-3xl">📄</span>
          </div>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {productosRegistrados}
          </p>
        </div>

        {/* Tarjeta 3 */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] hover:scale-[1.02] transition-transform">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400 text-lg">Consultas IA Hoy</h3>
            <span className="text-orange-500 text-3xl">🤖</span>
          </div>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {consultasIA}
          </p>
        </div>

      </div>

      {/* Sección de gráficos */}
      <h2 className="text-3xl font-semibold text-orange-300">Gráficos</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Gráfico 1: Categorías */}
        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-xl font-semibold mb-4 text-gray-300">
            Inventario por Categoría
          </h3>

          <div className="relative w-full h-[300px]">
            {isClient && (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dataCategorias}
                    dataKey="cantidad"
                    nameKey="tipo"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label
                  >
                    {dataCategorias.map((_, index) => (
                      <Cell key={index} fill={colores[index % colores.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Gráfico 2: Movimientos (placeholder v1) */}
        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-xl font-semibold mb-4 text-gray-300">
            Algo aquí
          </h3>

          <div className="h-56 flex items-center justify-center text-orange-500">
            (Vacío por ahora)
          </div>
        </div>

      </div>

    </div>
  );
}
