# 混合检索系统设计 (Hybrid Search)

## 概述
采用 **70% RAG语义检索 + 30% 关键词检索** 的混合策略，兼顾语义理解和精确匹配。

## 为什么需要混合检索？

### 单一检索方式的局限性

| 场景 | 纯RAG语义检索 | 纯关键词检索 |
|------|--------------|-------------|
| 查询"呼吸困难的鸡" | ✅ 能匹配"喘气"、"张口呼吸" | ❌ 只能匹配精确词 |
| 查询"禽流感H5N1" | ❌ 可能匹配其他流感 | ✅ 精确匹配疾病名 |
| 查询"阳光养殖场" | ❌ 可能匹配其他养殖场 | ✅ 精确匹配场名 |
| 查询"鸡咳嗽发烧" | ✅ 理解症状组合 | ⚠️ 需要同时包含两词 |

### 混合检索的优势
- **语义理解**: RAG能理解"腹泻"和"拉稀"是同一个意思
- **精确匹配**: 关键词确保疾病名、药物名精确匹配
- **互补增强**: 两种方式取长补短

## 系统架构

```
                        ┌─────────────────┐
                        │   用户查询输入   │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │    查询预处理    │
                        │  (分词、纠错)    │
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼─────────┐       │       ┌─────────▼─────────┐
    │   RAG语义检索      │       │       │   关键词检索       │
    │   (权重: 70%)     │       │       │   (权重: 30%)     │
    │                   │       │       │                   │
    │  ┌─────────────┐  │       │       │  ┌─────────────┐  │
    │  │ 文本向量化   │  │       │       │  │ 关键词提取   │  │
    │  └──────┬──────┘  │       │       │  └──────┬──────┘  │
    │         │         │       │       │         │         │
    │  ┌──────▼──────┐  │       │       │  ┌──────▼──────┐  │
    │  │ Milvus检索   │  │       │       │  │ ES/PG全文   │  │
    │  │ (余弦相似度) │  │       │       │  │ (BM25算法)  │  │
    │  └──────┬──────┘  │       │       │  └──────┬──────┘  │
    │         │         │       │       │         │         │
    │  ┌──────▼──────┐  │       │       │  ┌──────▼──────┐  │
    │  │ 结果+分数    │  │       │       │  │ 结果+分数    │  │
    │  └─────────────┘  │       │       │  └─────────────┘  │
    └─────────┬─────────┘       │       └─────────┬─────────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   分数归一化     │
                        │ (Min-Max Norm)  │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   加权融合       │
                        │ 0.7*RAG+0.3*KW  │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  去重+重排序     │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   返回TOP K     │
                        └─────────────────┘
```

## 技术实现

### 1. RAG语义检索 (70%)

#### 向量化模型选择
```python
# 推荐使用阿里云DashScope的embedding模型
EMBEDDING_CONFIG = {
    "provider": "dashscope",
    "model": "text-embedding-v2",  # 阿里云文本向量模型
    "dimension": 1536,
    "batch_size": 25
}

# 备选：OpenAI
# "model": "text-embedding-3-small"
```

#### Milvus检索配置
```python
# Milvus集合配置
MILVUS_CONFIG = {
    "collection_name": "poultry_records",
    "metric_type": "COSINE",  # 余弦相似度
    "index_type": "IVF_FLAT",
    "nlist": 1024,
    "nprobe": 16
}

# 检索参数
RAG_SEARCH_PARAMS = {
    "top_k": 20,              # 先检索20条
    "min_similarity": 0.6     # 最低相似度阈值
}
```

