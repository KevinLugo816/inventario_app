export default function Card({ title, value, children }: any) {
  return (
    <div className="bg-fondo2 border border-naranja2 rounded-xl p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-naranja mb-2">{title}</h3>
      {value && <p className="text-3xl font-bold text-naranja2">{value}</p>}
      {children}
    </div>
  );
}
