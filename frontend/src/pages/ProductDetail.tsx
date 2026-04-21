import { useParams, Link } from "react-router-dom";
import {
  useGetProductApiProductsProductIdGet,
  useTriggerCheckApiProductsProductIdCheckPost,
  type ProductDetailResponse,
} from "../api/backend";
import PriceChart from "../components/PriceChart";

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: response, isLoading, error } =
    useGetProductApiProductsProductIdGet(id!);
  const triggerCheck = useTriggerCheckApiProductsProductIdCheckPost();

  if (isLoading) return <p className="text-gray-400">Loading...</p>;
  if (error)
    return <p className="text-red-500">Error: {String(error)}</p>;
  if (!response || response.status !== 200)
    return <p className="text-gray-400">Product not found</p>;

  const product = response.data as ProductDetailResponse;

  return (
    <div>
      <Link to="/" className="text-blue-600 hover:underline text-sm">
        &larr; Back to Dashboard
      </Link>

      <div className="mt-4 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
          <p className="text-gray-500 mt-1">
            {product.target_price
              ? `Target: $${product.target_price} ${product.currency}`
              : "No target price set"}
          </p>
        </div>
        <button
          onClick={() => triggerCheck.mutate({ productId: product.id })}
          disabled={triggerCheck.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {triggerCheck.isPending ? "Checking..." : "Check Now"}
        </button>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Price History
        </h2>
        <PriceChart
          priceHistory={product.price_history ?? []}
          sources={product.sources ?? []}
        />
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Sources ({(product.sources ?? []).length})
        </h2>
        {(product.sources ?? []).length === 0 ? (
          <p className="text-gray-400">
            No sources found yet. The pipeline may still be running.
          </p>
        ) : (
          <div className="space-y-2">
            {product.sources!.map((source) => (
              <div
                key={source.id}
                className="flex justify-between items-center p-3 border border-gray-200 rounded-lg"
              >
                <div>
                  <span className="font-medium text-gray-800">
                    {source.domain}
                  </span>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm ml-2"
                  >
                    Visit
                  </a>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">
                    Confidence: {(source.match_confidence * 100).toFixed(0)}%
                  </span>
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${
                      source.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {source.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
