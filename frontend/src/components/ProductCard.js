export default function ProductCard({ product, onClick }) {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow hover:shadow-lg cursor-pointer transition p-4 flex flex-col"
    >
      <img
        src={product.image || "/no-image.png"}
        alt={product.name}
        className="w-full h-48 object-cover rounded-xl"
      />
      <h3 className="text-lg font-semibold mt-3">{product.name}</h3>
      <p className="text-gray-500">{product.description}</p>
      <span className="mt-auto text-blue-600 font-medium">{product.status}</span>
    </div>
  );
}
