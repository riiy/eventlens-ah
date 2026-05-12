import { useParams, Link } from "react-router-dom";
import { Card, Descriptions, Tag, Typography, Table, Spin, Empty } from "antd";
import { useAsset, useAssets, useAssetEvents } from "@/hooks/useAssets";
import ScoreTag from "@/components/ScoreTag";
import DirectionTag from "@/components/DirectionTag";

const { Title } = Typography;

export default function AssetDetailPage() {
  const { assetId } = useParams<{ assetId: string }>();

  if (assetId) {
    return <AssetDetail assetId={assetId} />;
  }

  const { data, isLoading } = useAssets();

  const columns = [
    { title: "Symbol", dataIndex: "symbol", render: (s: string, r: any) => <Link to={`/assets/${r.id}`}>{s}</Link> },
    { title: "Name", dataIndex: "name" },
    { title: "Market", dataIndex: "market", render: (m: string) => <Tag>{m}</Tag> },
    { title: "Exchange", dataIndex: "exchange" },
    { title: "Sector", dataIndex: "sector", render: (s: string | null) => s || "-" },
    { title: "Industry", dataIndex: "industry", render: (i: string | null) => i || "-" },
    {
      title: "Tags",
      dataIndex: "business_tags",
      render: (tags: string[]) => tags?.length ? tags.map((t) => <Tag key={t}>{t}</Tag>) : "-",
    },
  ];

  return (
    <div>
      <Title level={4}>Asset Universe</Title>
      <Table
        dataSource={data?.items || []}
        columns={columns}
        rowKey="id"
        size="small"
        loading={isLoading}
        pagination={false}
        locale={{ emptyText: "No assets found" }}
      />
    </div>
  );
}

function AssetDetail({ assetId }: { assetId: string }) {
  const { data: asset, isLoading } = useAsset(assetId);
  const { data: events, isLoading: eventsLoading } = useAssetEvents(assetId);

  if (isLoading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;
  if (!asset) return <Empty description="Asset not found" />;

  const eventColumns = [
    { title: "Event", dataIndex: "event_summary", render: (s: string, r: any) => <Link to={`/events/${r.id}`}>{s.slice(0, 80)}{s.length > 80 ? "..." : ""}</Link> },
    { title: "Type", dataIndex: "event_type", render: (t: string) => <Tag>{t}</Tag> },
    { title: "Direction", dataIndex: "direction", render: (d: string) => <DirectionTag direction={d} /> },
    { title: "Alpha", dataIndex: "event_alpha_score", render: (s: number) => <ScoreTag score={s} /> },
    { title: "Status", dataIndex: "status", render: (s: string) => <Tag>{s}</Tag> },
  ];

  return (
    <div>
      <Title level={4}>{asset.name} ({asset.symbol})</Title>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="Market"><Tag>{asset.market}</Tag></Descriptions.Item>
          <Descriptions.Item label="Exchange">{asset.exchange}</Descriptions.Item>
          <Descriptions.Item label="Sector">{asset.sector || "-"}</Descriptions.Item>
          <Descriptions.Item label="Industry">{asset.industry || "-"}</Descriptions.Item>
          <Descriptions.Item label="Liquidity Score"><ScoreTag score={asset.liquidity_score} /></Descriptions.Item>
          <Descriptions.Item label="Tags">
            {(asset.business_tags || []).map((t: string) => <Tag key={t}>{t}</Tag>)}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title={`Related Events (${events?.length || 0})`}>
        <Table
          dataSource={events || []}
          columns={eventColumns}
          rowKey="id"
          size="small"
          loading={eventsLoading}
          pagination={false}
          locale={{ emptyText: "No events linked to this asset yet" }}
        />
      </Card>
    </div>
  );
}