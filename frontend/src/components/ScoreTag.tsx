import { Tag } from "antd";

interface Props {
  score: number;
}

function getColor(score: number): string {
  if (score >= 0.7) return "#52c41a";
  if (score >= 0.4) return "#faad14";
  return "#ff4d4f";
}

export default function ScoreTag({ score }: Props) {
  return (
    <Tag color={getColor(score)} style={{ margin: 0, fontWeight: 600 }}>
      {score.toFixed(2)}
    </Tag>
  );
}