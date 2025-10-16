import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DisciplineChartProps {
  disciplineData: Record<string, {
    avg_compliance_score: number;
    user_count: number;
  }>;
}

export const DisciplineChart: React.FC<DisciplineChartProps> = ({ disciplineData }) => {
  const chartData = Object.entries(disciplineData).map(([discipline, data]) => ({
    discipline: discipline.toUpperCase(),
    'Avg Compliance Score': Math.round(data.avg_compliance_score),
    'User Count': data.user_count,
  }));

  if (chartData.length === 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '300px',
        color: '#666',
        fontSize: '14px'
      }}>
        No discipline data available
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="discipline"
            stroke="#666"
            fontSize={12}
          />
          <YAxis
            yAxisId="left"
            stroke="#007acc"
            fontSize={12}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#ffc107"
            fontSize={12}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
          <Legend />
          <Bar
            yAxisId="left"
            dataKey="Avg Compliance Score"
            fill="#007acc"
            name="Avg Compliance Score (%)"
          />
          <Bar
            yAxisId="right"
            dataKey="User Count"
            fill="#ffc107"
            name="User Count"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};