#### RAG检索实现
```python
from pymilvus import Collection
import dashscope

class RAGSearcher:
    def __init__(self):
        self.collection = Collection("poultry_records")
        self.collection.load()

    async def search(self, query: str, top_k: int = 20) -> list[dict]:
        """RAG语义检索"""
        # 1. 查询文本向量化
        embedding = await self._get_embedding(query)

        # 2. Milvus相似度搜索
        results = self.collection.search(
            data=[embedding],
            anns_field="embedding_vector",
            param={"metric_type": "COSINE", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["record_id", "record_no", "diagnosis", "symptoms"]
        )

        # 3. 格式化结果
        return [
            {
                "record_id": hit.entity.get("record_id"),
                "record_no": hit.entity.get("record_no"),
                "diagnosis": hit.entity.get("diagnosis"),
                "symptoms": hit.entity.get("symptoms"),
                "rag_score": hit.score,  # 余弦相似度 0-1
                "source": "rag"
            }
            for hit in results[0]
        ]

    async def _get_embedding(self, text: str) -> list[float]:
        """获取文本向量"""
        response = dashscope.TextEmbedding.call(
            model="text-embedding-v2",
            input=text
        )
        return response.output["embeddings"][0]["embedding"]
```

### 2. 关键词检索 (30%)

#### 关键词提取策略
```python
# 医学领域关键词词典
MEDICAL_KEYWORDS = {
    "diseases": ["禽流感", "新城疫", "传染性支气管炎", "法氏囊病", ...],
    "symptoms": ["咳嗽", "腹泻", "呼吸困难", "食欲减退", "羽毛蓬松", ...],
    "medications": ["金刚烷胺", "阿莫西林", "恩诺沙星", ...],
    "poultry_types": ["鸡", "鸭", "鹅", "白羽肉鸡", "蛋鸡", ...]
}

# 同义词映射
SYNONYMS = {
    "腹泻": ["拉稀", "稀便", "水样便"],
    "呼吸困难": ["喘气", "张口呼吸", "呼吸急促"],
    "食欲减退": ["不吃食", "采食量下降", "厌食"],
    ...
}
```

#### PostgreSQL全文搜索
```python
class KeywordSearcher:
    """关键词检索器"""

    async def search(self, query: str, top_k: int = 20) -> list[dict]:
        """关键词检索"""
        # 1. 提取关键词
        keywords = self._extract_keywords(query)

        # 2. 构建搜索查询
        sql = """
        SELECT
            id as record_id,
            record_no,
            primary_diagnosis as diagnosis,
            ts_rank(
                to_tsvector('simple', coalesce(record_markdown, '')),
                plainto_tsquery('simple', :query)
            ) as keyword_score
        FROM medical_records
        WHERE
            -- 全文搜索
            to_tsvector('simple', coalesce(record_markdown, ''))
            @@ plainto_tsquery('simple', :query)
            -- 或者JSON字段匹配
            OR record_json->>'primary_diagnosis' ILIKE ANY(:keywords)
            OR record_json->'case_info'->>'symptoms' ILIKE ANY(:keywords)
        ORDER BY keyword_score DESC
        LIMIT :limit
        """

        results = await db.fetch_all(sql, {
            "query": query,
            "keywords": [f"%{kw}%" for kw in keywords],
            "limit": top_k
        })

        return [
            {
                "record_id": r["record_id"],
                "record_no": r["record_no"],
                "diagnosis": r["diagnosis"],
                "keyword_score": float(r["keyword_score"]),
                "source": "keyword"
            }
            for r in results
        ]

    def _extract_keywords(self, query: str) -> list[str]:
        """提取关键词"""
        keywords = []

        # 匹配医学词典
        for category, words in MEDICAL_KEYWORDS.items():
            for word in words:
                if word in query:
                    keywords.append(word)
                    # 添加同义词
                    if word in SYNONYMS:
                        keywords.extend(SYNONYMS[word])

        # jieba分词补充
        import jieba
        jieba.load_userdict("medical_dict.txt")
        tokens = jieba.cut(query)
        keywords.extend([t for t in tokens if len(t) > 1])

        return list(set(keywords))
```

