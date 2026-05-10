import { useState, useEffect, useRef } from 'react';
import { chatApi, Message, Trip } from './services/api';
import ChatInterface from './components/ChatInterface';
import ChecklistView from './components/ChecklistView';
import Sidebar from './components/Sidebar';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentTrip, setCurrentTrip] = useState<Trip | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [view, setView] = useState<'chat' | 'checklist'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (view === 'chat') {
      scrollToBottom();
    }
  }, [view]);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const trip = await chatApi.getCurrentTrip();
        if (trip) {
          setCurrentTrip(trip);
        }
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };
    loadInitialData();
  }, []);

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    setIsLoading(true);
    try {
      const response = await chatApi.sendMessage(message);

      setMessages(response.history);

      if (response.trip) {
        setCurrentTrip(response.trip);
      }
      if (response.checklist && !response.trip) {
        setCurrentTrip(prev => prev ? { ...prev, checklist: response.checklist! } : null);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '抱歉，服务暂时不可用，请稍后重试。',
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleItemToggle = async (itemId: string, packed: boolean) => {
    try {
      const updatedChecklist = await chatApi.manageItem(
        itemId,
        packed ? 'pack' : 'unpack'
      );
      if (updatedChecklist && currentTrip) {
        setCurrentTrip({ ...currentTrip, checklist: updatedChecklist });
      }
    } catch (error) {
      console.error('Failed to update item:', error);
    }
  };

  const handleItemDelete = async (itemId: string) => {
    try {
      const updatedChecklist = await chatApi.manageItem(itemId, 'delete');
      if (updatedChecklist && currentTrip) {
        setCurrentTrip({ ...currentTrip, checklist: updatedChecklist });
      }
    } catch (error) {
      console.error('Failed to delete item:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <Sidebar currentView={view} onViewChange={setView} trip={currentTrip} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">旅睿</h1>
              <p className="text-sm text-gray-500">你的私人旅行管家</p>
            </div>
            {currentTrip && (
              <div className="text-right">
                <p className="font-medium text-gray-700">
                  {currentTrip.destination} · {currentTrip.duration}日游
                </p>
                <p className="text-sm text-gray-500">
                  {currentTrip.checklist?.total_count || 0} 件物品
                </p>
              </div>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-hidden">
          {view === 'chat' ? (
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              messagesEndRef={messagesEndRef}
            />
          ) : (
            <ChecklistView
              trip={currentTrip}
              onItemToggle={handleItemToggle}
              onItemDelete={handleItemDelete}
              onBack={() => setView('chat')}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;