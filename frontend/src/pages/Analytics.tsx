/**
 * Analytics Dashboard
 * Modern analytics dashboard with key product metrics for AI customer support system.
 * Shows deflection rate, resolution rate, confidence scores, and feedback sentiment.
 */
import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, MessageSquare, CheckCircle, AlertTriangle, ThumbsUp, BarChart2, Loader2, Info } from 'lucide-react';
import { getMetrics, getFeedbackHistory, Metrics, FeedbackHistory } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Skeleton } from '../components/ui/skeleton';
import { Separator } from '../components/ui/separator';
import { PageHeader } from '../components/layout/PageHeader';
import { cn } from '../components/ui/utils';

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
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const MetricCard = ({
    title,
    value,
    icon: Icon,
    iconBg,
    subtitle,
  }: {
    title: string;
    value: string | number;
    icon: any;
    iconBg: string;
    subtitle?: string;
  }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className={cn("p-1.5 rounded-md", iconBg)}>
          <Icon className="h-4 w-4 text-white" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );

  const getRatingBadgeVariant = (rating: string) => {
    switch (rating) {
      case 'helpful':
        return 'default';
      case 'not_helpful':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics Dashboard"
        description="Monitor your AI support system performance"
      />

      {/* Key Metrics Grid - 6 cards in top row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <MetricCard
          title="Total Conversations"
          value={metrics.total_conversations}
          icon={MessageSquare}
          iconBg="bg-sky-500"
          subtitle="All time"
        />
        
        <MetricCard
          title="Active Conversations"
          value={metrics.active_conversations}
          icon={TrendingUp}
          iconBg="bg-blue-500"
          subtitle="Currently active"
        />
        
        <MetricCard
          title="Resolution Rate"
          value={`${metrics.resolution_rate}%`}
          icon={CheckCircle}
          iconBg="bg-green-500"
          subtitle={`${Math.round(metrics.total_conversations * metrics.resolution_rate / 100)} resolved`}
        />
        
        <MetricCard
          title="Escalation Rate"
          value={`${metrics.escalation_rate}%`}
          icon={AlertTriangle}
          iconBg="bg-red-500"
          subtitle={`${Math.round(metrics.total_conversations * metrics.escalation_rate / 100)} escalated`}
        />
        
        <MetricCard
          title="Avg Confidence Score"
          value={`${(metrics.avg_confidence_score * 100).toFixed(0)}%`}
          icon={BarChart2}
          iconBg="bg-purple-500"
          subtitle="AI response confidence"
        />
        
        <MetricCard
          title="Feedback Sentiment"
          value={`${metrics.feedback_sentiment}%`}
          icon={ThumbsUp}
          iconBg="bg-green-500"
          subtitle={`${metrics.helpful_feedback} of ${metrics.total_feedback} helpful`}
        />
      </div>

      {/* Key Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Key Insights</CardTitle>
          <CardDescription>
            Automated analysis of your support metrics
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Alert>
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle>Strong AI Performance</AlertTitle>
            <AlertDescription>
              {(100 - metrics.escalation_rate).toFixed(1)}% of conversations handled without escalation demonstrates effective AI assistance
            </AlertDescription>
          </Alert>
          
          {metrics.avg_confidence_score < 0.7 && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Confidence Score Opportunity</AlertTitle>
              <AlertDescription>
                Average confidence is {(metrics.avg_confidence_score * 100).toFixed(0)}%. Consider expanding knowledge base for better accuracy.
              </AlertDescription>
            </Alert>
          )}
          
          <Alert>
            <ThumbsUp className="h-4 w-4 text-blue-600" />
            <AlertTitle>Agent Feedback Collection</AlertTitle>
            <AlertDescription>
              {metrics.feedback_sentiment}% positive feedback rate - valuable data for model improvement
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      {/* Recent Feedback */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Agent Feedback</CardTitle>
          <CardDescription>
            Latest feedback from support agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Conversation</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Agent Notes</TableHead>
                <TableHead>Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {feedbackHistory.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No feedback collected yet
                  </TableCell>
                </TableRow>
              ) : (
                feedbackHistory.map((feedback) => (
                  <TableRow key={feedback.id}>
                    <TableCell className="font-medium">
                      #{feedback.conversation_id}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRatingBadgeVariant(feedback.rating)}>
                        {feedback.rating.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-md">
                      <p className="truncate">
                        {feedback.notes || feedback.agent_correction || '-'}
                      </p>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {new Date(feedback.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Interview Talking Points */}
      <Card className="bg-gradient-to-r from-primary/5 to-purple-500/5 border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart2 className="h-5 w-5" />
            Product Metrics Design Rationale
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>Deflection Rate:</strong> Key indicator of AI effectiveness - shows % of issues resolved without human escalation</p>
            <p><strong>Resolution Rate:</strong> Measures customer satisfaction and conversation closure success</p>
            <p><strong>Confidence Score:</strong> Enables data-driven HITL decisions - low scores trigger agent review</p>
            <p><strong>Feedback Sentiment:</strong> Critical for RLHF - tracks agent satisfaction for model improvement</p>
            <p><strong>Escalation Rate:</strong> Inverse metric to deflection - highlights when AI needs support</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
