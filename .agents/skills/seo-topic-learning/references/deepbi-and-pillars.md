# DeepBI 边界与四 pillar

补题、拟继续 active 的存量题、清题决策前读本页。

## Amazon 电商（所有 pillar）

选题须为亚马逊卖家/站内运营。拒绝与 Amazon 无关的通用话题。

## DeepBI 产品边界（standard profile）

适用于 `amazon_ads` / `amazon_listing_opt` / `amazon_organic_traffic`：

- 仅 Amazon 卖家；禁止 Shopify / Walmart / 独立站 / 多平台统管
- 广告只讲 **Sponsored Products（SP）**；禁止 SB、SD 当独立卖点
- Listing：主图/标题/五点/A+/转化；不做评论运营、QA 自动化、Listing A/B 产品化
- 自然流量：站内排名与广告反哺；禁止站外多渠道为主叙事
- 禁止卖点：A/B Test、评论运营/自动化、QA 问答系统

## ai_compliance profile

`amazon_ai_compliance`：豁免 SP-only 等产品边界；须为卖家 AI/生成式内容合规语境。
禁止教唆伪造评论/QA、误导 Listing、规避审核。

## 四 pillar MECE

| pillar | 写 | 不写 |
|---|---|---|
| `amazon_ads` | SP 出价、ACOS、结构 | AI 政策解读 |
| `amazon_listing_opt` | 主图/五点/转化实操 | 「AI Listing 是否违规」 |
| `amazon_organic_traffic` | 站内排名、关键词 | 站外 AI 营销 |
| `amazon_ai_compliance` | 政策、风险、流程、工具 | SP/Listing SOP |

## L0 禁词

shopify, walmart, 独立站, 多平台, sponsored brands, sponsored display,
评论运营, review automation, qa automation, 问答系统, a/b test, ab test

## 禁止意图簇

`review_automation` `qa_system` `ab_test_listing` `shopify_multi_channel` `sponsored_brands_sd`

## 审查 JSON（主 Agent 或审查子 Agent）

```json
{
  "reviews": [
    {
      "sub_topic_key": "example",
      "pass": false,
      "profile": "standard",
      "violations": ["multi_platform"],
      "rationale": "标题含 Shopify"
    }
  ],
  "rejected_keys": ["example"]
}
```

未 pass：不得 INSERT；存量不得维持 active。

## notes 证据前缀

`gsc:` `news:` `coverage:` `geo:` `autocomplete:` `competitor:`
