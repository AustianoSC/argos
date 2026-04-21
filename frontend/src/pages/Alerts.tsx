import { Link } from "react-router-dom";
import {
  useListAlertsApiAlertsGet,
  type AlertResponse,
} from "../api/backend";

export default function Alerts() {
  const { data: response, isLoading, error } = useListAlertsApiAlertsGet();

  const alerts = response?.status === 200
    ? (response.data as AlertResponse[])
    : undefined;

  return (
    <div>
      <Link to="/" className="text-blue-600 hover:underline text-sm">
        &larr; Back to Dashboard
      </Link>

      <h1 className="text-2xl font-bold text-gray-900 mt-4 mb-6">Alerts</h1>

      {isLoading && <p className="text-gray-400">Loading alerts...</p>}

      {error && (
        <p className="text-red-500">
          Failed to load alerts: {String(error)}
        </p>
      )}

      {alerts && alerts.length === 0 && (
        <p className="text-gray-400 py-12">
          No alerts yet. Alerts will appear when prices drop below your targets.
        </p>
      )}

      {alerts && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="p-4 border border-gray-200 rounded-lg"
            >
              <div className="flex justify-between items-start">
                <p className="text-gray-800">{alert.message}</p>
                <span className="text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-700">
                  {alert.alert_type}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {new Date(alert.sent_at).toLocaleString()} via {alert.channel}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
