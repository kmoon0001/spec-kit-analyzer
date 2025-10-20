import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

interface HabitsDistributionChartProps {
  habitsData: Record<
    string,
    {
      habit_number: number;
      habit_name: string;
      percentage: number;
    }
  >;
}

const COLORS = ["#007acc", "#28a745", "#ffc107", "#dc3545", "#17a2b8"];

export const HabitsDistributionChart: React.FC<
  HabitsDistributionChartProps
> = ({ habitsData }) => {
  // Get top 5 habits by percentage
  const chartData = Object.entries(habitsData)
    .sort(([, a], [, b]) => b.percentage - a.percentage)
    .slice(0, 5)
    .map(([, habit]) => ({
      name: `Habit ${habit.habit_number}`,
      value: habit.percentage,
      fullName:
        habit.habit_name.length > 20
          ? `${habit.habit_name.substring(0, 20)}...`
          : habit.habit_name,
    }));

  if (chartData.length === 0 || chartData.every((item) => item.value === 0)) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "300px",
          color: "#666",
          fontSize: "14px",
        }}
      >
        No habit distribution data available
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height: "300px" }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) =>
              `${name}: ${(percent * 100).toFixed(1)}%`
            }
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, name: string, props: any) => [
              `${value.toFixed(1)}%`,
              props.payload.fullName,
            ]}
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontSize: "12px",
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