#### Elasticsearch增强（可选）
```python
# 如果需要更强的全文搜索能力，可以使用Elasticsearch
ES_CONFIG = {
    "index": "poultry_records",
    "analyzer": "ik_smart",  # 中文分词
}

class ESKeywordSearcher:
    async def search(self, query: str, top_k: int = 20) -> list[dict]:
        """Elasticsearch BM25检索"""
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "diagnosis^3",      # 诊断权重最高
                                    "symptoms^2",       # 症状次之
                                    "treatment",
                                    "content"
                                ],
                                "type": "best_fields"
                            }
                        },
                        {
                            "match_phrase": {
                                "farm_name": {
                                    "query": query,
                                    "boost": 2
                                }
                            }
                        }
                    ]
                }
            },
            "size": top_k
        }

        response = await es.search(index="poultry_records", body=body)

        return [
            {
                "record_id": hit["_source"]["record_id"],
                "record_no": hit["_source"]["record_no"],
                "diagnosis": hit["_source"]["diagnosis"],
                "keyword_score": hit["_score"],
                "source": "keyword"
            }
            for hit in response["hits"]["hits"]
        ]
```

### 3. 混合融合算法

```python
class HybridSearcher:
    """混合检索器"""

    def __init__(
        self,
        rag_weight: float = 0.7,
        keyword_weight: float = 0.3,
        top_k: int = 10
    ):
        self.rag_weight = rag_weight
        self.keyword_weight = keyword_weight
        self.top_k = top_k
        self.rag_searcher = RAGSearcher()
        self.keyword_searcher = KeywordSearcher()

    async def search(self, query: str) -> list[dict]:
        """混合检索"""
        # 1. 并行执行两种检索
        rag_results, keyword_results = await asyncio.gather(
            self.rag_searcher.search(query, top_k=20),
            self.keyword_searcher.search(query, top_k=20)
        )

        # 2. 分数归一化
        rag_results = self._normalize_scores(rag_results, "rag_score")
        keyword_results = self._normalize_scores(keyword_results, "keyword_score")

        # 3. 合并结果
        merged = self._merge_results(rag_results, keyword_results)

        # 4. 加权融合计算最终分数
        for item in merged:
            rag_score = item.get("rag_score_norm", 0)
            keyword_score = item.get("keyword_score_norm", 0)
            item["final_score"] = (
                self.rag_weight * rag_score +
                self.keyword_weight * keyword_score
            )

        # 5. 排序并返回TOP K
        merged.sort(key=lambda x: x["final_score"], reverse=True)
        return merged[:self.top_k]

    def _normalize_scores(
        self,
        results: list[dict],
        score_field: str
    ) -> list[dict]:
        """Min-Max归一化"""
        if not results:
            return results

        scores = [r[score_field] for r in results]
        min_score = min(scores)
        max_score = max(scores)

        for r in results:
            if max_score > min_score:
                r[f"{score_field}_norm"] = (
                    (r[score_field] - min_score) / (max_score - min_score)
                )
            else:
                r[f"{score_field}_norm"] = 1.0

        return results

    def _merge_results(
        self,
        rag_results: list[dict],
        keyword_results: list[dict]
    ) -> list[dict]:
        """合并去重"""
        merged = {}

        # 添加RAG结果
        for r in rag_results:
            record_id = r["record_id"]
            merged[record_id] = {
                "record_id": record_id,
                "record_no": r["record_no"],
                "diagnosis": r["diagnosis"],
                "rag_score_norm": r.get("rag_score_norm", 0),
                "keyword_score_norm": 0,
                "sources": ["rag"]
            }

        # 合并关键词结果
        for r in keyword_results:
            record_id = r["record_id"]
            if record_id in merged:
                merged[record_id]["keyword_score_norm"] = r.get("keyword_score_norm", 0)
                merged[record_id]["sources"].append("keyword")
            else:
                merged[record_id] = {
                    "record_id": record_id,
                    "record_no": r["record_no"],
                    "diagnosis": r["diagnosis"],
                    "rag_score_norm": 0,
                    "keyword_score_norm": r.get("keyword_score_norm", 0),
                    "sources": ["keyword"]
                }

        return list(merged.values())
```

