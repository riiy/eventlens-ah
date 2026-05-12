import { Card, Col, Row, Statistic, Table, Typography, Button, Space, Tag } from "antd";
import { ThunderboltOutlined, FileTextOutlined, StarOutlined, ClockCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useDashboardSummary, useTopEvents } from "@/hooks/useDashboard";
import { useRunDemoIngestion } from "@/hooks/useIngestion";
import ScoreTag from "@/components/ScoreTag";
import DirectionTag from "@/components/DirectionTag";
import type { TopEventItem } from "@/types/dashboard";

const { Title, Text } = Typography;

const EVENT_TYPE_COLORS: Record<string, string> = {
  earnings_surprise: "#52c41a",
  policy_change: "#1890ff",
  merger_acquisition: "#722ed1",
  product_launch: "#13c2c2",
  regulatory_action: "#fa8c16",
  geopolitical: "#eb2f96",
  industry_disruption: "#faad14",
  management_change: "#2f54eb",
  market_anomaly: "#f5222d",
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  earnings_surprise: "Earnings Surprise",
  policy_change: "Policy Change",
  merger_acquisition: "M&A",
  product_launch: "Product Launch",
  regulatory_action: "Regulatory",
  geopolitical: "Geopolitical",
  industry_disruption: "Industry Disruption",
  management_change: "Management Change",
  market_anomaly: "Market Anomaly",
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useDashboardSummary();
  const { data: topEvents } = useTopEvents(10);
  const runDemo = useRunDemoIngestion();

  const pieData = summary
    ? Object.entries(summary.event_type_distribution).map(([type, count]) => ({
        name: EVENT_TYPE_LABELS[type] || type,
        value: count,
        color: EVENT_TYPE_COLORS[type] || "#d9d9d9",
      }))
    : [];

  const columns = [
    { title: "Type", dataIndex: "event_type", width: 150,
      render: (t: string) => <Tag color={EVENT_TYPE_COLORS[t]}>{EVENT_TYPE_LABELS[t] || t}</Tag> },
    { title: "Summary", dataIndex: "event_summary", ellipsis: true,
      render: (text: string, r: TopEventItem) => (
        <a onClick={() => navigate(`/events/${r.id}`)}>{text}</a>
      )},
    { title: "Score", dataIndex: "event_alpha_score", width: 80,
      render: (s: number) => <ScoreTag score={s} /> },
    { title: "Direction", dataIndex: "direction", width: 120,
      render: (d: string) => <DirectionTag direction={d} /> },
    { title: "Market", dataIndex: "market_scope", width: 100 },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16, justifyContent: "space-between", width: "100%" }}>
        <Title level={4} style={{ margin: 0 }}>Research Dashboard</Title>
        <Button type="primary" loading={runDemo.isPending} onClick={() => runDemo.mutate()}>
          Run Demo Ingestion
        </Button>
      </Space>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="Total Events" value={summary?.total_events || 0} prefix={<ThunderboltOutlined />} loading={isLoading} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="High Score Events" value={summary?.high_score_events || 0} prefix={<StarOutlined />} suffix={summary ? `/ ${summary.total_events}` : ""} loading={isLoading} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Documents" value={summary?.total_documents || 0} prefix={<FileTextOutlined />} loading={isLoading} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="Pending Review" value={summary?.pending_events || 0} prefix={<ClockCircleOutlined />} loading={isLoading} /></Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={10}>
          <Card title="Event Type Distribution">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, value }) => `${name}: ${value}`}>
                    {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Text type="secondary">No data yet. Run demo ingestion to populate.</Text>
            )}
          </Card>
        </Col>
        <Col span={14}>
          <Card title="Recent Events">
            <Table
              dataSource={topEvents || []}
              columns={columns}
              rowKey="id"
              size="small"
              pagination={false}
              loading={isLoading}
              onRow={(r) => ({ onClick: () => navigate(`/events/${r.id}`), style: { cursor: "pointer" } })}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}