"use client";

import { useIsClient } from "@/hooks/useIsClient";
import { useEffect, useState, useMemo } from "react";
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

type Lote = {
  id: number;
  quantity: number;
  arrival_date: string;
  expiration_date: string | null;
};

type Variante = {
  variant_id: number;
  brand: string;
  type_variety: string;
  content_value: number;
  content_unit: string;
  sku_code: string;
  total_quantity: number;
  batches: Lote[];
  product_name: string;
  category: string;
};

type Producto = {
  id: number;
  name: string;
  category: string;
  variants: Omit<Variante, "product_name" | "category">[];
};

export default function Home() {
  const isClient = useIsClient();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/inventario`)
      .then((res) => res.json())
      .then((data) => {
        setProductos(data.productos || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const variantes = useMemo(() => {
    return productos.flatMap((p) =>
      p.variants.map((v) => ({
        ...v,
        product_name: p.name,
        category: p.category,
      }))
    );
  }, [productos]);

  const totalInventario = variantes.reduce(
    (acc, v) => acc + v.total_quantity,
    0
  );

  const variantesRegistradas = variantes.length;

  const consultasIA = 0;

  const categoriasMap: Record<string, number> = {};
  variantes.forEach((v) => {
    const cat = v.category || "Sin categoría";
    categoriasMap[cat] = (categoriasMap[cat] || 0) + v.total_quantity;
  });

  const dataCategorias = Object.entries(categoriasMap).map(
    ([categoria, cantidad]) => ({
      categoria,
      cantidad,
    })
  );

  const colores = ["#f97316", "#fb923c", "#fdba74", "#fed7aa", "#ffedd5"];

  const stockLevels = {
    alto: variantes.filter((v) => v.total_quantity >= 20).length,
    medio: variantes.filter((v) => v.total_quantity >= 10 && v.total_quantity < 20).length,
    bajo: variantes.filter((v) => v.total_quantity < 10).length,
  };

  const dataStock = [
    { nivel: "Alto", cantidad: stockLevels.alto },
    { nivel: "Medio", cantidad: stockLevels.medio },
    { nivel: "Bajo", cantidad: stockLevels.bajo },
  ];


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
          <p className="text-5xl font-bold text-orange-500 mt-2">{variantesRegistradas}</p>
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
            Inventario por Rubro
          </h3>

          <div className="relative w-full h-[300px]">
            {isClient && (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dataCategorias}
                    dataKey="cantidad"
                    nameKey="categoria"
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

        {/* Gráfico 2 */}
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
                    labelStyle={{ color: "#f97316" }}
                    itemStyle={{ color: "#f97316" }}
                    formatter={(value) => [`${value} variantes`, "Cantidad"]}
                  />

                  <Bar
                    dataKey="cantidad"
                    radius={[10, 10, 0, 0]}
                    animationDuration={800}
                  >
                    {dataStock.map((entry, index) => {
                      const colores: Record<"Alto" | "Medio" | "Bajo", string> = {
                        Alto: "#22c55e",
                        Medio: "#eab308",
                        Bajo: "#ef4444",
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

      </div>

    </div>
  );
}