## API设计

### 混合检索接口
```
POST /api/v1/search/hybrid
```

**Request**
```json
{
  "query": "白羽肉鸡呼吸困难咳嗽",
  "filters": {
    "date_range": {
      "start": "2025-01-01",
      "end": "2026-01-31"
    },
    "poultry_type": "鸡",
    "severity": ["高", "中"]
  },
  "options": {
    "rag_weight": 0.7,
    "keyword_weight": 0.3,
    "top_k": 10,
    "min_score": 0.5
  }
}
```

**Response**
```json
{
  "total": 10,
  "query": "白羽肉鸡呼吸困难咳嗽",
  "results": [
    {
      "record_id": "uuid",
      "record_no": "PR20260115001",
      "diagnosis": "疑似禽流感",
      "symptoms": ["呼吸困难", "咳嗽", "食欲减退"],
      "farm_name": "阳光养殖场",
      "visit_date": "2026-01-15",
      "final_score": 0.92,
      "rag_score": 0.95,
      "keyword_score": 0.85,
      "sources": ["rag", "keyword"],
      "highlight": {
        "symptoms": ["<em>呼吸困难</em>", "<em>咳嗽</em>"]
      }
    },
    ...
  ],
  "search_time_ms": 120
}
```

## 配置管理

### 数据库配置表
```sql
CREATE TABLE search_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP NOT NULL,
    updated_by UUID REFERENCES users(id)
);

-- 默认配置
INSERT INTO search_config (config_key, config_value, description) VALUES
('hybrid_search', '{
  "rag_weight": 0.7,
  "keyword_weight": 0.3,
  "top_k": 10,
  "min_score": 0.5,
  "enable_synonym": true,
  "enable_highlight": true
}', '混合检索配置');
```

### Master配置界面
```vue
<template>
  <view class="search-config">
    <text class="title">混合检索配置</text>

    <view class="config-item">
      <text>RAG语义检索权重</text>
      <slider
        v-model="config.rag_weight"
        :min="0"
        :max="1"
        :step="0.05"
        show-value
      />
      <text>{{ (config.rag_weight * 100).toFixed(0) }}%</text>
    </view>

    <view class="config-item">
      <text>关键词检索权重</text>
      <slider
        v-model="config.keyword_weight"
        :min="0"
        :max="1"
        :step="0.05"
        show-value
        disabled
      />
      <text>{{ (config.keyword_weight * 100).toFixed(0) }}%</text>
    </view>

    <view class="config-item">
      <text>返回结果数量</text>
      <input v-model.number="config.top_k" type="number" />
    </view>

    <view class="config-item">
      <text>最低分数阈值</text>
      <slider
        v-model="config.min_score"
        :min="0"
        :max="1"
        :step="0.05"
        show-value
      />
    </view>

    <view class="config-item">
      <checkbox v-model="config.enable_synonym">启用同义词扩展</checkbox>
    </view>

    <button @click="saveConfig">保存配置</button>
    <button @click="testSearch">测试搜索</button>
  </view>
</template>

<script>
export default {
  data() {
    return {
      config: {
        rag_weight: 0.7,
        keyword_weight: 0.3,
        top_k: 10,
        min_score: 0.5,
        enable_synonym: true
      }
    }
  },
  watch: {
    'config.rag_weight'(val) {
      // 自动计算关键词权重
      this.config.keyword_weight = 1 - val
    }
  }
}
</script>
```

## 性能优化

### 1. 并行检索
两种检索方式并行执行，总耗时取决于较慢的一个：
```python
# 使用asyncio.gather并行执行
rag_results, keyword_results = await asyncio.gather(
    self.rag_searcher.search(query),
    self.keyword_searcher.search(query)
)
```

