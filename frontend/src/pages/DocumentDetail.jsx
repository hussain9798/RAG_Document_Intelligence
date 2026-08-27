import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, FileText } from "lucide-react";
import AppLayout from "../layouts/AppLayout.jsx";
import { documentsApi } from "../services/api.js";

const STATUS_STYLES = {
  uploaded: "bg-slate-100 text-slate-700",
  processing: "bg-amber-100 text-amber-700",
  processed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

export default function DocumentDetail() {
  const { id } = useParams();
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    documentsApi
      .get(id)
      .then((res) => setDoc(res.data))
      .catch(() => setError("Document not found."));
  }, [id]);

  return (
    <AppLayout>
      <div className="app-page max-w-3xl">
        <Link to="/documents" className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-6">
          <ArrowLeft size={16} /> Back to documents
        </Link>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {doc && (
          <div className="premium-card p-5 sm:p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-100 to-indigo-100 flex items-center justify-center">
                <FileText size={20} className="text-indigo-600" />
              </div>
              <div>
                <h1 className="font-semibold">{doc.filename}</h1>
                <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_STYLES[doc.status]}`}>
                  {doc.status}
                </span>
              </div>
            </div>

            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-slate-500">Uploaded</dt>
                <dd className="font-medium">{new Date(doc.created_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Page count</dt>
                <dd className="font-medium">{doc.page_count ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Size</dt>
                <dd className="font-medium">{(doc.file_size / 1024).toFixed(0)} KB</dd>
              </div>
              <div>
                <dt className="text-slate-500">Last updated</dt>
                <dd className="font-medium">{new Date(doc.updated_at).toLocaleString()}</dd>
              </div>
            </dl>

            {doc.status === "failed" && doc.error_message && (
              <div className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {doc.error_message}
              </div>
            )}

            <div className="mt-6">
              <Link
                to="/chat"
                className="premium-button inline-block text-sm font-medium px-4 py-2.5 rounded-xl"
              >
                Ask a question about this document
              </Link>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
