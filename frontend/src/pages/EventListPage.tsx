import { useState } from "react";
import { Card, Table, Tag, Select, Space, Typography, Input, Row, Col } from "antd";
import { useNavigate } from "react-router-dom";
import { useEvents } from "@/hooks/useEvents";
import ScoreTag from "@/components/ScoreTag";
import DirectionTag from "@/components/DirectionTag";
import type { MarketEvent, MarketEventListParams } from "@/types/marketEvent";

const { Title } = Typography;

const EVENT_TYPES = [
  "earnings_surprise", "policy_change", "merger_acquisition", "product_launch",
  "regulatory_action", "geopolitical", "industry_disruption", "management_change", "market_anomaly",
];
const MARKETS = ["A_SHARE", "HK_SHARE", "BOTH", "UNKNOWN"];
const DIRECTIONS = ["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "UNKNOWN"];
const SORT_OPTIONS = [
  { label: "Alpha Score", value: "event_alpha_score" },
  { label: "Created At", value: "created_at" },
  { label: "Materiality", value: "materiality_score" },
];

export default function EventListPage() {
  const navigate = useNavigate();
  const [params, setParams] = useState<MarketEventListParams>({
    offset: 0, limit: 20, sort_by: "event_alpha_score", sort_order: "desc",
  });
  const { data, isLoading } = useEvents(params);

  const updateFilter = (key: string, value: string | undefined) => {
    setParams((p) => ({ ...p, [key]: value || undefined, offset: 0 }));
  };

  const columns = [
    { title: "Date", dataIndex: "first_seen_at", width: 120,
      render: (d: string) => new Date(d).toLocaleDateString("zh-CN") },
    { title: "Type", dataIndex: "event_type", width: 140,
      render: (t: string) => <Tag>{t}</Tag> },
    { title: "Summary", dataIndex: "event_summary", ellipsis: true },
    { title: "Market", dataIndex: "market_scope", width: 100 },
    { title: "Direction", dataIndex: "direction", width: 130,
      render: (d: string) => <DirectionTag direction={d} /> },
    { title: "Alpha", dataIndex: "event_alpha_score", width: 80, sorter: true,
      render: (s: number) => <ScoreTag score={s} /> },
    { title: "Confidence", dataIndex: "confidence_score", width: 90,
      render: (s: number) => <ScoreTag score={s} /> },
    { title: "Risk", dataIndex: "risk_score", width: 80,
      render: (s: number) => <ScoreTag score={s} /> },
    { title: "Status", dataIndex: "status", width: 110,
      render: (s: string) => <Tag>{s}</Tag> },
  ];

  return (
    <div>
      <Title level={4}>Events</Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]}>
          <Col><Select placeholder="Event Type" allowClear style={{ width: 160 }} options={EVENT_TYPES.map((t) => ({ label: t, value: t }))} onChange={(v) => updateFilter("event_type", v)} /></Col>
          <Col><Select placeholder="Market" allowClear style={{ width: 130 }} options={MARKETS.map((m) => ({ label: m, value: m }))} onChange={(v) => updateFilter("market_scope", v)} /></Col>
          <Col><Select placeholder="Direction" allowClear style={{ width: 130 }} options={DIRECTIONS.map((d) => ({ label: d, value: d }))} onChange={(v) => updateFilter("direction", v)} /></Col>
          <Col><Select placeholder="Sort By" style={{ width: 140 }} options={SORT_OPTIONS} value={params.sort_by} onChange={(v) => updateFilter("sort_by", v)} /></Col>
          <Col><Select placeholder="Order" style={{ width: 100 }} options={[{ label: "Desc", value: "desc" }, { label: "Asc", value: "asc" }]} value={params.sort_order} onChange={(v) => updateFilter("sort_order", v)} /></Col>
        </Row>
      </Card>
      <Table
        dataSource={data?.items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: (params.offset || 0) / (params.limit || 20) + 1,
          pageSize: params.limit || 20,
          total: data?.total || 0,
          onChange: (page, size) => setParams((p) => ({ ...p, offset: (page - 1) * size, limit: size })),
        }}
        onRow={(r) => ({ onClick: () => navigate(`/events/${r.id}`), style: { cursor: "pointer" } })}
      />
    </div>
  );
}