### 2. 缓存策略
```python
# Redis缓存热门查询结果
CACHE_CONFIG = {
    "enable": True,
    "ttl": 300,  # 5分钟
    "max_size": 1000
}

async def search_with_cache(query: str) -> list[dict]:
    cache_key = f"hybrid_search:{hash(query)}"

    # 检查缓存
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 执行检索
    results = await hybrid_searcher.search(query)

    # 存入缓存
    await redis.setex(cache_key, 300, json.dumps(results))

    return results
```

### 3. 索引优化

#### PostgreSQL
```sql
-- 全文搜索GIN索引
CREATE INDEX idx_records_fulltext ON medical_records
USING GIN(to_tsvector('simple', coalesce(record_markdown, '')));

-- JSONB GIN索引
CREATE INDEX idx_records_json_gin ON medical_records
USING GIN(record_json);

-- 部分索引（只索引活跃病历）
CREATE INDEX idx_records_active_fulltext ON medical_records
USING GIN(to_tsvector('simple', coalesce(record_markdown, '')))
WHERE status = 'active';
```

#### Milvus
```python
# 使用IVF_FLAT索引，平衡精度和速度
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}

# 搜索时设置nprobe
search_params = {"nprobe": 16}  # 搜索16个聚类
```

## 监控指标

### 检索质量指标
```python
METRICS = {
    "search_latency_ms": "检索延迟",
    "rag_hit_rate": "RAG命中率",
    "keyword_hit_rate": "关键词命中率",
    "overlap_rate": "两种方式重叠率",
    "avg_final_score": "平均最终分数",
    "zero_result_rate": "零结果率"
}
```

### 日志记录
```python
@app.post("/api/v1/search/hybrid")
async def hybrid_search(request: SearchRequest):
    start_time = time.time()

    results = await hybrid_searcher.search(request.query)

    # 记录检索日志
    await log_search(
        query=request.query,
        result_count=len(results),
        latency_ms=(time.time() - start_time) * 1000,
        rag_results=len([r for r in results if "rag" in r["sources"]]),
        keyword_results=len([r for r in results if "keyword" in r["sources"]]),
        user_id=current_user.id
    )

    return results
```

## 测试用例

### 单元测试
```python
class TestHybridSearch:

    async def test_rag_only_result(self):
        """测试只有RAG能匹配的语义查询"""
        results = await hybrid_searcher.search("禽类呼吸系统疾病")
        assert len(results) > 0
        # 应该能匹配"呼吸困难"、"咳嗽"等症状的病历

    async def test_keyword_only_result(self):
        """测试只有关键词能匹配的精确查询"""
        results = await hybrid_searcher.search("阳光养殖场")
        assert len(results) > 0
        # 应该精确匹配养殖场名称

    async def test_hybrid_boost(self):
        """测试两种方式都匹配时分数更高"""
        results = await hybrid_searcher.search("禽流感H5N1呼吸困难")

        # 两种方式都匹配的结果应该排在前面
        top_result = results[0]
        assert "rag" in top_result["sources"]
        assert "keyword" in top_result["sources"]
        assert top_result["final_score"] > 0.8

    async def test_weight_adjustment(self):
        """测试权重调整效果"""
        # 70% RAG
        results_70_30 = await HybridSearcher(0.7, 0.3).search("咳嗽")

        # 30% RAG
        results_30_70 = await HybridSearcher(0.3, 0.7).search("咳嗽")

        # 结果排序应该不同
        assert results_70_30[0]["record_id"] != results_30_70[0]["record_id"]
```

## 常见问题

### Q: 为什么选择70:30的权重比例？
A: 根据医疗检索场景的特点：
- 语义理解很重要（症状描述多样）
- 但精确匹配也不可或缺（疾病名、药物名）
- 70:30是经验值，可根据实际效果调整

### Q: 两种检索结果完全不重叠怎么办？
A: 这是正常的，说明两种方式互补性强。融合后的结果会包含两边的结果，按加权分数排序。

### Q: 如何处理检索结果为空？
A:
1. 降低最低分数阈值
2. 扩展同义词
3. 提示用户调整查询词
4. 显示"相关推荐"而非空结果
