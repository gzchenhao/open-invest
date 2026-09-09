"""P3-0/P3-1 Policy Ingestion Pipeline（JUDGE 批准契约实施）。

Crawler 的任务是：DISCOVER → FETCH → PARSE → NORMALIZE → VALIDATE → INGEST。
**Crawler 不是 verification engine**——本包产出的候选记录永远
`is_mock=false, verification_status="unverified"`，VERIFIED 无任何代码路径。

阶段实现状态（见 CONTRACT.md）：
- P3-1（本 Quest）：source_registry + fetcher + raw snapshot + fetch failure log
- P3-2（未实现）：parser + normalize
- P3-3（未实现）：validate + staging + human approval

边界：不修改 real_policies.json / production server / Evidence v1 / src/trust/**。
"""

from global_policy_aggregator.pipeline.source_registry import (  # noqa: F401
    RegistryError,
    SourceRegistry,
    SourceEntry,
    DEFAULT_REGISTRY_PATH,
)
from global_policy_aggregator.pipeline.fetcher import (  # noqa: F401
    Fetcher,
    FetchResult,
    USER_AGENT,
    compute_content_hash,
    normalize_content,
)
from global_policy_aggregator.pipeline.candidate import (  # noqa: F401
    Candidate,
    FieldEvidence,
    Provenance,
    SCHEMA_VERSION,
)
from global_policy_aggregator.pipeline.parser import (  # noqa: F401
    ParsedContent,
    ParseError,
    ParseFailure,
    parse_html,
    record_parse_failure,
)
from global_policy_aggregator.pipeline.normalizer import (  # noqa: F401
    normalize,
    run_pipeline,
)
