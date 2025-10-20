import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8001";

export interface HabitProgression {
  overall_progress: {
    percentage: number;
    status: string;
  };
  current_streak: number;
  improvement_rate: number;
  habit_breakdown: Record<
    string,
    {
      habit_number: number;
      habit_name: string;
      percentage: number;
      mastery_level: "Mastered" | "Proficient" | "Developing" | "Needs Focus";
    }
  >;
  achievements: Array<{
    id: string;
    title: string;
    description: string;
    earned_date: string;
    badge_type: string;
  }>;
  recommendations: Array<{
    title: string;
    description: string;
    priority: "high" | "medium" | "low";
    action_items: string[];
  }>;
  current_goals: Array<{
    title: string;
    description: string;
    progress: number;
    target_date: string;
  }>;
}

export interface HabitsAchievements {
  recent_achievements: Array<{
    id: string;
    title: string;
    description: string;
    earned_date: string;
    badge_type: string;
  }>;
  total_achievements: number;
  achievement_categories: Record<string, number>;
}

export const fetchHabitsProgression = async (): Promise<HabitProgression> => {
  const response = await axios.get(`${API_BASE_URL}/habits/progression`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
    },
  });
  return response.data;
};

export const fetchHabitsAchievements =
  async (): Promise<HabitsAchievements> => {
    const response = await axios.get(`${API_BASE_URL}/habits/achievements`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
      },
    });
    return response.data;
  };
