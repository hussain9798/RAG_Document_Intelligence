import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, CheckCircle2, MessageSquare, Upload } from "lucide-react";
import AppLayout from "../layouts/AppLayout.jsx";
import { documentsApi, chatApi } from "../services/api.js";

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="premium-card p-5 flex items-center gap-4">
      <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-100 to-indigo-100 flex items-center justify-center shrink-0">
        <Icon size={20} className="text-indigo-600" />
      </div>
      <div>
        <p className="text-2xl font-semibold">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([documentsApi.list(), chatApi.listConversations()])
      .then(([docsRes, convosRes]) => {
        setDocuments(docsRes.data.documents);
        setConversations(convosRes.data);
      })
      .catch(() => setError("Failed to load dashboard data."))
      .finally(() => setLoading(false));
  }, []);

  const processedCount = documents.filter((d) => d.status === "processed").length;

  return (
    <AppLayout>
      <div className="app-page">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold">Dashboard</h1>
            <p className="text-sm text-slate-500 mt-1">Overview of your documents and conversations.</p>
          </div>
          <Link
            to="/documents"
            className="premium-button flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-xl"
          >
            <Upload size={16} />
            Upload document
          </Link>
        </div>

        {error && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-6">{error}</div>}

        {loading ? (
          <p className="text-slate-500">Loading...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <StatCard icon={FileText} label="Total documents" value={documents.length} />
              <StatCard icon={CheckCircle2} label="Processed documents" value={processedCount} />
              <StatCard icon={MessageSquare} label="Total conversations" value={conversations.length} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="premium-card p-5">
                <h2 className="font-medium mb-4">Recent documents</h2>
                {documents.length === 0 ? (
                  <p className="text-sm text-slate-500">No documents uploaded yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {documents.slice(0, 5).map((d) => (
                      <li key={d.id} className="flex items-center justify-between text-sm">
                        <span className="truncate max-w-[65%]">{d.filename}</span>
                        <span className="text-xs text-slate-500 capitalize">{d.status}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="premium-card p-5">
                <h2 className="font-medium mb-4">Recent conversations</h2>
                {conversations.length === 0 ? (
                  <p className="text-sm text-slate-500">No conversations yet.</p>
                ) : (
                  <ul className="space-y-3">
                    {conversations.slice(0, 5).map((c) => (
                      <li key={c.id} className="text-sm truncate">
                        {c.title}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}
