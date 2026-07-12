"use client";

import { XMarkIcon } from "@heroicons/react/24/solid";

type Props = {
  variante: any;
  form: any;
  setForm: (v: any) => void;
  onClose: () => void;
  onSave: () => void;
};

export default function EditarVariante({
  variante,
  form,
  setForm,
  onClose,
  onSave,
}: Props) {
  if (!variante) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#1b1b1b] p-6 rounded-xl w-[420px] border border-[#2a2a2a] shadow-xl relative">

        {/* Botón cerrar */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-200 transition"
        >
          <XMarkIcon className="h-6 w-6" />
        </button>

        <h2 className="text-xl font-semibold text-orange-400 mb-4">
          Editar {form.product_name}
        </h2>

        <div className="space-y-4">
          {[
            ["product_name", "Producto"],
            ["category", "Rubro"],
            ["brand", "Marca"],
            ["type_variety", "Variedad"],
            ["content_value", "Contenido (valor)"],
            ["content_unit", "Unidad"],
          ].map(([campo, label]) => (
            <div key={campo}>
              <label className="text-gray-300 text-sm">{label}</label>
              <input
                type="text"
                value={form[campo] ?? ""}
                onChange={(e) =>
                  setForm({ ...form, [campo]: e.target.value })
                }
                className="w-full p-2 rounded bg-[#111] border border-[#333] text-white focus:ring-2 focus:ring-orange-500"
              />
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Cancelar
          </button>

          <button
            onClick={onSave}
            className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
}
