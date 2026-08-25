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
      <div className={`max-w-2xl ${isUser ? "order-2" : ""}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${
            isUser ? "bg-brand-500 text-white rounded-br-sm" : "bg-white border border-slate-200 rounded-bl-sm"
          }`}
        >
          {message.content}
        </div>
        {!isUser && message.sources?.length > 0 && (
          <div className="mt-2 space-y-2">
            <p className="text-xs font-medium text-slate-500 px-1">Sources</p>
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
    setActiveConversationId(id);
    const res = await chatApi.getConversation(id);
    setMessages(res.data);
  };

  const startNewConversation = () => {
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

  return (
    <AppLayout>
      <div className="h-full flex">
        {/* Conversation sidebar */}
        <div className="w-72 border-r border-slate-200 bg-white flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-200">
            <button
              onClick={startNewConversation}
              className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium py-2.5 rounded-lg"
            >
              <Plus size={16} />
              New conversation
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => openConversation(c.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm flex items-center gap-2 ${
                  activeConversationId === c.id ? "bg-brand-50 text-brand-700" : "hover:bg-slate-100 text-slate-700"
                }`}
              >
                <MessageSquare size={14} className="shrink-0" />
                <span className="truncate">{c.title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Main chat area */}
        <div className="flex-1 flex flex-col">
          <div className="h-16 border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
            <h1 className="font-medium">
              {activeConversationId
                ? conversations.find((c) => c.id === activeConversationId)?.title || "Conversation"
                : "New conversation"}
            </h1>
            <div className="relative">
              <button
                onClick={() => setShowFilter((v) => !v)}
                className="flex items-center gap-2 text-sm border border-slate-300 rounded-lg px-3 py-1.5 hover:bg-slate-50"
              >
                <Filter size={14} />
                {selectedDocIds.length === 0 ? "All documents" : `${selectedDocIds.length} selected`}
              </button>
              {showFilter && (
                <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-lg p-2 z-10 max-h-72 overflow-y-auto">
                  {documents.length === 0 ? (
                    <p className="text-xs text-slate-500 p-2">No processed documents yet.</p>
                  ) : (
                    documents.map((d) => (
                      <label
                        key={d.id}
                        className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-slate-50 text-sm cursor-pointer"
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

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">
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
            <div className="mx-6 mb-2 flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <div className="p-4 border-t border-slate-200">
            <div className="flex items-end gap-2 max-w-3xl mx-auto">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="Ask a question about your documents..."
                className="flex-1 resize-none border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <button
                onClick={handleSend}
                disabled={sending || !input.trim()}
                className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white p-3 rounded-xl shrink-0"
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
