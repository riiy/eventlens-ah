import { useParams, Link } from "react-router-dom";
import {
  Card, Descriptions, Tag, Tabs, Typography, Table, Spin, Button, Space, Progress,
  Alert, List, Empty, Collapse, Steps,
} from "antd";
import { useEvent, useEventAssets, useEventHypotheses, useEventPriceReactions, useGenerateHypothesis, useScoreEvent, useEventDocument, useEventLLMRunLogs } from "@/hooks/useEvents";
import ScoreTag from "@/components/ScoreTag";
import DirectionTag from "@/components/DirectionTag";

const { Title, Text, Paragraph } = Typography;

export default function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const { data: event, isLoading } = useEvent(eventId);
  const { data: assets } = useEventAssets(eventId);
  const { data: hypotheses } = useEventHypotheses(eventId);
  const { data: priceReactions } = useEventPriceReactions(eventId);
  const { data: document } = useEventDocument(event?.raw_document_id);
  const { data: llmRunLogs } = useEventLLMRunLogs(eventId);
  const scoreMutation = useScoreEvent();
  const hypothesisMutation = useGenerateHypothesis();

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;
  if (!event) return <Empty description="Event not found" />;

  const assetColumns = [
    { title: "Symbol", dataIndex: "symbol", render: (s: string, r: any) => <Link to={`/assets/${r.asset_id}`}>{s}</Link> },
    { title: "Name", dataIndex: "name" },
    { title: "Impact", dataIndex: "impact_direction", render: (d: string) => <DirectionTag direction={d} /> },
    { title: "Strength", dataIndex: "impact_strength", render: (s: number) => <Progress percent={Math.round(s * 100)} size="small" /> },
    { title: "Confidence", dataIndex: "confidence_score", render: (s: number) => <ScoreTag score={s} /> },
    { title: "Reason", dataIndex: "reason", ellipsis: true },
  ];

  const priceColumns = [
    { title: "Symbol", dataIndex: "asset_symbol", render: (s: string, r: any) => <Link to={`/assets/${r.asset_id}`}>{s}</Link> },
    { title: "Asset", dataIndex: "asset_name"},
    { title: "1D Return", dataIndex: "return_1d", render: (v: number | null) => v != null ? <Text style={{ color: v >= 0 ? "#52c41a" : "#ff4d4f" }}>{(v * 100).toFixed(2)}%</Text> : "-" },
    { title: "5D Return", dataIndex: "return_5d", render: (v: number | null) => v != null ? <Text style={{ color: v >= 0 ? "#52c41a" : "#ff4d4f" }}>{(v * 100).toFixed(2)}%</Text> : "-" },
    { title: "20D Return", dataIndex: "return_20d", render: (v: number | null) => v != null ? <Text style={{ color: v >= 0 ? "#52c41a" : "#ff4d4f" }}>{(v * 100).toFixed(2)}%</Text> : "-" },
    { title: "Max DD", dataIndex: "max_drawdown", render: (v: number | null) => v != null ? `${(v * 100).toFixed(2)}%` : "-" },
    { title: "Excess Ret", dataIndex: "excess_return", render: (v: number | null) => v != null ? <Text style={{ color: v >= 0 ? "#52c41a" : "#ff4d4f" }}>{(v * 100).toFixed(2)}%</Text> : "-" },
  ];

  const llmLogColumns = [
    { title: "Task", dataIndex: "task_type", width: 160, render: (t: string) => <Tag>{t}</Tag> },
    { title: "Model", dataIndex: "model_name", width: 100 },
    { title: "Version", dataIndex: "prompt_version", width: 80 },
    { title: "Latency", dataIndex: "latency_ms", width: 100, render: (v: number | null) => v != null ? `${v}ms` : "-" },
    { title: "Success", dataIndex: "success", width: 80, render: (s: boolean) => <Tag color={s ? "green" : "red"}>{s ? "OK" : "FAIL"}</Tag> },
    { title: "Error", dataIndex: "error_message", ellipsis: true, render: (e: string | null) => e ? <Text type="danger">{e}</Text> : "-" },
  ];

  const scoreItems = [
    { label: "Event Alpha", value: event.event_alpha_score },
    { label: "Materiality", value: event.materiality_score },
    { label: "Novelty", value: event.novelty_score },
    { label: "Credibility", value: event.credibility_score },
    { label: "Urgency", value: event.urgency_score },
    { label: "Confidence", value: event.confidence_score },
    { label: "Risk", value: event.risk_score },
  ];

  const tabItems = [
    {
      key: "scores",
      label: "Scores",
      children: (
        <Card>
          {scoreItems.map((s) => (
            <div key={s.label} style={{ marginBottom: 12 }}>
              <Space style={{ width: "100%", justifyContent: "space-between" }}>
                <Text>{s.label}</Text>
                <ScoreTag score={s.value} />
              </Space>
              <Progress percent={Math.round(s.value * 100)} size="small"
                strokeColor={s.value >= 0.7 ? "#52c41a" : s.value >= 0.4 ? "#faad14" : "#ff4d4f"} />
            </div>
          ))}
          <Alert type="info" showIcon style={{ marginTop: 16 }}
            message="Score Formula"
            description="Alpha = 0.20×Novelty + 0.20×Materiality + 0.15×Credibility + 0.15×Urgency + 0.10×Confidence + 0.10×Tradability + 0.10×Liquidity − 0.20×Risk" />
        </Card>
      ),
    },
    {
      key: "assets",
      label: `Linked Assets (${assets?.length || 0})`,
      children: (
        <Table dataSource={assets || []} columns={assetColumns} rowKey="id" size="small"
          pagination={false} locale={{ emptyText: "No linked assets. Generate a hypothesis to map assets." }} />
      ),
    },
    {
      key: "hypotheses",
      label: `Hypotheses (${hypotheses?.length || 0})`,
      children: hypotheses && hypotheses.length > 0 ? (
        <Collapse items={hypotheses.map((h, i) => ({
          key: h.id,
          label: <Space><Tag>{h.status}</Tag> {h.hypothesis_text.slice(0, 80)}...</Space>,
          children: (
            <div>
              <Paragraph><Text strong>Hypothesis:</Text> {h.hypothesis_text}</Paragraph>
              <Paragraph><Text strong>Time Horizon:</Text> {h.time_horizon}</Paragraph>
              <Paragraph><Text strong>Risk Notes:</Text> {h.risk_notes || "N/A"}</Paragraph>
              {h.impact_chain && h.impact_chain.length > 0 && (
                <Card size="small" title="Impact Chain" style={{ marginBottom: 8 }}>
                  <Steps direction="vertical" size="small" current={h.impact_chain.length}
                    items={h.impact_chain.map((step) => ({ title: step }))} />
                </Card>
              )}
              <Card size="small" title="Supporting Evidence" style={{ marginBottom: 8 }}>
                <List dataSource={h.supporting_evidence || []} renderItem={(item: string) => <List.Item><Text style={{ color: "#52c41a" }}>{item}</Text></List.Item>} />
              </Card>
              <Card size="small" title="Counter Evidence" style={{ marginBottom: 8 }}>
                <List dataSource={h.counter_evidence || []} renderItem={(item: string) => <List.Item><Text style={{ color: "#ff4d4f" }}>{item}</Text></List.Item>} />
              </Card>
              <Card size="small" title="Trigger Conditions">
                <List dataSource={h.trigger_conditions || []} renderItem={(item: string) => <List.Item>{item}</List.Item>} />
              </Card>
              <Card size="small" title="Invalidation Conditions">
                <List dataSource={h.invalidation_conditions || []} renderItem={(item: string) => <List.Item>{item}</List.Item>} />
              </Card>
            </div>
          ),
        }))} />
      ) : <Empty description="No hypotheses yet. Click 'Generate Hypothesis' to create one." />,
    },
    {
      key: "price",
      label: "Price Reaction",
      children: (
        <Table dataSource={priceReactions || []} columns={priceColumns} rowKey="id" size="small"
          pagination={false} locale={{ emptyText: "No price reaction data available yet." }} />
      ),
    },
    {
      key: "document",
      label: "Raw Document",
      children: document ? (
        <Card>
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="Source">{document.source}</Descriptions.Item>
            <Descriptions.Item label="Type">{document.source_type}</Descriptions.Item>
            <Descriptions.Item label="URL">{document.url || "-"}</Descriptions.Item>
            <Descriptions.Item label="Language">{document.language}</Descriptions.Item>
            <Descriptions.Item label="Published At">{document.published_at ? new Date(document.published_at).toLocaleString("zh-CN") : "-"}</Descriptions.Item>
            <Descriptions.Item label="Crawled At">{document.crawled_at ? new Date(document.crawled_at).toLocaleString("zh-CN") : "-"}</Descriptions.Item>
            <Descriptions.Item label="First Seen">{new Date(document.first_seen_at).toLocaleString("zh-CN")}</Descriptions.Item>
            <Descriptions.Item label="Credibility"><ScoreTag score={document.credibility_score} /></Descriptions.Item>
            <Descriptions.Item label="Content Hash" span={2}>{document.content_hash}</Descriptions.Item>
          </Descriptions>
          <Title level={5} style={{ marginTop: 16 }}>{document.title}</Title>
          <Paragraph style={{ whiteSpace: "pre-wrap", marginTop: 8 }}>{document.content}</Paragraph>
        </Card>
      ) : <Empty description="Raw document not available." />,
    },
    {
      key: "llm-logs",
      label: `LLM Run Logs (${llmRunLogs?.length || 0})`,
      children: (
        <Table dataSource={llmRunLogs || []} columns={llmLogColumns} rowKey="id" size="small"
          pagination={false} locale={{ emptyText: "No LLM run logs recorded yet." }}
          expandable={{
            expandedRowRender: (log) => (
              <pre style={{ maxHeight: 300, overflow: "auto", fontSize: 12 }}>
                {JSON.stringify(log.output_json, null, 2)}
              </pre>
            ),
            rowExpandable: (log) => log.output_json != null,
          }} />
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>{event.event_summary}</Title>
      </Space>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="Type"><Tag>{event.event_type}</Tag></Descriptions.Item>
          <Descriptions.Item label="Market">{event.market_scope}</Descriptions.Item>
          <Descriptions.Item label="Direction"><DirectionTag direction={event.direction} /></Descriptions.Item>
          <Descriptions.Item label="Status"><Tag>{event.status}</Tag></Descriptions.Item>
          <Descriptions.Item label="Primary Entity">{event.primary_entity || "-"}</Descriptions.Item>
          <Descriptions.Item label="First Seen">{new Date(event.first_seen_at).toLocaleString("zh-CN")}</Descriptions.Item>
        </Descriptions>
        <Space>
          <Button onClick={() => scoreMutation.mutate(event.id)} loading={scoreMutation.isPending}>
            Re-Score Event
          </Button>
          <Button type="primary" onClick={() => hypothesisMutation.mutate(event.id)} loading={hypothesisMutation.isPending}>
            Generate Hypothesis
          </Button>
        </Space>
      </Card>

      <Tabs defaultActiveKey="scores" items={tabItems} />
    </div>
  );
}