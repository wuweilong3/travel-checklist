import { useState, RefObject } from 'react';
import { Message } from '../services/api';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  messagesEndRef: RefObject<HTMLDivElement>;
}

const QuickActions = [
  { label: '🏖️ 去海边度假', text: '我要去海边度假，5天' },
  { label: '🏔️ 登山徒步', text: '我想去爬山，徒步3天' },
  { label: '👨‍👩‍👧 家庭出游', text: '带家人去厦门旅游，4天' },
  { label: '💼 商务出差', text: '下周一要去北京出差，3天' },
];

export default function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  messagesEndRef,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleQuickAction = (text: string) => {
    onSendMessage(text);
  };

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✈️</div>
            <h2 className="text-2xl font-bold text-gray-700 mb-2">
              你好！我是旅睿
            </h2>
            <p className="text-gray-500 mb-8">
              告诉我你要去哪里旅行，我来帮你准备完美的清单
            </p>

            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
              {QuickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleQuickAction(action.text)}
                  className="p-3 bg-white rounded-xl shadow-sm border hover:shadow-md transition-all text-left"
                >
                  <span className="text-sm">{action.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white rounded-br-md'
                  : 'bg-white text-gray-800 rounded-bl-md shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.timestamp && (
                <div
                  className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl rounded-bl-md shadow-sm px-4 py-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 bg-white border-t">
        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="告诉我你要去哪里旅行..."
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-6 py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
