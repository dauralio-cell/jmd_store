export default function Banner() {
  return (
    <div className="relative w-full h-64 bg-cover bg-center" style={{ backgroundImage: "url('/banner.jpg')" }}>
      <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
        <h1 className="text-white text-3xl md:text-5xl font-bold">DENE Store</h1>
      </div>
    </div>
  );
}
