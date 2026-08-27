import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, CheckCircle2, MessageSquare, Upload } from "lucide-react";
import AppLayout from "../layouts/AppLayout.jsx";
import { documentsApi, chatApi } from "../services/api.js";

function StatCard({ icon: Icon, label, value, colors }) {
  return (
    <div className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br ${colors} p-5 text-white shadow-xl transition duration-300 hover:-translate-y-1 hover:shadow-2xl`}>
      <div className="absolute -right-5 -top-8 h-28 w-28 rounded-full bg-white/15 blur-2xl transition group-hover:scale-150" />
      <div className="relative flex items-center gap-4">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/20 backdrop-blur">
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-semibold">{value}</p>
        <p className="text-sm text-white/75">{label}</p>
      </div>
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
        <div className="mb-7 rounded-3xl bg-gradient-to-r from-indigo-600 via-violet-600 to-fuchsia-600 p-5 text-white shadow-xl shadow-indigo-500/20 sm:p-7">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div>
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-cyan-200">Workspace overview</p>
            <h1 className="text-2xl font-bold sm:text-3xl">Your intelligence hub</h1>
            <p className="mt-1 text-sm text-indigo-100">Everything you need to turn documents into decisions.</p>
          </div>
          <Link
            to="/documents"
            className="premium-button flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-xl"
          >
            <Upload size={16} />
            Upload document
          </Link>
          </div>
        </div>

        {error && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-6">{error}</div>}

        {loading ? (
          <p className="text-slate-500">Loading...</p>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              <StatCard icon={FileText} label="Total documents" value={documents.length} colors="from-cyan-500 to-blue-600" />
              <StatCard icon={CheckCircle2} label="Processed documents" value={processedCount} colors="from-emerald-500 to-teal-600" />
              <StatCard icon={MessageSquare} label="Total conversations" value={conversations.length} colors="from-fuchsia-500 to-violet-600" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="premium-card p-5">
                <h2 className="mb-4 flex items-center gap-2 font-semibold"><span className="h-2 w-2 rounded-full bg-cyan-400" />Recent documents</h2>
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
                <h2 className="mb-4 flex items-center gap-2 font-semibold"><span className="h-2 w-2 rounded-full bg-fuchsia-400" />Recent conversations</h2>
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
