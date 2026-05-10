import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface Item {
  id: string;
  name: string;
  category: string;
  quantity: number;
  packed: boolean;
  is_essential: boolean;
  reason: string;
  source: 'template' | 'habit' | 'ai_suggestion';
}

export interface Checklist {
  checklist_id: string;
  trip_id: string;
  items: Item[];
  categories: string[];
  total_count: number;
  packed_count: number;
  completeness_score: number;
}

export interface Trip {
  trip_id: string;
  destination: string;
  duration: number;
  season: string;
  crowd_type: string;
  trip_type: string;
  start_date?: string;
  special_needs: string[];
  checklist?: Checklist;
  created_at: string;
}

export interface ChatResponse {
  response: string;
  intent: string;
  trip?: Trip;
  checklist?: Checklist;
  history: Message[];
}

export interface UserProfile {
  user_id: string;
  name: string;
  frequent_destinations: string[];
  preferred_season: string;
  travel_frequency: string;
  habits: Record<string, string[]>;
  health_info: string[];
  family_members: string[];
  pets: string[];
}

export const chatApi = {
  sendMessage: async (message: string, userId: string = 'default'): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', { message, user_id: userId });
    return response.data;
  },

  getCurrentTrip: async (userId: string = 'default'): Promise<Trip | null> => {
    try {
      const response = await api.get<Trip>(`/trip/current/${userId}`);
      return response.data;
    } catch {
      return null;
    }
  },

  getProfile: async (userId: string = 'default'): Promise<UserProfile | null> => {
    try {
      const response = await api.get<UserProfile>(`/profile/${userId}`);
      return response.data;
    } catch {
      return null;
    }
  },

  updateProfile: async (userId: string, key: string, value: string): Promise<void> => {
    await api.post('/profile/update', { user_id: userId, key, value });
  },

  manageItem: async (
    itemId: string,
    action: 'pack' | 'unpack' | 'delete',
    userId: string = 'default'
  ): Promise<Checklist | null> => {
    try {
      const response = await api.post<{ success: boolean; checklist: Checklist }>(
        `/item/${userId}`,
        { item_id: itemId, action, user_id: userId }
      );
      return response.data.checklist;
    } catch {
      return null;
    }
  },

  getTripHistory: async (userId: string = 'default'): Promise<Trip[]> => {
    try {
      const response = await api.get<{ trips: Trip[] }>(`/history/${userId}`);
      return response.data.trips;
    } catch {
      return [];
    }
  },
};

export default api;
