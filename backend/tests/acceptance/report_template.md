# EventLens AH MVP 验收报告

> 生成日期：{{ report_date }}
> 验收版本：MVP v1
> 验收标准：7 层验收体系

---

## 1. 系统运行状态

| 检查项 | 状态 | 备注 |
|-------|------|------|
| Docker Compose 启动 (5 services) | {{ docker_up }} | |
| 后端健康检查 (`/api/health`) | {{ backend_health }} | |
| 前端访问 (Vite :5173) | {{ frontend_health }} | |
| 数据库迁移完成 | {{ db_migration }} | |
| Redis 连接 (Celery broker) | {{ redis_ok }} | |
| 全量测试通过 | {{ all_tests }} | {{ test_summary }} |

---

## 2. 核心链路测试 (7 步闭环)

| 步骤 | 成功 / 总数 | 通过率 |
|------|------------|--------|
| Step 1: 信息入库 | {{ step1_ok }} / {{ sample_count }} | {{ step1_pct }}% |
| Step 2: 事件抽取 | {{ step2_ok }} / {{ sample_count }} | {{ step2_pct }}% |
| Step 3: 标的映射 | {{ step3_ok }} / {{ sample_count }} | {{ step3_pct }}% |
| Step 4: 假设生成 | {{ step4_ok }} / {{ sample_count }} | {{ step4_pct }}% |
| Step 5: 风险反证 | {{ step5_ok }} / {{ sample_count }} | {{ step5_pct }}% |
| Step 6: 打分排序 | {{ step6_ok }} / {{ sample_count }} | {{ step6_pct }}% |
| Step 7: 后续表现记录 | {{ step7_ok }} / {{ sample_count }} | {{ step7_pct }}% |

**失败样本详情：**

{{ failure_details }}

---

## 3. LLM 输出质量

| 指标 | 阈值 | 实际 | 合格 |
|------|------|------|------|
| JSON 解析成功率 | ≥ 95% | {{ json_parse_rate }}% | {{ json_pass }} |
| 必填字段完整率 | ≥ 95% | {{ field_completeness }}% | {{ field_pass }} |
| 错误资产映射率 | ≤ 15% | {{ wrong_asset_rate }}% | {{ asset_pass }} |
| 直接买卖建议次数 | 0 | {{ buy_sell_count }} | {{ buy_sell_pass }} |
| 噪音标记为高分率 | ≤ 10% | {{ noise_high_score_rate }}% | {{ noise_pass }} |

**幻觉案例：**

{{ hallucination_cases }}

**买卖建议检测到的输出：**

{{ buy_sell_cases }}

---

## 4. 评分区分度检验

| 测试项 | 结果 |
|--------|------|
| 高价值 > 低价值事件 (差值 > 0.25) | {{ high_vs_low }} |
| 高可信度 > 传闻 (差值 > 0.08) | {{ credible_vs_rumor }} |
| 新闻 > 旧闻 (差值 > 0.12) | {{ fresh_vs_old }} |
| 低风险 > 高风险 (差值 > 0.12) | {{ low_risk_vs_high }} |
| 利好+不新+不可信+高风险 < 0.35 | {{ not_all_bullish }} |
| 分数分布范围 (max-min > 0.35) | {{ spread }} |
| 低分区 (< 0.4) 样本数 ≥ 3/20 | {{ low_count }} |
| 高分区 (> 0.7) 样本数 ≥ 3/20 | {{ high_count }} |

**评分错误案例：**

{{ scoring_errors }}

---

## 5. 前端体验

| 页面 | 功能 | 状态 | 备注 |
|------|------|------|------|
| Dashboard | 概览数据 | {{ dash_overview }} | |
| Dashboard | Top Events | {{ dash_top }} | |
| Dashboard | 最近文档 | {{ dash_docs }} | |
| Event List | 列表+分页 | {{ list_page }} | |
| Event List | 事件类型筛选 | {{ list_type_filter }} | |
| Event List | 市场/方向筛选 | {{ list_market_filter }} | |
| Event List | Status 筛选 | {{ list_status_filter }} | |
| Event List | Alpha/Risk 排序 | {{ list_sort }} | |
| Event Detail | Scores 面板 | {{ detail_scores }} | |
| Event Detail | Linked Assets | {{ detail_assets }} | |
| Event Detail | Hypotheses + 反证 | {{ detail_hypotheses }} | |
| Event Detail | Impact Chain 可视化 | {{ detail_impact_chain }} | |
| Event Detail | Price Reaction 表格 | {{ detail_price }} | |
| Event Detail | Raw Document 原文展示 | {{ detail_document }} | |
| Event Detail | LLM Run Logs 记录 | {{ detail_llm_logs }} | |
| Asset Detail | 资产信息 | {{ asset_page }} | |

---

## 6. 不通过信号检查

| 检查项 | 是否触发 | 说明 |
|--------|----------|------|
| 只有新闻总结，没有事件结构 | {{ fail_news_only }} | |
| 只有利好利空，没有反证 | {{ fail_no_counter }} | |
| 只有模型输出，没有 LLMRunLog | {{ fail_no_logs }} | |
| 只有前端展示，没有后续表现记录 | {{ fail_no_price }} | |
| 出现 "建议买入/卖出" | {{ fail_buy_sell }} | |
| 模型把无关新闻映射到热门股 | {{ fail_wrong_map }} | |
| 所有事件分数集中在 70-90 分 | {{ fail_score_cluster }} | |
| 没有 first_seen_at | {{ fail_no_first_seen }} | |
| 没有错误样本分析 | {{ fail_no_error_analysis }} | |

---

## 7. 已知问题

### P0 (必须修复)

{{ p0_issues }}

### P1 (应该修复)

{{ p1_issues }}

### P2 (建议修复)

{{ p2_issues }}

---

## 8. 下一版必须修复

{{ next_version_must_fix }}

---

## 9. 验收结论

| 层级 | 结论 |
|------|------|
| L1: 系统运行 | {{ l1_result }} |
| L2: 核心链路 | {{ l2_result }} |
| L3: 数据质量 | {{ l3_result }} |
| L4: LLM 输出质量 | {{ l4_result }} |
| L5: 评分区分度 | {{ l5_result }} |
| L6: 前端体验 | {{ l6_result }} |
| L7: 业务价值 | {{ l7_result }} |

**总体结论：{{ overall_result }}**

---
*本报告由 EventLens AH 自动验收框架生成*