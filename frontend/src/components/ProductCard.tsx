import { Link } from "react-router-dom";
import type { ProductResponse } from "../api/backend";

interface Props {
  product: ProductResponse;
}

export default function ProductCard({ product }: Props) {
  return (
    <Link
      to={`/products/${product.id}`}
      className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-medium text-gray-900">{product.name}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {product.currency}{" "}
            {product.target_price
              ? `Target: $${product.target_price}`
              : "No target set"}
          </p>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded-full ${
            product.is_active
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {product.is_active ? "Active" : "Inactive"}
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        Added {new Date(product.created_at).toLocaleDateString()}
      </p>
    </Link>
  );
}
