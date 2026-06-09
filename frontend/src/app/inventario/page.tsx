"use client";

import { useEffect, useState } from "react";

type Producto = {
  id: number;
  nombre: string;
  cantidad: number;
  marca: string;
  tipo: string;
  fecha_ingreso: string;
  fecha_caducidad: string;
};

export default function Inventario() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [busqueda, setBusqueda] = useState("");
  const [orden, setOrden] = useState<keyof Producto | null>(null);
  const [direccion, setDireccion] = useState<"asc" | "desc">("asc");

  const estadoCaducidad = (fecha: string) => {
    if (
      !fecha ||
      fecha.toLowerCase() === "por definir" ||
      fecha === "-" ||
      fecha.trim() === ""
    ) {
      return "text-gray-300"; // No aplicar color
    }

    const hoy = new Date();
    const cad = new Date(fecha);

    if (isNaN(cad.getTime())) return "text-gray-300";

    const diffTime = cad.getTime() - hoy.getTime();
    const dias = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (dias < 0) return "text-red-400";        // Vencido
    if (dias <= 30) return "text-yellow-400";   // Por vencer
    return "text-green-400";                    // En buen estado
  };


  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/inventario`)
      .then(res => res.json())
      .then(data => setProductos(data.productos));
  }, []);

  const productosFiltrados = productos.filter(p =>
    p.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
    p.marca.toLowerCase().includes(busqueda.toLowerCase()) ||
    p.tipo.toLowerCase().includes(busqueda.toLowerCase())
  );

  const ordenarPor = (columna: keyof Producto) => {
    if (orden === columna) {
      setDireccion(direccion === "asc" ? "desc" : "asc");
    } else {
      setOrden(columna);
      setDireccion("asc");
    }
  };

  const productosOrdenados = [...productosFiltrados].sort((a, b) => {
    if (!orden) return 0;

    const valorA = a[orden];
    const valorB = b[orden];

    // Ordenar fechas
    if (orden === "fecha_ingreso" || orden === "fecha_caducidad") {
      const fechaA = new Date(valorA).getTime();
      const fechaB = new Date(valorB).getTime();
      return direccion === "asc" ? fechaA - fechaB : fechaB - fechaA;
    }

    // Ordenar números
    if (orden === "cantidad") {
      return direccion === "asc"
        ? (valorA as number) - (valorB as number)
        : (valorB as number) - (valorA as number);
    }

    // Ordenar texto
    return direccion === "asc"
      ? String(valorA).localeCompare(String(valorB))
      : String(valorB).localeCompare(String(valorA));
  });

  return (
    <div className="space-y-10">

      {/* Título */}
      <h1 className="text-4xl font-bold tracking-tight text-orange-400">
        Inventario
      </h1>

      {/* Barra de búsqueda */}
      <input
        type="text"
        placeholder="Buscar producto, marca o tipo..."
        className="w-full p-4 rounded-xl bg-[#111] border border-[#2a2a2a] text-white focus:outline-none focus:ring-2 focus:ring-orange-500 transition"
        value={busqueda}
        onChange={e => setBusqueda(e.target.value)}
      />

      {/* Tarjetas de métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-gray-400 text-lg">Productos Totales</h3>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {productos.length}
          </p>
        </div>

        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-gray-400 text-lg">Categorías</h3>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {new Set(productos.map(p => p.tipo)).size}
          </p>
        </div>

        <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">
          <h3 className="text-gray-400 text-lg">Stock Total</h3>
          <p className="text-5xl font-bold text-orange-500 mt-2">
            {productos.reduce((acc, p) => acc + p.cantidad, 0)}
          </p>
        </div>

      </div>

      {/* Tabla moderna */}
      <div className="bg-[#1b1b1b] p-6 rounded-xl shadow-lg border border-[#2a2a2a]">

        <h2 className="text-2xl font-semibold mb-6 text-gray-200">
          Lista de Productos
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="text-gray-400 border-b border-[#333] text-left">

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("nombre")}>
                  Producto {orden === "nombre" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("cantidad")}>
                  Cantidad {orden === "cantidad" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("marca")}>
                  Marca {orden === "marca" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("tipo")}>
                  Tipo {orden === "tipo" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("fecha_ingreso")}>
                  Ingreso {orden === "fecha_ingreso" && (direccion === "asc" ? "▲" : "▼")}
                </th>

                <th className="p-3 cursor-pointer" onClick={() => ordenarPor("fecha_caducidad")}>
                  Caducidad {orden === "fecha_caducidad" && (direccion === "asc" ? "▲" : "▼")}
                </th>

              </tr>
            </thead>

            <tbody>
              {productosOrdenados.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-[#2a2a2a] hover:bg-[#2a2a2a] transition"
                >
                  <td className="p-3 font-medium text-gray-200">{p.nombre}</td>
                  <td className="p-3">{p.cantidad}</td>
                  <td className="p-3 text-gray-300">{p.marca}</td>
                  <td className="p-3">
                    <span className="px-3 py-1 bg-orange-600/20 text-orange-400 rounded-full text-sm">
                      {p.tipo}
                    </span>
                  </td>
                  <td className="p-3 text-gray-300">{p.fecha_ingreso}</td>
                  <td className={`p-3 font-semibold ${estadoCaducidad(p.fecha_caducidad)}`}>
                    {p.fecha_caducidad}
                  </td>
                </tr>
              ))}
            </tbody>

          </table>
        </div>
      </div>

    </div>
  );
}
