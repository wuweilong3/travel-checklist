import { Trip } from '../services/api';

interface SidebarProps {
  currentView: 'chat' | 'checklist';
  onViewChange: (view: 'chat' | 'checklist') => void;
  trip: Trip | null;
}

export default function Sidebar({ currentView, onViewChange, trip }: SidebarProps) {
  return (
    <aside className="w-64 bg-white border-r flex flex-col">
      <div className="p-4 border-b">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
            <span className="text-xl">🧳</span>
          </div>
          <div>
            <h2 className="font-bold text-gray-800">旅睿</h2>
            <p className="text-xs text-gray-500">TravelWise</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        <button
          onClick={() => onViewChange('chat')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
            currentView === 'chat'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <span className="text-xl">💬</span>
          <span className="font-medium">聊天</span>
        </button>

        <button
          onClick={() => onViewChange('checklist')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-colors ${
            currentView === 'checklist'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <span className="text-xl">📋</span>
          <span className="font-medium">清单</span>
          {trip?.checklist && (
            <span className="ml-auto px-2 py-0.5 bg-blue-100 text-blue-600 text-xs rounded-full">
              {trip.checklist.total_count}
            </span>
          )}
        </button>
      </nav>

      <div className="p-4 border-t">
        <div className="text-xs text-gray-500 space-y-1">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-green-500 rounded-full" />
            <span>服务正常</span>
          </div>
          <div>v1.0.0 MVP</div>
        </div>
      </div>
    </aside>
  );
}
