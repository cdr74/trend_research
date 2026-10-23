# Curated Data Source Catalog & Feed Registry

This document establishes the curated data sources for the **Trend Horizon Radar**. Sources are organized across four channels to balance academic rigor, open-source code velocity, enterprise production viability, and early community momentum.

---

## 1. Source Classification & Authority Weighting Matrix

| Channel | Focus & Value Proposition | Authority Weight ($W_{\text{auth}}$) | Telemetry Captured |
| :--- | :--- | :---: | :--- |
| **Academic Venues** | Empirical peer-reviewed breakthroughs, formal proofs, artifact evaluations. | **1.3** | Citations, venue rank, download rates. |
| **Practitioner Blogs** | High-scale production case studies, post-mortems, real-world failure modes. | **1.2** | Case study depth, production validation. |
| **Open Source Repos** | Real implementation velocity, contributor diversity, permissive licenses. | **1.1** | Star velocity ($\Delta\text{stars}/\Delta t$), forks, contributor count. |
| **Community Feeds** | Early pulse, practitioner debates, unfiltered feedback on new tools. | **0.8** | Views, upvotes, comment/discussion density. |

---

## 2. Channel 1: Academic & Pre-Print Repositories

Academic feeds deliver high-signal research before commercial productization:

1. **arXiv `cs.SE` (Software Engineering)**
   - **URL / Query:** `http://export.arxiv.org/api/query?search_query=cat:cs.SE`
   - **Primary Focus:** Test generation, mutation testing, formal verification, automated debugging, program repair.
   - **Telemetry:** arXiv version count, Semantic Scholar citation count, venue publication acceptance.

2. **arXiv `cs.AI` & `cs.PL` (AI & Programming Languages)**
   - **URL / Query:** `http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.PL`
   - **Primary Focus:** Property-based testing, formal semantics, LLM agent planning, code synthesis verification.
   - **Telemetry:** Citation velocity.

3. **Top SE Conference Feeds (ICSE, FSE/ESEC, ISSTA, ASE)**
   - **Primary Focus:** Rigorous empirical evaluations with open artifact evaluation badges.

---

## 3. Channel 2: Open Source Ecosystems (GitHub)

Open-source repositories provide live telemetry on actual adoption and technical velocity:

1. **GitHub Topics (Trending Queries)**
   - `https://github.com/topics/test-generation`
   - `https://github.com/topics/mutation-testing`
   - `https://github.com/topics/flaky-tests`
   - `https://github.com/topics/browser-automation`
   - `https://github.com/topics/evals`
   - `https://github.com/topics/agentic-testing`
   - **Telemetry:** Star velocity ($\Delta\text{stars}/\text{week}$), fork velocity, commit cadence, contributor count.

2. **Core Quality & Testing Frameworks (Watchlist)**
   - `microsoft/playwright` (Browser automation and synthetic agent execution)
   - `vitest-dev/vitest` (Modern unit/integration test runner ergonomics)
   - `HypothesisWorks/hypothesis` (Property-based test synthesis)
   - `ragas-io/ragas` & `confident-ai/deepeval` (LLM-as-a-judge test suites & evals)
   - `google/fuzzbench` (Fuzzing benchmarks and empirical performance)

---

## 4. Channel 3: Practitioner Engineering Blogs (Tier-1 Enterprise)

Case studies from high-scale engineering organizations expose practical failure modes:

1. **Meta Engineering Blog** (`https://engineering.fb.com/category/developer-tools/`)
   - *Key Focus:* Sapienz automated testing, predictive test selection at mono-repo scale.
2. **Netflix Technology Blog** (`https://netflixtechblog.com/`)
   - *Key Focus:* Chaos engineering, automated canary analysis, continuous verification.
3. **Uber Engineering Blog** (`https://www.uber.com/en-US/blog/engineering/`)
   - *Key Focus:* Predictive test selection, flaky test isolation, microservice mock generation.
4. **Google Testing Blog Archive & Open Source Blog** (`https://testing.googleblog.com/`)
   - *Key Focus:* Hermetic testing, mutation testing at scale, test sizing conventions.
5. **ThoughtWorks Technology Insights / Martin Fowler Bliki** (`https://martinfowler.com/`)
   - *Key Focus:* Test pyramid, architecture fitness functions, contract testing.
6. **Cloudflare & Stripe Engineering Blogs** (`https://blog.cloudflare.com/tag/engineering/`)
   - *Key Focus:* Distributed reliability, sandbox testing, API contract verification.

---

## 5. Channel 4: Community Discussions & Audience Telemetry

Captures audience attention velocity and practitioner consensus:

1. **HackerNews (Algolia Search API)**
   - **Endpoint:** `https://hn.algolia.com/api/v1/search_by_date`
   - **Target Queries:** `test generation`, `mutation testing`, `evals`, `agent testing`, `flaky test`
   - **Telemetry:** Story points (upvotes), comment count, discussion sentiment.
2. **Reddit Professional Communities**
   - `r/softwaretesting` & `r/qualityassurance`
   - **Telemetry:** Post score, comment density.
3. **Curated Quality Newsletters**
   - Software Testing Weekly (`https://softwaretestingweekly.com/`)
   - Pragmatic Engineer (`https://newsletter.pragmaticengineer.com/`)
