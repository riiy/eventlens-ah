import { Tag } from "antd";
import { CaretUpOutlined, CaretDownOutlined, MinusOutlined } from "@ant-design/icons";

interface Props {
  direction: string;
}

const colorMap: Record<string, { color: string; icon: React.ReactNode }> = {
  POSITIVE: { color: "#52c41a", icon: <CaretUpOutlined /> },
  NEGATIVE: { color: "#ff4d4f", icon: <CaretDownOutlined /> },
  NEUTRAL: { color: "#d9d9d9", icon: <MinusOutlined /> },
  MIXED: { color: "#faad14", icon: null },
  UNKNOWN: { color: "#d9d9d9", icon: null },
};

export default function DirectionTag({ direction }: Props) {
  const config = colorMap[direction] || colorMap.UNKNOWN;
  return (
    <Tag color={config.color} style={{ margin: 0 }}>
      {config.icon} {direction}
    </Tag>
  );
}