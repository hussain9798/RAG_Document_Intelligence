import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Upload, FileText, Trash2, Search, Loader2, AlertCircle } from "lucide-react";
import AppLayout from "../layouts/AppLayout.jsx";
import { documentsApi } from "../services/api.js";

const STATUS_STYLES = {
  uploaded: "bg-slate-100 text-slate-700",
  processing: "bg-amber-100 text-amber-700",
  processed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef(null);
  const pollRef = useRef(null);

  const loadDocuments = useCallback(async () => {
    try {
      const res = await documentsApi.list();
      setDocuments(res.data.documents);
      setError("");
    } catch {
      setError("Failed to load documents.");
    }
  }, []);

  useEffect(() => {
    loadDocuments().finally(() => setLoading(false));
  }, [loadDocuments]);

  // Poll while any document is still processing, so status updates without a manual refresh.
  useEffect(() => {
    const hasPending = documents.some((d) => d.status === "uploaded" || d.status === "processing");
    if (hasPending && !pollRef.current) {
      pollRef.current = setInterval(loadDocuments, 3000);
    } else if (!hasPending && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [documents, loadDocuments]);

  const handleFiles = async (files) => {
    const file = files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      return;
    }
    setUploadError("");
    setUploading(true);
    try {
      await documentsApi.upload(file);
      await loadDocuments();
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this document and all associated data?")) return;
    try {
      await documentsApi.remove(id);
      setDocuments((docs) => docs.filter((d) => d.id !== id));
    } catch {
      setError("Failed to delete document.");
    }
  };

  const filtered = documents.filter((d) => d.filename.toLowerCase().includes(search.toLowerCase()));

  return (
    <AppLayout>
      <div className="app-page">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold">Documents</h1>
          <p className="text-sm text-slate-500 mt-1">Upload PDFs and manage your document library.</p>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`mb-6 border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
            dragging ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30" : "border-slate-300 bg-white/75 dark:bg-slate-800/75 hover:border-indigo-400"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          {uploading ? (
            <>
              <Loader2 size={28} className="animate-spin text-brand-500 mb-3" />
              <p className="text-sm text-slate-600">Uploading...</p>
            </>
          ) : (
            <>
              <Upload size={28} className="text-slate-400 mb-3" />
              <p className="text-sm font-medium">Drag & drop a PDF, or click to browse</p>
              <p className="text-xs text-slate-500 mt-1">Processing continues in the background after upload.</p>
            </>
          )}
        </div>

        {uploadError && (
          <div className="mb-6 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <AlertCircle size={16} /> {uploadError}
          </div>
        )}

        <div className="relative mb-4 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="premium-input w-full rounded-xl pl-9 pr-3 py-2 text-sm"
          />
        </div>

        <div className="premium-card overflow-hidden">
          {loading ? (
            <p className="p-6 text-sm text-slate-500">Loading documents...</p>
          ) : error ? (
            <p className="p-6 text-sm text-red-600">{error}</p>
          ) : filtered.length === 0 ? (
            <div className="p-10 text-center text-slate-500">
              <FileText size={28} className="mx-auto mb-3 text-slate-300" />
              <p className="text-sm">No documents found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-200">
                  <th className="px-3 sm:px-5 py-3 font-medium">Name</th>
                  <th className="px-3 sm:px-5 py-3 font-medium">Pages</th>
                  <th className="px-3 sm:px-5 py-3 font-medium">Size</th>
                  <th className="px-3 sm:px-5 py-3 font-medium">Status</th>
                  <th className="px-3 sm:px-5 py-3 font-medium">Uploaded</th>
                  <th className="px-3 sm:px-5 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-3 sm:px-5 py-3">
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-slate-400 shrink-0" />
                        <span className="truncate max-w-xs">{doc.filename}</span>
                      </div>
                      {doc.status === "failed" && doc.error_message && (
                        <p className="text-xs text-red-600 mt-1">{doc.error_message}</p>
                      )}
                    </td>
                    <td className="px-3 sm:px-5 py-3">{doc.page_count ?? "—"}</td>
                    <td className="px-3 sm:px-5 py-3">{formatSize(doc.file_size)}</td>
                    <td className="px-3 sm:px-5 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${STATUS_STYLES[doc.status]}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-3 sm:px-5 py-3 text-slate-500">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="px-3 sm:px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Link
                          to={`/documents/${doc.id}`}
                          title="View"
                          className="text-slate-600 dark:text-slate-200 hover:text-brand-600 text-xs font-medium px-2 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="text-slate-600 dark:text-slate-200 hover:text-red-600 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-600/10"
                          title="Delete"
                          aria-label="Delete document"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
