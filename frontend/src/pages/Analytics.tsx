/**
 * Analytics Dashboard
 * Key product metrics for AI customer support system.
 * Shows deflection rate, resolution rate, confidence scores, and feedback sentiment.
 */
import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, MessageSquare, CheckCircle, AlertTriangle, ThumbsUp, BarChart2 } from 'lucide-react';
import { getMetrics, getFeedbackHistory, Metrics, FeedbackHistory } from '../services/api';

export default function Analytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [feedbackHistory, setFeedbackHistory] = useState<FeedbackHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [metricsData, feedbackData] = await Promise.all([
        getMetrics(),
        getFeedbackHistory(),
      ]);
      setMetrics(metricsData);
      setFeedbackHistory(feedbackData);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const MetricCard = ({
    title,
    value,
    icon: Icon,
    color,
    subtitle,
    trend,
  }: {
    title: string;
    value: string | number;
    icon: any;
    color: string;
    subtitle?: string;
    trend?: 'up' | 'down';
  }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        {trend && (
          <div className={`flex items-center ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
            {trend === 'up' ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
          </div>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
    </div>
  );

  // Calculate deflection rate (inverse of escalation rate)
  const deflectionRate = 100 - metrics.escalation_rate;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Key metrics for AI customer support performance
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Conversations"
          value={metrics.total_conversations}
          icon={MessageSquare}
          color="bg-primary-600"
          subtitle={`${metrics.active_conversations} active now`}
        />
        
        <MetricCard
          title="Resolution Rate"
          value={`${metrics.resolution_rate}%`}
          icon={CheckCircle}
          color="bg-green-600"
          subtitle="Conversations resolved"
          trend="up"
        />
        
        <MetricCard
          title="Deflection Rate"
          value={`${deflectionRate.toFixed(1)}%`}
          icon={Activity}
          color="bg-blue-600"
          subtitle="AI handled without escalation"
          trend="up"
        />
        
        <MetricCard
          title="Avg Confidence Score"
          value={`${(metrics.avg_confidence_score * 100).toFixed(0)}%`}
          icon={BarChart2}
          color="bg-purple-600"
          subtitle="AI response confidence"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <MetricCard
          title="Escalation Rate"
          value={`${metrics.escalation_rate}%`}
          icon={AlertTriangle}
          color="bg-red-600"
          subtitle="Requiring human intervention"
          trend="down"
        />
        
        <MetricCard
          title="Feedback Sentiment"
          value={`${metrics.feedback_sentiment}%`}
          icon={ThumbsUp}
          color="bg-green-600"
          subtitle={`${metrics.helpful_feedback}/${metrics.total_feedback} helpful`}
          trend="up"
        />
        
        <MetricCard
          title="Agent Feedback"
          value={metrics.total_feedback}
          icon={MessageSquare}
          color="bg-indigo-600"
          subtitle="Total feedback collected"
        />
      </div>

      {/* Key Insights */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Key Insights</h2>
        <div className="space-y-3">
          <div className="flex items-start p-3 bg-green-50 rounded-lg">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <p className="font-medium text-green-900">Strong AI Performance</p>
              <p className="text-sm text-green-700">
                {deflectionRate.toFixed(1)}% of conversations handled without escalation demonstrates effective AI assistance
              </p>
            </div>
          </div>
          
          {metrics.avg_confidence_score < 0.7 && (
            <div className="flex items-start p-3 bg-yellow-50 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <p className="font-medium text-yellow-900">Confidence Score Opportunity</p>
                <p className="text-sm text-yellow-700">
                  Average confidence is {(metrics.avg_confidence_score * 100).toFixed(0)}%. Consider expanding knowledge base for better accuracy.
                </p>
              </div>
            </div>
          )}
          
          <div className="flex items-start p-3 bg-blue-50 rounded-lg">
            <ThumbsUp className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <p className="font-medium text-blue-900">Agent Feedback Collection</p>
              <p className="text-sm text-blue-700">
                {metrics.feedback_sentiment}% positive feedback rate - valuable data for model improvement
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Feedback */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">Recent Agent Feedback</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Conversation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rating
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agent Notes
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {feedbackHistory.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                    No feedback collected yet
                  </td>
                </tr>
              ) : (
                feedbackHistory.map((feedback) => (
                  <tr key={feedback.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{feedback.conversation_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          feedback.rating === 'helpful'
                            ? 'bg-green-100 text-green-800'
                            : feedback.rating === 'not_helpful'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {feedback.rating.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate">
                      {feedback.notes || feedback.agent_correction || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(feedback.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interview Talking Points */}
      <div className="mt-8 bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg p-6 border border-primary-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">📊 Product Metrics Design Rationale</h3>
        <div className="space-y-2 text-sm text-gray-700">
          <p><strong>Deflection Rate:</strong> Key indicator of AI effectiveness - shows % of issues resolved without human escalation</p>
          <p><strong>Resolution Rate:</strong> Measures customer satisfaction and conversation closure success</p>
          <p><strong>Confidence Score:</strong> Enables data-driven HITL decisions - low scores trigger agent review</p>
          <p><strong>Feedback Sentiment:</strong> Critical for RLHF - tracks agent satisfaction for model improvement</p>
          <p><strong>Escalation Rate:</strong> Inverse metric to deflection - highlights when AI needs support</p>
        </div>
      </div>
    </div>
  );
}

