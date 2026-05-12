import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Typography } from "antd";
import {
  DashboardOutlined,
  ThunderboltOutlined,
  StockOutlined,
} from "@ant-design/icons";

const { Header, Sider, Content, Footer } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/events", icon: <ThunderboltOutlined />, label: "Events" },
  { key: "/assets", icon: <StockOutlined />, label: "Assets" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = "/" + location.pathname.split("/")[1];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        width={220}
        style={{
          background: "linear-gradient(180deg, #1a365d 0%, #2d5a8e 100%)",
        }}
      >
        <div
          style={{
            padding: "20px 16px",
            borderBottom: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          <Text
            strong
            style={{ color: "#fff", fontSize: 18, letterSpacing: 1 }}
          >
            EventLens AH
          </Text>
          <br />
          <Text style={{ color: "rgba(255,255,255,0.55)", fontSize: 11 }}>
            AI-Powered Market Event Research
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: "transparent",
            borderRight: 0,
            marginTop: 8,
          }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: "#fff",
            padding: "0 24px",
            borderBottom: "1px solid #f0f0f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Text strong style={{ fontSize: 16 }}>
            EventLens AH Research Dashboard
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Research tool only — not financial advice
          </Text>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: "#fff", borderRadius: 6 }}>
          <Outlet />
        </Content>
        <Footer style={{ textAlign: "center", fontSize: 12, color: "#999" }}>
          <Text type="secondary">
            This tool is for research purposes only. It does NOT provide
            investment advice, buy/sell recommendations, or trading signals. All
            data is for informational use and may contain inaccuracies.
          </Text>
        </Footer>
      </Layout>
    </Layout>
  );
}