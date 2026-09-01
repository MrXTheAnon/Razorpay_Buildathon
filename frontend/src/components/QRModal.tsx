import React, { useState } from 'react';
import { X, QrCode, Send, Smartphone, Check } from 'lucide-react';

interface QRModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendToChatId: (chatId: string) => void;
  defaultChatId: string;
}

export const QRModal: React.FC<QRModalProps> = ({
  isOpen,
  onClose,
  onSendToChatId,
  defaultChatId,
}) => {
  const [chatId, setChatId] = useState(defaultChatId);
  const [sent, setSent] = useState(false);

  if (!isOpen) return null;

  const handleSend = () => {
    if (!chatId.trim()) return;
    onSendToChatId(chatId.trim());
    setSent(true);
    setTimeout(() => setSent(false), 3000);
  };

  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://t.me/razor_loop_bot`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white border border-[#d8d0c2] rounded-3xl w-full max-w-md p-6 modal-shadow flex flex-col items-center text-center relative overflow-hidden font-sans">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg cream-btn text-stone-500 hover:text-stone-900 transition cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="w-11 h-11 rounded-xl cream-well flex items-center justify-center text-sky-700 mb-3">
          <QrCode className="w-6 h-6" />
        </div>

        <h2 className="text-base font-bold text-stone-900 font-mono uppercase tracking-wider">
          Connect Your Mobile Phone
        </h2>
        <p className="text-xs text-stone-600 mt-1 max-w-xs leading-relaxed font-medium">
          Scan the QR code to open <strong>@razor_loop_bot</strong> on Telegram. Click <code>/start</code> to pair.
        </p>

        {/* QR Code Container */}
        <div className="my-5 p-3.5 bg-[#fbf9f4] border border-[#e5dec9] rounded-2xl shadow-sm">
          <img
            src={qrUrl}
            alt="Telegram QR Code"
            className="w-44 h-44 object-contain rounded-lg"
          />
        </div>

        <div className="text-xs text-stone-600 mb-4 font-mono">
          Or search: <strong className="text-sky-800 font-bold">@razor_loop_bot</strong> on Telegram
        </div>

        {/* Custom Chat ID Input */}
        <div className="w-full cream-well p-4 rounded-xl text-left space-y-2.5">
          <label className="text-[11px] text-stone-700 font-semibold flex items-center justify-between font-mono">
            <span className="flex items-center gap-1.5">
              <Smartphone className="w-3.5 h-3.5 text-sky-700" />
              <span>Target Telegram Chat ID:</span>
            </span>
            <span className="text-[10px] text-emerald-800 font-semibold bg-emerald-100 px-2 py-0.5 rounded">
              Default: 6*******4
            </span>
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              placeholder="Enter your chat id"
              className="flex-1 bg-white border border-[#d6ccbe] rounded-lg px-3 py-2 text-xs text-stone-900 focus:outline-none focus:border-stone-800 font-mono shadow-inner"
            />
            <button
              onClick={handleSend}
              className="px-3.5 py-2 bg-stone-900 hover:bg-stone-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-md"
            >
              {sent ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Send className="w-3.5 h-3.5" />}
              <span>{sent ? 'Sent!' : 'Send Test'}</span>
            </button>
          </div>
          {sent && (
            <p className="text-[11px] text-emerald-800 font-mono font-medium">
              ✓ Recovery card dispatched to Telegram! Check your phone.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
