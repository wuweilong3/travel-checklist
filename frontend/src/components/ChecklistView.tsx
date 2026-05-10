import { useState } from 'react';
import { Trip, Item } from '../services/api';

interface ChecklistViewProps {
  trip: Trip | null;
  onItemToggle: (itemId: string, packed: boolean) => void;
  onItemDelete: (itemId: string) => void;
  onBack: () => void;
}

type TabType = 'all' | 'packed' | 'unpacked';

export default function ChecklistView({
  trip,
  onItemToggle,
  onItemDelete,
  onBack,
}: ChecklistViewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('all');

  if (!trip || !trip.checklist) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <div className="text-6xl mb-4">📋</div>
        <p className="mb-4">还没有创建清单</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          去聊天创建
        </button>
      </div>
    );
  }

  const { items, categories, total_count, packed_count } = trip.checklist;
  const progress = total_count > 0 ? (packed_count / total_count) * 100 : 0;

  const filteredItems = items.filter((item) => {
    if (activeTab === 'packed') return item.packed;
    if (activeTab === 'unpacked') return !item.packed;
    return true;
  });

  const groupedItems = categories.reduce((acc, category) => {
    acc[category] = filteredItems.filter((item) => item.category === category);
    return acc;
  }, {} as Record<string, Item[]>);

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 bg-white border-b">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800"
          >
            <span className="mr-1">←</span> 返回聊天
          </button>
          <div className="text-sm text-gray-500">
            {packed_count}/{total_count} 已打包
          </div>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex space-x-2">
          {(['all', 'packed', 'unpacked'] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab === 'all' ? '全部' : tab === 'packed' ? '已打包' : '未打包'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {Object.entries(groupedItems).map(([category, categoryItems]) => {
          if (categoryItems.length === 0) return null;

          const packedInCategory = categoryItems.filter((i) => i.packed).length;

          return (
            <div key={category}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-800">{category}</h3>
                <span className="text-sm text-gray-500">
                  {packedInCategory}/{categoryItems.length}
                </span>
              </div>

              <div className="space-y-2">
                {categoryItems.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-center p-3 bg-white rounded-xl shadow-sm border transition-all ${
                      item.packed ? 'opacity-60' : ''
                    }`}
                  >
                    <button
                      onClick={() => onItemToggle(item.id, !item.packed)}
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center mr-3 transition-colors ${
                        item.packed
                          ? 'bg-green-500 border-green-500 text-white'
                          : 'border-gray-300 hover:border-blue-500'
                      }`}
                    >
                      {item.packed && '✓'}
                    </button>

                    <div className="flex-1">
                      <div className={`font-medium ${item.packed ? 'line-through text-gray-500' : 'text-gray-800'}`}>
                        {item.name}
                      </div>
                      {item.reason && (
                        <div className="text-xs text-gray-500">{item.reason}</div>
                      )}
                    </div>

                    {item.quantity > 1 && (
                      <div className="px-2 py-1 bg-gray-100 rounded text-sm text-gray-600 mr-2">
                        ×{item.quantity}
                      </div>
                    )}

                    {item.source === 'habit' && (
                      <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded mr-2">
                        习惯
                      </span>
                    )}

                    <button
                      onClick={() => onItemDelete(item.id)}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {filteredItems.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {activeTab === 'packed' ? '还没有打包任何物品' : '没有未打包的物品'}
          </div>
        )}
      </div>
    </div>
  );
}
