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
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";

type Producto = {
  cantidad: number;
  tipo?: string;
  fecha_caducidad?: string;
};

export default function Home() {
  const isClient = useIsClient();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);
  const [fechaActual, setFechaActual] = useState("");

  // FECHA ACTUAL
  useEffect(() => {
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
  }, []);

  // CARGA DE INVENTARIO
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/inventario`)
      .then((res) => res.json())
      .then((data) => {
        setProductos(data.productos || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // MÉTRICAS
  const totalInventario = productos.reduce((acc, p) => acc + p.cantidad, 0);
  const productosRegistrados = productos.length;
  const consultasIA = 0;

  // CATEGORÍAS
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

  // GRÁFICO DE STOCK MEJORADO
  const stockLevels = {
    alto: productos.filter((p) => p.cantidad >= 20).length,
    medio: productos.filter((p) => p.cantidad >= 10 && p.cantidad < 20).length,
    bajo: productos.filter((p) => p.cantidad < 10).length,
  };

  const dataStock = [
    { nivel: "Alto", cantidad: stockLevels.alto },
    { nivel: "Medio", cantidad: stockLevels.medio },
    { nivel: "Bajo", cantidad: stockLevels.bajo },
  ];

  // SKELETON
  if (loading) {
    return (
      <div className="space-y-10 animate-pulse">
        <h1 className="text-4xl font-bold tracking-tight text-orange-400">
          Panel Principal
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#1b1b1b] h-32 rounded-xl"></div>
          <div className="bg-[#1b1b1b] h-32 rounded-xl"></div>
          <div className="bg-[#1b1b1b] h-32 rounded-xl"></div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-[#1b1b1b] h-72 rounded-xl"></div>
          <div className="bg-[#1b1b1b] h-72 rounded-xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">

      {/* Título */}
      <h1 className="text-4xl font-bold tracking-tight text-orange-400 animate-[fadeIn_.4s_ease-out]">
        Panel Principal
      </h1>

      {/* TARJETAS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Tarjeta 1 */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] hover:scale-[1.03] transition-all animate-[fadeIn_.4s_ease-out]">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400 text-lg">Total Inventario</h3>
            <span className="text-orange-500 text-4xl drop-shadow-[0_0_10px_rgba(249,115,22,0.4)]">📦</span>
          </div>
          <p className="text-5xl font-bold text-orange-500 mt-2">{totalInventario}</p>
          <div className="h-[3px] w-full bg-orange-500/20 mt-4 rounded-full"></div>
        </div>

        {/* Tarjeta 2 */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] hover:scale-[1.03] transition-all animate-[fadeIn_.5s_ease-out]">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400 text-lg">Productos Registrados</h3>
            <span className="text-orange-500 text-4xl drop-shadow-[0_0_10px_rgba(249,115,22,0.4)]">📄</span>
          </div>
          <p className="text-5xl font-bold text-orange-500 mt-2">{productosRegistrados}</p>
          <div className="h-[3px] w-full bg-orange-500/20 mt-4 rounded-full"></div>
        </div>

        {/* Tarjeta 3 */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] hover:scale-[1.03] transition-all animate-[fadeIn_.6s_ease-out]">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400 text-lg">Consultas IA Hoy</h3>
            <span className="text-orange-500 text-4xl drop-shadow-[0_0_10px_rgba(249,115,22,0.4)]">🤖</span>
          </div>
          <p className="text-5xl font-bold text-orange-500 mt-2">{consultasIA}</p>
          <div className="h-[3px] w-full bg-orange-500/20 mt-4 rounded-full"></div>
        </div>

      </div>

      {/* GRÁFICOS */}
      <h2 className="text-3xl font-semibold text-orange-300 drop-shadow-[0_0_8px_rgba(249,115,22,0.3)]">
        Gráficos
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Gráfico 1 */}
        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a] animate-[fadeIn_.5s_ease-out]">
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
                    isAnimationActive={true}
                    animationDuration={800}
                    label={({ name, percent }) =>
                      `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                    }
                  >
                    {dataCategorias.map((_, index) => (
                      <Cell key={index} fill={colores[index % colores.length]} />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "#1b1b1b",
                      border: "1px solid #333",
                      borderRadius: "10px",
                      color: "#fff",
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Gráfico 2: Stock mejorado */}
        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a] animate-[fadeIn_.6s_ease-out]">
          <h3 className="text-xl font-semibold mb-4 text-gray-300">
            Niveles de Stock
          </h3>

          <div className="relative w-full h-[300px]">
            {isClient && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dataStock}>
                  <XAxis dataKey="nivel" stroke="#aaa" />
                  <YAxis stroke="#aaa" />

                  <Tooltip
                    contentStyle={{
                      background: "#1b1b1b",
                      border: "1px solid #333",
                      borderRadius: "10px",
                      color: "#fff",
                    }}
                    formatter={(value) => [`${value} productos`, "Cantidad"]}
                  />

                  <Bar
                    dataKey="cantidad"
                    radius={[10, 10, 0, 0]}
                    animationDuration={800}
                  >
                    {dataStock.map((entry, index) => {
                      const colores: Record<"Alto" | "Medio" | "Bajo", string> = {
                        Alto: "#22c55e",   // verde
                        Medio: "#eab308",  // amarillo
                        Bajo: "#ef4444",   // rojo
                      };
                      const nivel = entry.nivel as keyof typeof colores;
                      return <Cell key={index} fill={colores[nivel]} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* PANEL DE FECHA */}
        <div className="bg-gradient-to-br from-[#1b1b1b] to-[#141414] p-6 rounded-xl shadow-lg border border-[#2a2a2a] flex flex-col items-center justify-center animate-[fadeIn_.7s_ease-out]">
          <h3 className="text-xl font-semibold text-gray-300 mb-2">
            Fecha Actual
          </h3>

          <p className="text-4xl font-bold text-orange-500 tracking-wide">
            {fechaActual}
          </p>

          <div className="h-[3px] w-full bg-orange-500/20 mt-4 rounded-full"></div>
        </div>

      </div>

    </div>
  );
}
