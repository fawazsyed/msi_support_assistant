# Rate Limiting & Budget Control Guide

This guide explains the multi-layered cost protection built into the MSI AI Assistant to prevent API overspending.

---

## 🛡️ Built-in Protections (Already Configured)

### 1. **Client-Side Rate Limiting** ⏱️

**Location:** [`src/main.py:48-53`](src/main.py#L48-L53), [`src/api_server.py:71-76`](src/api_server.py#L71-L76)

```python
rate_limiter = InMemoryRateLimiter(
    requests_per_second=2,  # 120 requests/minute
    check_every_n_seconds=0.1,
    max_bucket_size=10,  # Allow bursts of 10
)
```

**What it does:**
- Limits LLM API calls to **2 per second** (120/minute)
- Prevents rapid-fire requests that could rack up costs
- Thread-safe across multiple concurrent users
- Works **before** requests reach the API (no charges for blocked requests)

**Cost impact:**
- GPT-4o-mini @ 120 RPM = ~7,200 requests/hour max
- At $0.15/1M input tokens (~500 tokens/request) = **~$0.54/hour max**

---

### 2. **Tool Call Limits** 🔧

**Location:** [`src/main.py:174-178`](src/main.py#L174-L178), [`src/api_server.py:180-184`](src/api_server.py#L180-L184)

```python
tool_call_limit = ToolCallLimitMiddleware(
    run_limit=15,  # Max 15 tool calls per query
    exit_behavior="continue"
)
```

**What it does:**
- Prevents runaway agent loops (e.g., infinite tool calling)
- Stops execution after **15 tool calls** per user query
- Each tool call = 1 LLM inference = API cost
- Agent returns partial answer if limit hit (doesn't crash)

**Why 15?**
- Typical RAG query: 2-4 tool calls (search → answer)
- Complex multi-step: 8-12 tool calls
- 15 provides safety margin without restricting legitimate use

**Cost impact:**
- Worst case: 15 tool calls × 2 LLM calls each = 30 API calls/query
- With rate limiter: 30 calls @ 2 RPS = 15 seconds max per query
- Still capped by rate limiter at 120 RPM globally

---

### 3. **Agentic RAG Architecture** 🧠

**Location:** Refactored in [`src/main.py:95-122`](src/main.py#L95-L122)

**What it does:**
- RAG is now a **tool** the agent chooses to call
- Simple queries ("What is 5+3?") skip vector search entirely
- Documentation queries call `search_msi_documentation` tool only when needed

**Cost savings vs. old middleware approach:**
- **Before:** Vector search + LLM call on EVERY request (even "hello")
- **After:** LLM decides if docs are needed
- **Savings:** ~60-90% reduction in unnecessary retrievals

---

## 🔐 OpenAI Platform Limits (You Must Configure)

### **Step 1: Set Monthly Budget Cap**

1. Go to [OpenAI Platform → Billing](https://platform.openai.com/settings/organization/billing/overview)
2. Click **"Usage limits"**
3. Set **"Monthly budget"**:
   - **Recommended starting point:** $10-20/month
   - Conservative estimate: $10 = ~66,000 GPT-4o-mini requests
4. Set **"Email notification threshold"**:
   - **Recommended:** 80% ($8 if $10 budget)
   - You'll get an email when you hit this threshold

**What happens when you hit the limit:**
- ✅ OpenAI stops serving your requests automatically
- ✅ You get an email notification
- ✅ No surprise charges

### **Step 2: Monitor Usage**

**Real-time dashboard:**
- [Usage Dashboard](https://platform.openai.com/usage)
- Shows: Requests, tokens, costs (updated every ~15 minutes)

**Key metrics to watch:**
- **Requests per day:** Should stay under ~3,000 with rate limiter (120 RPM × 25 minutes/day usage)
- **Tokens per request:** GPT-4o-mini typical = 500-1500 tokens
- **Daily cost:** Should be < $0.33/day ($10/month ÷ 30 days)

### **Step 3: Project-Level Limits (Optional)**

For production deployments with multiple teams:

1. Go to [OpenAI Projects](https://platform.openai.com/projects)
2. Create a project for "MSI AI Assistant"
3. Set project-specific limits:
   - **Service tier limits** (Tier 1 = 200 RPM for GPT-4o-mini)
   - **Project budget** (separate from org budget)

---

## 📊 Cost Estimation

### **Current Configuration Costs**

| Metric | Value | Monthly Cost (30 days) |
|--------|-------|------------------------|
| Rate limit | 120 RPM | - |
| Active usage | 8 hours/day | - |
| Requests/month | ~172,800 | - |
| Avg tokens/request | 750 | ~130M tokens |
| **GPT-4o-mini** | $0.15/1M input | **~$19.50/month** |
| **GPT-4o** | $2.50/1M input | **~$325/month** |

**With Agentic RAG savings (50% fewer requests):**
- GPT-4o-mini: **~$9.75/month**
- GPT-4o: **~$162.50/month**

### **Adjusting Rate Limits**

**To reduce costs further:**

Edit [`src/main.py:48-52`](src/main.py#L48-L52) and [`src/api_server.py:71-75`](src/api_server.py#L71-L75):

```python
# More aggressive limiting
rate_limiter = InMemoryRateLimiter(
    requests_per_second=1,  # 60 RPM instead of 120
    max_bucket_size=5,      # Smaller bursts
)
```

**To increase throughput (if budget allows):**

```python
# Higher limits (monitor costs!)
rate_limiter = InMemoryRateLimiter(
    requests_per_second=5,  # 300 RPM
    max_bucket_size=20,
)
```

---

## ⚠️ What If I Hit Limits?

### **Rate Limiter Hit**
**Symptom:** Requests wait/queue (slower responses)
**Solution:** Requests automatically wait in queue, then process
**No cost impact:** Blocked requests don't charge

### **Tool Call Limit Hit**
**Symptom:** Agent response says "I've reached my limit..."
**Solution:** Agent returns partial answer (still useful)
**Action:** Check logs for runaway loops, adjust limit if needed

### **OpenAI Budget Hit**
**Symptom:** `401 Unauthorized` or quota error
**Solution:** Increase monthly budget or wait until next month
**Prevention:** Set email alerts at 80% to get warning

### **OpenAI Rate Limit Hit**
**Symptom:** `429 Too Many Requests` error
**Solution:** Our rate limiter should prevent this, but if it happens:
1. Check if multiple processes are running
2. Reduce `requests_per_second` in config
3. Upgrade to higher [OpenAI tier](https://platform.openai.com/docs/guides/rate-limits#usage-tiers)

---

## 🎯 Recommended Setup for Production

1. **Set OpenAI monthly budget:** $50/month (safe for moderate production use)
2. **Set email alert:** 80% ($40)
3. **Monitor daily:** Check usage dashboard weekly
4. **Start conservative:** Keep rate limiter at 2 RPS, increase if needed
5. **Use GPT-4o-mini:** 10x cheaper than GPT-4o, still excellent quality
6. **Enable logging:** Check `logs/` directory for usage patterns

---

## 🔧 Advanced: Per-Tool Rate Limiting

If you want to limit specific tools (e.g., expensive weather API):

```python
# Limit only the weather tool
weather_limit = ToolCallLimitMiddleware(
    tool_name="get_weather",  # Specific tool
    run_limit=3,  # Max 3 weather calls per query
)

# Limit all tools globally
global_limit = ToolCallLimitMiddleware(
    run_limit=15,  # Total limit across all tools
)

agent = create_agent(
    model,
    tools=all_tools,
    middleware=[weather_limit, global_limit],  # Both limits active
)
```

---

## 📚 Additional Resources

- [OpenAI Rate Limits Guide](https://platform.openai.com/docs/guides/rate-limits)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [LangChain Rate Limiting Docs](https://docs.langchain.com/oss/python/langchain/models#rate-limiting)
- [Tool Call Limits Middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in#tool-call-limit)

---

## 🆘 Quick Reference

| Protection Layer | Location | Purpose | Adjustable? |
|-----------------|----------|---------|-------------|
| Rate Limiter | `main.py:48`, `api_server.py:71` | Prevent rapid-fire requests | ✅ Yes |
| Tool Call Limit | `main.py:174`, `api_server.py:180` | Stop runaway loops | ✅ Yes |
| Agentic RAG | `main.py:95`, `api_server.py:111` | Reduce unnecessary retrievals | ✅ Yes (via system prompt) |
| OpenAI Budget | OpenAI Platform | Hard cost cap | ✅ Yes (on platform) |
| OpenAI Tier Limits | OpenAI Platform | Per-model RPM caps | ❌ No (tier-based) |

---

**Last updated:** 2025-12-03
**Maintained by:** MSI AI Team
