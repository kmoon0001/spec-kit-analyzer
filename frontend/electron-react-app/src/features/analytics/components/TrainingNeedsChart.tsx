import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TrainingNeed {
  habit_name: string;
  percentage_of_findings: number;
  priority: 'high' | 'medium' | 'low';
  affected_users: number;
  training_focus: string;
}

interface TrainingNeedsChartProps {
  trainingNeeds: TrainingNeed[];
}

export const TrainingNeedsChart: React.FC<TrainingNeedsChartProps> = ({ trainingNeeds }) => {
  const chartData = trainingNeeds.slice(0, 10).map((need) => ({
    habit: need.habit_name.length > 30 ? `${need.habit_name.substring(0, 30)}...` : need.habit_name,
    percentage: need.percentage_of_findings,
    priority: need.priority,
    affected_users: need.affected_users,
  }));

  const getBarColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return '#dc3545';
      case 'medium':
        return '#ffc107';
      case 'low':
        return '#28a745';
      default:
        return '#6c757d';
    }
  };

  if (chartData.length === 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '400px',
        color: '#666',
        fontSize: '14px'
      }}>
        No training needs identified
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="horizontal"
          data={chartData}
          margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            type="number"
            stroke="#666"
            fontSize={12}
          />
          <YAxis
            type="category"
            dataKey="habit"
            stroke="#666"
            fontSize={10}
            width={90}
          />
          <Tooltip
            formatter={(value: number, name: string, props: any) => [
              `${value.toFixed(1)}%`,
              `Affected users: ${props.payload.affected_users}`
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Bar
            dataKey="percentage"
            fill={(entry: any) => getBarColor(entry.priority)}
          >
            {chartData.map((entry, index) => (
              <Bar key={`bar-${index}`} fill={getBarColor(entry.priority)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};