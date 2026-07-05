"use client";

import { useEffect, useState, useMemo } from "react";

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

const formatearFecha = (fecha: string | null) => {
  if (!fecha) return "Por definir";

  if (/^\d{4}-\d{2}-\d{2}$/.test(fecha)) {
    const [y, m, d] = fecha.split("-");
    return `${d}/${m}/${y}`;
  }

  return "Por definir";
};

const estadoCaducidad = (fecha: string | null) => {
  if (!fecha) return "text-gray-300";

  const hoy = new Date();
  const cad = new Date(fecha);

  if (isNaN(cad.getTime())) return "text-gray-300";

  const diff = cad.getTime() - hoy.getTime();
  const dias = Math.ceil(diff / (1000 * 60 * 60 * 24));

  if (dias < 0) return "text-red-400";
  if (dias <= 30) return "text-yellow-400";
  return "text-green-400";
};

export default function Inventario() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [busqueda, setBusqueda] = useState("");
  const [orden, setOrden] = useState<string | null>(null);
  const [direccion, setDireccion] = useState<"asc" | "desc">("asc");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/inventario`)
      .then((res) => res.json())
      .then((data) => {
        setProductos(data.productos || []);
        setLoading(false);
      })
      .catch(() => {
        setProductos([]);
        setLoading(false);
      });
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

  const variantesFiltradas = useMemo(() => {
    return variantes.filter((v) => {
      const lote = v.batches[0] || null;

      const texto = `
        ${v.category}
        ${v.product_name}
        ${v.brand}
        ${v.type_variety}
        ${v.content_value} ${v.content_unit}
        ${lote?.arrival_date ?? ""}
        ${lote?.expiration_date ?? ""}
      `.toLowerCase();

      return texto.includes(busqueda.toLowerCase());
    });
  }, [variantes, busqueda]);

  const ordenarPor = (columna: string) => {
    if (orden === columna) {
      setDireccion(direccion === "asc" ? "desc" : "asc");
    } else {
      setOrden(columna);
      setDireccion("asc");
    }
  };

  const variantesOrdenadas = useMemo(() => {
    if (!orden) return variantesFiltradas;

    return [...variantesFiltradas].sort((a, b) => {
      if (orden === "total_quantity") {
        return direccion === "asc"
          ? a.total_quantity - b.total_quantity
          : b.total_quantity - a.total_quantity;
      }

      if (orden === "fecha_ingreso") {
        const fechaA = new Date(a.batches[0]?.arrival_date || "9999-12-31").getTime();
        const fechaB = new Date(b.batches[0]?.arrival_date || "9999-12-31").getTime();
        return direccion === "asc" ? fechaA - fechaB : fechaB - fechaA;
      }

      if (orden === "fecha_caducidad") {
        const fechaA = new Date(a.batches[0]?.expiration_date || "9999-12-31").getTime();
        const fechaB = new Date(b.batches[0]?.expiration_date || "9999-12-31").getTime();
        return direccion === "asc" ? fechaA - fechaB : fechaB - fechaA;
      }

      const A = String((a as any)[orden] ?? "").toLowerCase();
      const B = String((b as any)[orden] ?? "").toLowerCase();

      return direccion === "asc" ? A.localeCompare(B) : B.localeCompare(A);
    });
  }, [variantesFiltradas, orden, direccion]);


  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-400 text-xl animate-pulse">
          Cargando inventario...
        </p>
      </div>
    );
  }


  return (
    <div className="space-y-10">
      <h1 className="text-4xl font-bold tracking-tight text-orange-400">
        Inventario
      </h1>

      <input
        type="text"
        placeholder="Buscar por cualquier campo..."
        className="w-full p-4 rounded-xl bg-[#111] border border-[#2a2a2a] text-white focus:outline-none focus:ring-2 focus:ring-orange-500 transition"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
      />

      {/* TARJETAS RESUMEN */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-gray-400 text-lg">Productos Totales</h3>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {variantes.length}
          </p>
        </div>

        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-gray-400 text-lg">Categorías</h3>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {new Set(variantes.map((v) => v.category)).size}
          </p>
        </div>

        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-gray-400 text-lg">Stock Total</h3>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {variantes.reduce((acc, v) => acc + v.total_quantity, 0)}
          </p>
        </div>
      </div>

      {/* TABLA */}
      <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
        <h2 className="text-2xl font-semibold mb-6 text-gray-200">
          Lista de Productos
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="text-gray-400 border-b border-[#333] text-left">
                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("category")}>
                  Rubro {orden === "category" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("product_name")}>
                  Producto {orden === "product_name" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("brand")}>
                  Marca {orden === "brand" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3">Variedad</th>

                <th className="p-3">Contenido</th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("total_quantity")}>
                  Cantidad {orden === "total_quantity" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("fecha_ingreso")}>
                  Ingreso {orden === "fecha_ingreso" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("fecha_caducidad")}>
                  Vencimiento {orden === "fecha_caducidad" && (direccion === "asc" ? "▲" : "▼")}
                </th>
              </tr>
            </thead>

            <tbody>
              {variantesOrdenadas.map((v) => {
                const lote = v.batches[0] || null;

                return (
                  <tr
                    key={v.variant_id}
                    className="border-b border-[#2a2a2a] hover:bg-[#2a2a2a]/40 transition group"
                  >
                    {/* Rubro con gradiente + tooltip */}
                    <td className="p-3">
                      <span className="px-3 py-1 bg-orange-600/20 text-orange-400 rounded-full text-sm relative inline-block">
                        {v.category}

                        {v.batches.length > 0 && (
                          <div
                            className="
                              absolute 
                              left-1/2 
                              -translate-x-1/2 
                              -translate-y-full 
                              mt-1
                              opacity-0 
                              group-hover:opacity-100 
                              group-hover:translate-y-0
                              transition-all 
                              duration-300 
                              bg-[#111] 
                              text-gray-300 
                              px-3 py-2 
                              rounded-lg 
                              border 
                              border-[#333] 
                              shadow-xl 
                              z-50 
                              text-xs
                            "
                          >
                            <div
                              className="
                                absolute 
                                left-1/2 
                                top-full 
                                -translate-x-1/2 
                                w-0 h-0 
                                border-l-8 border-r-8 border-t-8 
                                border-l-transparent border-r-transparent border-t-[#111]
                              "
                            />

                            {v.batches.map((l) => (
                              <p key={l.id}>Lote: #{l.id}</p>
                            ))}
                          </div>
                        )}
                      </span>
                    </td>

                    <td className="p-3 font-medium text-gray-200">{v.product_name}</td>

                    <td className="p-3 text-gray-300">{v.brand}</td>

                    <td className="p-3 text-gray-300">{v.type_variety}</td>

                    <td className="p-3 text-gray-300">
                      {v.content_value ? `${v.content_value} ${v.content_unit}` : "Por definir"}
                    </td>

                    <td className="p-3">{v.total_quantity}</td>

                    <td className="p-3 text-gray-300">
                      {formatearFecha(lote?.arrival_date || null)}
                    </td>

                    <td className={`p-3 font-semibold ${estadoCaducidad(lote?.expiration_date || null)}`}>
                      {formatearFecha(lote?.expiration_date || null)}
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>
        </div>
      </div>
    </div>
  );
}
