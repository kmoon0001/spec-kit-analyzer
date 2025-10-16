import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ComplianceTrend } from '../api';

interface ComplianceChartProps {
  data: ComplianceTrend;
  title: string;
}

export const ComplianceChart: React.FC<ComplianceChartProps> = ({ data, title }) => {
  // Transform data for recharts
  const chartData = data.dates.map((date, index) => ({
    date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    'Overall Compliance': data.overall_scores[index],
    'Frequency Documentation': data.frequency_scores[index],
    'Goal Specificity': data.goal_scores[index],
    'Progress Tracking': data.progress_scores[index],
  }));

  return (
    <div style={{ width: '100%', height: '400px', padding: '20px', background: 'white', borderRadius: '8px' }}>
      <h3 style={{ marginBottom: '20px', color: '#2c3e50', fontSize: '14px', fontWeight: 'bold' }}>{title}</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            stroke="#666"
            fontSize={12}
          />
          <YAxis
            domain={[60, 100]}
            stroke="#666"
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
          <Line
            type="monotone"
            dataKey="Overall Compliance"
            stroke="#007acc"
            strokeWidth={2}
            dot={{ fill: '#007acc', strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Frequency Documentation"
            stroke="#28a745"
            strokeWidth={2}
            dot={{ fill: '#28a745', strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Goal Specificity"
            stroke="#ffc107"
            strokeWidth={2}
            dot={{ fill: '#ffc107', strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="Progress Tracking"
            stroke="#17a2b8"
            strokeWidth={2}
            dot={{ fill: '#17a2b8', strokeWidth: 2, r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};