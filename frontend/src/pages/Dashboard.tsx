import {
  useListProductsApiProductsGet,
  useCreateProductApiProductsPost,
  type ProductResponse,
} from "../api/backend";
import ProductCard from "../components/ProductCard";
import { useState } from "react";

export default function Dashboard() {
  const { data: response, isLoading, error } = useListProductsApiProductsGet();
  const createMutation = useCreateProductApiProductsPost();
  const [name, setName] = useState("");
  const [targetPrice, setTargetPrice] = useState("");

  const products = response?.status === 200
    ? (response.data as ProductResponse[])
    : undefined;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate(
      {
        data: {
          name: name.trim(),
          target_price: targetPrice ? parseFloat(targetPrice) : null,
        },
      },
      {
        onSuccess: () => {
          setName("");
          setTargetPrice("");
        },
      }
    );
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Argos</h1>
        <p className="text-gray-500">Track product prices across retailers</p>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3 items-end mb-8">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder='e.g. "Sony WH-1000XM5"'
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        <div className="w-36">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Target price
          </label>
          <input
            type="number"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            placeholder="Optional"
            step="0.01"
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={createMutation.isPending || !name.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {createMutation.isPending ? "Adding..." : "Track"}
        </button>
      </form>

      {isLoading && <p className="text-gray-400">Loading products...</p>}

      {error !== undefined && error !== null && (
        <p className="text-red-500">
          Failed to load products: {String(error)}
        </p>
      )}

      {products && products.length === 0 && (
        <p className="text-gray-400 py-12">
          No products tracked yet. Add one above to get started.
        </p>
      )}

      {products && products.length > 0 && (
        <div className="grid gap-3">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
