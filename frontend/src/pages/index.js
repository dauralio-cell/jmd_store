import { useState, useEffect } from "react";
import Banner from "@/components/Banner";
import ProductCard from "@/components/ProductCard";
import ProductModal from "@/components/ProductModal";

export default function Home() {
  const [catalog, setCatalog] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    fetch("/data/catalog.json")
      .then((res) => res.json())
      .then((data) => setCatalog(data))
      .catch((err) => console.error("Ошибка загрузки JSON:", err));
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      <Banner />
      <div className="container mx-auto px-4 py-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {catalog.map((item, index) => (
          <ProductCard key={index} product={item} onClick={() => setSelectedProduct(item)} />
        ))}
      </div>

      {selectedProduct && (
        <ProductModal product={selectedProduct} onClose={() => setSelectedProduct(null)} />
      )}
    </div>
  );
}
