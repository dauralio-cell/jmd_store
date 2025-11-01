export default function ProductModal({ product, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-2xl shadow-lg max-w-md w-full relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-xl"
        >
          ✕
        </button>
        <img
          src={product.image || "/no-image.png"}
          alt={product.name}
          className="w-full h-60 object-cover rounded-xl"
        />
        <h2 className="text-2xl font-bold mt-4">{product.name}</h2>
        <p className="text-gray-600 mt-2">{product.description}</p>
        <p className="text-sm text-gray-500 mt-1">Размеры: {product.sizes}</p>
        <p className="text-blue-600 font-medium mt-3">Статус: {product.status}</p>
      </div>
    </div>
  );
}
