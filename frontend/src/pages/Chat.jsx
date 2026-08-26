import { useEffect, useRef, useState } from "react";
import {
  Send,
  Plus,
  MessageSquare,
  FileText,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  Filter,
} from "lucide-react";
import AppLayout from "../layouts/AppLayout.jsx";
import { chatApi, documentsApi } from "../services/api.js";

function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-slate-50">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <FileText size={14} className="text-slate-400 shrink-0" />
          <span className="text-sm font-medium truncate">{source.document_name}</span>
          <span className="text-xs text-slate-500 shrink-0">Page {source.page_number}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-brand-600 font-medium">{(source.score * 100).toFixed(0)}%</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>
      {expanded && <p className="text-xs text-slate-600 mt-2 leading-relaxed">{source.text}</p>}
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] md:max-w-2xl ${isUser ? "order-2" : ""}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap shadow-sm transition-all duration-200 ${
            isUser
              ? "bg-brand-500 text-white rounded-br-md shadow-brand-500/20"
              : "bg-white border border-slate-200 rounded-bl-md text-slate-700 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100"
          }`}
        >
          {message.content}
        </div>
        {!isUser && message.sources?.length > 0 && (
          <div className="mt-2 space-y-2">
            <p className="text-xs font-medium text-slate-500 dark:text-slate-300 px-1">Sources</p>
            {message.sources.map((s) => (
              <SourceCard key={s.chunk_id} source={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [showFilter, setShowFilter] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    chatApi.listConversations().then((res) => setConversations(res.data));
    documentsApi.list().then((res) =>
      setDocuments(res.data.documents.filter((d) => d.status === "processed"))
    );
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const openConversation = async (id) => {
    setMobileSidebarOpen(false);
    setActiveConversationId(id);
    const res = await chatApi.getConversation(id);
    setMessages(res.data);
  };

  const startNewConversation = () => {
    setMobileSidebarOpen(false);
    setActiveConversationId(null);
    setMessages([]);
    setError("");
  };

  const toggleDoc = (id) => {
    setSelectedDocIds((prev) => (prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]));
  };

  const handleSend = async () => {
    const question = input.trim();
    if (!question || sending) return;

    setError("");
    setInput("");
    setSending(true);

    const optimisticUserMsg = { id: `temp-${Date.now()}`, role: "user", content: question, sources: [] };
    setMessages((prev) => [...prev, optimisticUserMsg]);

    try {
      const res = await chatApi.ask({
        question,
        conversation_id: activeConversationId,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : null,
      });

      const wasNew = !activeConversationId;
      setActiveConversationId(res.data.conversation_id);
      setMessages((prev) => [
        ...prev,
        { id: `assistant-${Date.now()}`, role: "assistant", content: res.data.answer, sources: res.data.sources },
      ]);

      if (wasNew) {
        const convosRes = await chatApi.listConversations();
        setConversations(convosRes.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to get a response. Please try again.");
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMsg.id));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const sidebarContent = (
    <>
      <div className="p-3 border-b border-slate-200 bg-white dark:bg-slate-800">
        <button
          onClick={startNewConversation}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-500 text-white text-sm font-medium py-2.5 rounded-xl shadow-lg shadow-brand-500/20 transition-all duration-200 hover:-translate-y-0.5"
        >
          <Plus size={16} />
          New conversation
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => openConversation(c.id)}
            className={`w-full text-left px-3 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all duration-200 ${
              activeConversationId === c.id
                ? "bg-brand-50 text-brand-700 shadow-sm ring-1 ring-brand-100"
                : "hover:bg-slate-100 text-slate-700 dark:hover:bg-slate-700/50 dark:text-slate-200"
            }`}
          >
            <div className={`rounded-md p-1.5 ${activeConversationId === c.id ? "bg-brand-100 text-brand-600" : "bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300"}`}>
              <MessageSquare size={12} className="shrink-0" />
            </div>
            <span className="truncate">{c.title}</span>
          </button>
        ))}
      </div>
    </>
  );

  return (
    <AppLayout>
      <div className="flex h-[calc(100vh-56px)] md:h-full md:min-h-[calc(100vh-64px)]">
        {/* Desktop sidebar */}
        <div className="hidden md:flex w-80 border-r border-slate-200 bg-gradient-to-b from-white to-slate-50 flex-col shrink-0 dark:from-slate-800 dark:to-slate-900 dark:border-slate-700">
          {sidebarContent}
        </div>

        {/* Mobile conversation drawer */}
        {mobileSidebarOpen && (
          <div className="md:hidden fixed inset-0 z-40 flex">
            <div className="absolute inset-0 bg-black/30" onClick={() => setMobileSidebarOpen(false)} />
            <div className="relative w-[82%] max-w-sm bg-gradient-to-b from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 shadow-2xl border-r border-slate-200 dark:border-slate-700 animate-slide-up">
              {sidebarContent}
            </div>
          </div>
        )}

        {/* Main chat area */}
        <div className="flex-1 flex flex-col min-h-0 bg-slate-50 dark:bg-slate-900">
          <div className="h-16 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between px-3 md:px-6 shrink-0 bg-white dark:bg-slate-800 shadow-sm">
            <div className="flex items-center gap-2 md:hidden">
              <button
                onClick={() => setMobileSidebarOpen(true)}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-100 shadow-sm transition-transform active:scale-95"
                aria-label="Open conversations"
              >
                <MessageSquare size={16} />
              </button>
              <button
                onClick={startNewConversation}
                className="flex items-center gap-2 bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-500 text-white text-xs font-medium px-3 py-2 rounded-xl transition-all duration-200 shadow-lg shadow-brand-500/20"
              >
                <Plus size={14} />
                New
              </button>
            </div>

            <h1 className="font-semibold text-sm md:text-base truncate">
              {activeConversationId
                ? conversations.find((c) => c.id === activeConversationId)?.title || "Conversation"
                : "New conversation"}
            </h1>

            <div className="relative">
              <button
                onClick={() => setShowFilter((v) => !v)}
                className="flex items-center gap-2 text-xs md:text-sm border border-slate-300 dark:border-slate-600 rounded-xl px-2.5 md:px-3 py-1.5 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-100 transition-colors shadow-sm"
              >
                <Filter size={14} />
                {selectedDocIds.length === 0 ? "All documents" : `${selectedDocIds.length} selected`}
              </button>
              {showFilter && (
                <div className="absolute right-0 mt-2 w-64 md:w-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-lg p-2 z-10 max-h-72 overflow-y-auto">
                  {documents.length === 0 ? (
                    <p className="text-xs text-slate-500 p-2">No processed documents yet.</p>
                  ) : (
                    documents.map((d) => (
                      <label
                        key={d.id}
                        className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 text-sm cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDocIds.includes(d.id)}
                          onChange={() => toggleDoc(d.id)}
                        />
                        <span className="truncate">{d.filename}</span>
                      </label>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 pb-24 md:pb-6 min-h-0">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm text-center px-4">
                Ask a question about your uploaded documents.
              </div>
            ) : (
              messages.map((m) => <MessageBubble key={m.id} message={m} />)
            )}
            {sending && (
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Loader2 size={14} className="animate-spin" /> Thinking...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {error && (
            <div className="mx-3 md:mx-6 mb-2 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div className="p-3 md:p-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 pb-24 md:pb-4 shadow-[0_-8px_24px_rgba(15,23,42,0.04)]">
            <div className="flex items-end gap-2 max-w-3xl mx-auto">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="Ask a question about your documents..."
                className="flex-1 resize-none border border-slate-300 dark:border-slate-600 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm"
              />
              <button
                onClick={handleSend}
                disabled={sending || !input.trim()}
                className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white p-3 rounded-2xl shrink-0 shadow-lg shadow-brand-500/20 transition-all duration-200 hover:-translate-y-0.5"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
