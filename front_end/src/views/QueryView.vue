<template>
  <div class="query-page">
    <div class="content-wrap">
      <!-- Hero：只做“问答状态面板” -->
      <div class="hero-card shadow-sm overflow-hidden mb-4">
        <div class="hero-bg"></div>
        <div class="hero-mask"></div>

        <div class="p-4 p-lg-5 position-relative text-white">
          <div class="row g-4 align-items-start">
            <!-- 左侧标题区 -->
            <div class="col-12 col-lg-7">
              <div class="text-uppercase small opacity-75 mb-2">图谱问答</div>
              <h2 class="fw-bold mb-2">Knowledge Graph · 查询面板</h2>
              <div class="opacity-90">
                输入问题 → 返回答案 → 查看证据 / 流程 / 调试 / 历史
              </div>

              <div class="mt-3 d-flex flex-wrap gap-2">
                <button class="btn btn-sm btn-light" type="button" @click="tab='历史'">
                  打开历史
                </button>
                <button class="btn btn-sm btn-outline-light" type="button" @click="settingsOpen = true">
                  设置
                </button>
              </div>
            </div>

            <!-- 右侧指标区（更像旧版那种“上方一排卡片”） -->
            <div class="col-12 col-lg-5">
              <div class="hero-metrics">
                <div class="hero-pill">
                  <div class="k">状态</div>
                  <div class="v">{{ loading ? '查询中…' : (result ? '已完成' : '待查询') }}</div>
                </div>
                <div class="hero-pill">
                  <div class="k">耗时</div>
                  <div class="v">{{ latencyMs === null ? '—' : (latencyMs + 'ms') }}</div>
                </div>
                <div class="hero-pill">
                  <div class="k">来源</div>
                  <div class="v">{{ result?.source ? result.source : '—' }}</div>
                </div>
                <div class="hero-pill">
                  <div class="k">历史</div>
                  <div class="v">{{ history.length }} 条</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Hero 底部小条，增加“厚度”和层次 -->
          <div class="hero-bottom mt-4">
            <span class="badge text-bg-light border me-2">接口：/api/query_v2</span>
            <span class="badge text-bg-light border me-2">Vue 3 · Bootstrap 5</span>
            <span class="badge text-bg-light border">模板 / 历史 / 证据 / 流程 / 调试</span>
          </div>
        </div>
      </div>

      <!-- 主卡片（内容不变，只调整视觉层次） -->
      <div class="card main-card border-0 shadow-sm">
        <div class="card-body p-4 p-lg-5">
          <!-- 快捷模板 -->
          <div class="mb-4">
            <div class="d-flex flex-wrap align-items-center gap-2">
              <div class="fw-semibold">快捷模板</div>
              <div class="small text-muted">（点击填充；☆收藏；自动记录最近使用）</div>

              <button class="btn btn-sm btn-outline-secondary ms-auto" type="button" @click="shuffleTemplates">
                换一批
              </button>
            </div>

            <div class="d-flex flex-wrap gap-2 mt-2">
              <button
                v-for="t in templatesShown"
                :key="t"
                type="button"
                class="btn btn-sm rounded-pill"
                :class="isFav(t) ? 'btn-outline-warning' : 'btn-outline-secondary'"
                @click="applyTemplate(t)"
                :title="t"
              >
                <span class="me-1">{{ t }}</span>
                <span class="ms-1" style="cursor:pointer" @click.stop="toggleFav(t)">
                  {{ isFav(t) ? '★' : '☆' }}
                </span>
              </button>
            </div>

            <div v-if="recentTemplates.length" class="mt-2 small text-muted">
              最近使用：
              <span
                v-for="t in recentTemplates"
                :key="t"
                class="badge text-bg-light border me-2 mb-1 template-chip"
                @click="applyTemplate(t)"
              >{{ t }}</span>
            </div>
          </div>

          <!-- 输入 -->
          <label class="form-label fw-semibold" for="q">请输入问题</label>
          <div class="input-group">
            <input
              id="q"
              v-model="query"
              class="form-control"
              :class="inputError ? 'is-invalid' : ''"
              :disabled="loading"
              placeholder="例如：歌曲兰亭序的作词人是？"
              @keyup.enter="toQuery"
            />
            <button class="btn btn-outline-secondary" type="button" :disabled="loading" @click="clearAll">清空</button>
            <button class="btn btn-primary" type="button" :disabled="loading || !query.trim()" @click="toQuery">
              <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
              开始查询
            </button>
          </div>
          <div v-if="inputError" class="invalid-feedback d-block mt-1">{{ inputError }}</div>

          <!-- 结果概览（无“可信度/可能幻觉”） -->
          <div class="mt-4 p-3 p-lg-4 rounded-4 border result-surface" :class="resultBoxClass">
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
              <div class="d-flex align-items-center gap-2 flex-wrap">
                <span class="fw-semibold">{{ statusLabel }}</span>

                <span v-if="latencyMs !== null" class="badge bg-light text-dark border">
                  耗时：{{ latencyMs }}ms
                </span>

                <span v-if="result?.source" class="badge" :class="sourceBadgeClass">
                  来源：{{ result.source }}
                </span>

                <span v-if="result?.stage_4_match_result !== undefined" class="badge"
                      :class="result.stage_4_match_result ? 'bg-success' : 'bg-secondary'">
                  匹配：{{ result.stage_4_match_result ? '是' : '否' }}
                </span>
              </div>

              <div class="d-flex gap-2 flex-wrap">
                <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!finalAnswerText"
                        @click="copyText(finalAnswerText)">复制答案</button>
                <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!result"
                        @click="copyText(prettyJson)">复制 JSON</button>
                <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!result"
                        @click="downloadJson">下载 JSON</button>
                <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="loading"
                        @click="toQuery">重试</button>
              </div>
            </div>

            <div class="mt-3">
              <div v-if="loading" class="placeholder-glow">
                <span class="placeholder col-8"></span>
                <span class="placeholder col-6"></span>
              </div>

              <div v-else-if="finalAnswerText" class="fs-4 fw-bold text-break">{{ finalAnswerText }}</div>
              <div v-else class="text-muted">暂无结果（请输入问题并查询）</div>
            </div>
          </div>

          <!-- Tabs：我们只用 Bootstrap 的样式，不靠它的 JS（更稳定） -->
          <ul class="nav nav-tabs mt-4">
            <li class="nav-item">
              <button class="nav-link" :class="{active: tab==='答案'}" @click="tab='答案'">答案</button>
            </li>
            <li class="nav-item">
              <button class="nav-link" :class="{active: tab==='证据'}" @click="tab='证据'">证据</button>
            </li>
            <li class="nav-item">
              <button class="nav-link" :class="{active: tab==='流程'}" @click="tab='流程'">流程</button>
            </li>
            <li class="nav-item">
              <button class="nav-link" :class="{active: tab==='调试'}" @click="tab='调试'">调试</button>
            </li>
            <li class="nav-item">
              <button class="nav-link" :class="{active: tab==='历史'}" @click="tab='历史'">
                历史 <span class="badge bg-secondary ms-1">{{ history.length }}</span>
              </button>
            </li>
          </ul>

          <div class="border border-top-0 rounded-bottom-4 p-3 p-lg-4 tab-surface">
            <!-- 答案 -->
            <div v-show="tab==='答案'">
              <div class="row g-3">
                <div class="col-12 col-lg-6">
                  <div class="p-3 p-lg-4 rounded-4 border bg-light h-100">
                    <div class="small text-muted fw-semibold mb-1">LLM 原始回答（llm_answer）</div>
                    <div v-if="loading" class="placeholder-glow">
                      <span class="placeholder col-10"></span>
                      <span class="placeholder col-7"></span>
                    </div>
                    <div v-else class="text-break">{{ safeText(result?.llm_answer) }}</div>
                  </div>
                </div>

                <div class="col-12 col-lg-6">
                  <div class="p-3 p-lg-4 rounded-4 border bg-light h-100">
                    <div class="small text-muted fw-semibold mb-1">KG 候选答案（kg_answers）</div>
                    <div v-if="loading" class="placeholder-glow">
                      <span class="placeholder col-8"></span>
                      <span class="placeholder col-6"></span>
                    </div>
                    <div v-else>
                      <ul class="mb-0" v-if="kgAnswersList.length">
                        <li v-for="(a,i) in kgAnswersList" :key="i" class="text-break">{{ a }}</li>
                      </ul>
                      <div class="text-muted" v-else>（无）</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 证据 -->
            <div v-show="tab==='证据'">
              <div class="d-flex flex-wrap gap-2 align-items-center mb-2">
                <div class="fw-semibold">三元组证据</div>
                <span class="badge bg-secondary">抽取 {{ extractedTriples.length }}</span>
                <span class="badge bg-secondary">KG 命中 {{ kgTriples.length }}</span>

                <div class="ms-auto d-flex gap-2">
                  <input class="form-control form-control-sm" style="width: 220px"
                         v-model="tripleFilter" placeholder="筛选：包含关键字…" />
                  <button class="btn btn-sm btn-outline-secondary" type="button" @click="tripleFilter=''">清除</button>
                </div>
              </div>

              <div class="row g-3">
                <div class="col-12 col-lg-6">
                  <div class="p-3 rounded-4 border">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div class="fw-semibold">抽取三元组（stage_2_extracted_triples）</div>
                      <button class="btn btn-sm btn-outline-secondary" type="button"
                              :disabled="!filteredExtractedTriples.length"
                              @click="copyText(JSON.stringify(filteredExtractedTriples, null, 2))">
                        复制
                      </button>
                    </div>

                    <div v-if="loading" class="placeholder-glow">
                      <span class="placeholder col-12"></span>
                      <span class="placeholder col-10"></span>
                    </div>

                    <div v-else-if="filteredExtractedTriples.length" class="table-responsive">
                      <table class="table table-sm align-middle mb-0">
                        <thead>
                          <tr>
                            <th style="width: 32%">主体</th>
                            <th style="width: 26%">关系</th>
                            <th>客体</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(t, i) in filteredExtractedTriples" :key="i">
                            <td class="text-break">{{ t.s }}</td>
                            <td class="text-break">{{ t.p }}</td>
                            <td class="text-break">{{ t.o }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    <div v-else class="text-muted">（无）</div>
                  </div>
                </div>

                <div class="col-12 col-lg-6">
                  <div class="p-3 rounded-4 border">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div class="fw-semibold">KG 命中三元组（stage_3_kg_triples）</div>
                      <button class="btn btn-sm btn-outline-secondary" type="button"
                              :disabled="!filteredKgTriples.length"
                              @click="copyText(JSON.stringify(filteredKgTriples, null, 2))">
                        复制
                      </button>
                    </div>

                    <div v-if="loading" class="placeholder-glow">
                      <span class="placeholder col-12"></span>
                      <span class="placeholder col-9"></span>
                    </div>

                    <div v-else-if="filteredKgTriples.length" class="table-responsive">
                      <table class="table table-sm align-middle mb-0">
                        <thead>
                          <tr>
                            <th style="width: 32%">主体</th>
                            <th style="width: 26%">关系</th>
                            <th>客体</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(t, i) in filteredKgTriples" :key="i">
                            <td class="text-break">{{ t.s }}</td>
                            <td class="text-break">{{ t.p }}</td>
                            <td class="text-break">{{ t.o }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    <div v-else class="text-muted">（无）</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 流程：stage 数字排序修复 2341 -->
            <div v-show="tab==='流程'">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <div class="fw-semibold">流程详情（stage_*）</div>
                <div class="d-flex gap-2">
                  <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!stageItems.length"
                          @click="openAllStages">全部展开</button>
                  <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!stageItems.length"
                          @click="closeAllStages">全部折叠</button>
                </div>
              </div>

              <div v-if="!stageItems.length" class="text-muted">（没有 stage_* 字段可展示）</div>

              <div v-else class="stage-list">
                <div v-for="it in stageItems" :key="it.key" class="stage-item border rounded-4 mb-2 overflow-hidden">
                  <button class="stage-head w-100 text-start" type="button" @click="toggleStage(it.key)">
                    <div class="d-flex align-items-center justify-content-between gap-2">
                      <div class="fw-semibold">
                        {{ it.title }}
                        <span class="badge bg-secondary ms-2" v-if="it.count != null">{{ it.count }}</span>
                      </div>
                      <span class="text-muted small">{{ isStageOpen(it.key) ? '收起' : '展开' }}</span>
                    </div>
                  </button>

                  <div v-show="isStageOpen(it.key)" class="stage-body">
                    <pre class="mb-0 small bg-light border-top p-3 text-break">{{ it.pretty }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <!-- 调试 -->
            <div v-show="tab==='调试'">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <div class="fw-semibold">原始返回 JSON</div>
                <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!result" @click="copyText(prettyJson)">
                  复制
                </button>
              </div>
              <pre class="mb-0 small bg-light border rounded-4 p-3 text-break">{{ prettyJson }}</pre>
            </div>

            <!-- 历史 -->
            <div v-show="tab==='历史'">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <div class="fw-semibold">查询历史（本地保存）</div>
                <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="!history.length"
                        @click="clearHistory">清空历史</button>
              </div>

              <div v-if="!history.length" class="text-muted">（暂无历史）</div>

              <div v-else class="list-group">
                <div class="list-group-item" v-for="item in history" :key="item.id">
                  <div class="d-flex justify-content-between align-items-start gap-2">
                    <div class="flex-grow-1">
                      <div class="fw-semibold text-break">{{ item.question }}</div>
                      <div class="small text-muted">
                        {{ item.time }} · {{ item.latencyMs }}ms · 来源={{ item.source || '—' }}
                      </div>
                      <div class="small mt-1 text-break">
                        <span class="text-muted">答案：</span>{{ item.final_answer || '（无）' }}
                      </div>
                    </div>

                    <div class="d-flex flex-column gap-2">
                      <button class="btn btn-sm btn-outline-primary" type="button" @click="restoreFromHistory(item)">
                        回放
                      </button>
                      <button class="btn btn-sm btn-outline-secondary" type="button" @click="copyText(item.rawJson)">
                        复制 JSON
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="small text-muted mt-2">
                历史数据保存在浏览器本地，刷新页面也不会丢。
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-top small text-muted d-flex flex-wrap justify-content-between gap-2">
            <div>© KG-homework · 图谱问答</div>
            <div>接口：/api/query_v2</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置弹窗 -->
    <div v-if="settingsOpen">
      <div class="modal-backdrop fade show"></div>
      <div class="modal fade show d-block" tabindex="-1" role="dialog" aria-modal="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content rounded-4">
            <div class="modal-header">
              <h5 class="modal-title">设置</h5>
              <button type="button" class="btn-close" @click="settingsOpen = false"></button>
            </div>

            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">请求超时（ms）</label>
                <input class="form-control" type="number" v-model.number="timeoutMs" min="1000" step="500">
              </div>

              <div class="mb-3">
                <label class="form-label">历史条数上限</label>
                <input class="form-control" type="number" v-model.number="historyLimit" min="5" step="5">
              </div>

              <div class="mb-0 form-check">
                <input class="form-check-input" type="checkbox" id="autoSwitchToAnswer" v-model="autoSwitchToAnswer">
                <label class="form-check-label" for="autoSwitchToAnswer">
                  查询完成后自动切回“答案”页
                </label>
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-outline-secondary" type="button" @click="settingsOpen = false">关闭</button>
              <button class="btn btn-primary" type="button" @click="applySettings">保存</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast.show" class="toast-lite">{{ toast.text }}</div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      tab: '答案',

      query: '',
      inputError: '',
      loading: false,
      statusLabel: '等待查询',
      latencyMs: null,

      // settings
      settingsOpen: false,
      timeoutMs: 20000,
      historyLimit: 30,
      autoSwitchToAnswer: true,

      result: null,

      templatesAll: [
        '歌曲兰亭序所属的音乐专辑是？',
        '歌曲兰亭序的作词人是？',
        '演唱兰亭序的歌手是？',
        '专辑魔杰座包含的歌曲是？',
        '周杰伦演唱的歌曲有？',
        '方文山作词的歌曲有？',
        '周杰伦合作过的人有？'
      ],
      templatesShown: [],
      favTemplates: [],
      recentTemplates: [],

      history: [],

      tripleFilter: '',
      openStages: [],

      toast: { show: false, text: '', timer: null }
    }
  },

  computed: {
    finalAnswerText() {
      return this.result?.final_answer ? String(this.result.final_answer) : ''
    },
    prettyJson() {
      try { return JSON.stringify(this.result, null, 2) } catch { return String(this.result) }
    },
    resultBoxClass() {
      if (!this.result) return 'border-secondary-subtle bg-light'
      if (this.result?.source === 'llm_unverified') return 'border-warning bg-warning-subtle'
      return 'border-success bg-success-subtle'
    },
    sourceBadgeClass() {
      if (!this.result?.source) return 'bg-secondary'
      return this.result.source === 'llm_unverified' ? 'bg-warning text-dark' : 'bg-info text-dark'
    },
    kgAnswersList() {
      const v = this.result?.kg_answers
      if (v == null) return []
      if (Array.isArray(v)) return v.map(x => String(x))
      if (typeof v === 'string') return v.split(/\n|;|；/).map(s => s.trim()).filter(Boolean)
      return [String(v)]
    },
    extractedTriples() {
      return this.normalizeTriples(this.result?.stage_2_extracted_triples)
    },
    kgTriples() {
      return this.normalizeTriples(this.result?.stage_3_kg_triples)
    },
    filteredExtractedTriples() {
      return this.filterTriples(this.extractedTriples)
    },
    filteredKgTriples() {
      return this.filterTriples(this.kgTriples)
    },
    stageItems() {
      if (!this.result) return []
      const keys = Object.keys(this.result).filter(k => k.startsWith('stage_'))
      keys.sort((a, b) => {
        const na = parseInt(a.match(/^stage_(\d+)/)?.[1] || '0', 10)
        const nb = parseInt(b.match(/^stage_(\d+)/)?.[1] || '0', 10)
        return na - nb
      })

      const titleMap = {
        stage_1_llm_raw: 'Stage 1：LLM 原始输出（stage_1_llm_raw）',
        stage_2_extracted_triples: 'Stage 2：抽取三元组（stage_2_extracted_triples）',
        stage_3_kg_triples: 'Stage 3：KG 命中三元组（stage_3_kg_triples）',
        stage_4_match_result: 'Stage 4：匹配结果（stage_4_match_result）'
      }

      return keys.map((key) => {
        const v = this.result[key]
        const title = titleMap[key] || key
        const pretty = this.safePretty(v)
        let count = null
        if (Array.isArray(v)) count = v.length
        return { key, title, pretty, count }
      })
    }
  },

  mounted() {
    this.loadFav()
    this.loadRecent()
    this.loadHistory()
    this.loadSettings()
    this.shuffleTemplates()
  },

  methods: {
    loadSettings() {
      try {
        const s = JSON.parse(localStorage.getItem('kg_query_settings') || '{}')
        if (typeof s.timeoutMs === 'number') this.timeoutMs = s.timeoutMs
        if (typeof s.historyLimit === 'number') this.historyLimit = s.historyLimit
        if (typeof s.autoSwitchToAnswer === 'boolean') this.autoSwitchToAnswer = s.autoSwitchToAnswer
      } catch {}
    },
    applySettings() {
      localStorage.setItem('kg_query_settings', JSON.stringify({
        timeoutMs: this.timeoutMs,
        historyLimit: this.historyLimit,
        autoSwitchToAnswer: this.autoSwitchToAnswer
      }))
      this.settingsOpen = false
      this.toastMsg('已保存设置')
    },

    shuffleTemplates() {
      const arr = [...this.templatesAll]
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[arr[i], arr[j]] = [arr[j], arr[i]]
      }
      this.templatesShown = arr.slice(0, 6)
    },
    applyTemplate(t) {
      this.query = t
      this.inputError = ''
      this.recentTemplates = [t, ...this.recentTemplates.filter(x => x !== t)].slice(0, 6)
      localStorage.setItem('kg_recent_templates', JSON.stringify(this.recentTemplates))
    },
    toggleFav(t) {
      const set = new Set(this.favTemplates)
      if (set.has(t)) set.delete(t)
      else set.add(t)
      this.favTemplates = Array.from(set)
      localStorage.setItem('kg_fav_templates', JSON.stringify(this.favTemplates))
    },
    isFav(t) { return this.favTemplates.includes(t) },
    loadFav() {
      try { this.favTemplates = JSON.parse(localStorage.getItem('kg_fav_templates') || '[]') } catch { this.favTemplates = [] }
    },
    loadRecent() {
      try { this.recentTemplates = JSON.parse(localStorage.getItem('kg_recent_templates') || '[]') } catch { this.recentTemplates = [] }
    },

    loadHistory() {
      try { this.history = JSON.parse(localStorage.getItem('kg_query_history_v2') || '[]') } catch { this.history = [] }
    },
    saveHistory() {
      localStorage.setItem('kg_query_history_v2', JSON.stringify(this.history))
    },
    pushHistory(entry) {
      this.history = [entry, ...this.history].slice(0, this.historyLimit)
      this.saveHistory()
    },
    clearHistory() {
      this.history = []
      this.saveHistory()
      this.toastMsg('历史已清空')
    },
    restoreFromHistory(item) {
      this.query = item.question
      try { this.result = JSON.parse(item.rawJson) } catch { this.result = null }
      this.latencyMs = item.latencyMs
      this.statusLabel = '已从历史回放'
      this.tab = '答案'
      this.toastMsg('已回放历史记录')
    },

    clearAll() {
      this.query = ''
      this.inputError = ''
      this.result = null
      this.statusLabel = '等待查询'
      this.latencyMs = null
      this.tripleFilter = ''
      this.openStages = []
      this.tab = '答案'
    },

    async postJson(url, body, timeoutMs) {
      const payload = JSON.stringify(body)
      const headers = { 'Content-Type': 'application/json' }

      if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
        const res = await fetch(url, { method: 'POST', headers, body: payload, signal: AbortSignal.timeout(timeoutMs) })
        return res
      }

      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), timeoutMs)
      try {
        const res = await fetch(url, { method: 'POST', headers, body: payload, signal: controller.signal })
        return res
      } finally {
        clearTimeout(timer)
      }
    },

    async toQuery() {
      const q = this.query.trim()
      this.inputError = ''

      if (!q) {
        this.inputError = '问题不能为空'
        return
      }

      this.loading = true
      this.result = null
      this.statusLabel = '查询中…'
      this.latencyMs = null
      this.openStages = []

      const t0 = (performance?.now ? performance.now() : Date.now())
      try {
        const res = await this.postJson('/api/query_v2', { question: q }, this.timeoutMs)
        const t1 = (performance?.now ? performance.now() : Date.now())
        this.latencyMs = Math.round(t1 - t0)

        if (!res.ok) {
          this.statusLabel = '查询失败'
          this.toastMsg(`请求失败：HTTP ${res.status}`)
          return
        }

        const data = await res.json()
        this.result = data || {}
        this.statusLabel = '查询完成'

        if (this.result && typeof this.result === 'object') {
          const hasStage4 = Object.prototype.hasOwnProperty.call(this.result, 'stage_4_match_result')
          this.openStages = hasStage4 ? ['stage_4_match_result'] : []
        }

        this.pushHistory({
          id: String(Date.now()),
          time: new Date().toLocaleString(),
          question: q,
          latencyMs: this.latencyMs,
          source: this.result?.source ?? '',
          final_answer: this.result?.final_answer ?? '',
          rawJson: JSON.stringify(this.result || {}, null, 2)
        })

        if (this.autoSwitchToAnswer) this.tab = '答案'
      } catch (e) {
        const t1 = (performance?.now ? performance.now() : Date.now())
        this.latencyMs = Math.round(t1 - t0)
        this.statusLabel = '查询失败'

        const msg = (e && (e.name === 'AbortError' || e.name === 'TimeoutError'))
          ? '请求超时，请增大超时或检查后端'
          : '请求失败，请检查后端/代理'
        this.toastMsg(msg)
      } finally {
        this.loading = false
      }
    },

    normalizeTriples(v) {
      if (v == null) return []
      const arr = Array.isArray(v) ? v : [v]
      const out = []

      for (const item of arr) {
        if (Array.isArray(item) && item.length >= 3) {
          out.push({ s: String(item[0]), p: String(item[1]), o: String(item[2]) })
          continue
        }
        if (item && typeof item === 'object') {
          const s = item.s ?? item.subject ?? item.sub ?? item.head ?? ''
          const p = item.p ?? item.predicate ?? item.rel ?? item.relation ?? ''
          const o = item.o ?? item.object ?? item.obj ?? item.tail ?? ''
          out.push({ s: String(s), p: String(p), o: String(o) })
        }
      }
      return out.filter(t => (t.s || t.p || t.o))
    },

    filterTriples(list) {
      const kw = (this.tripleFilter || '').trim()
      if (!kw) return list
      return list.filter(t => `${t.s} ${t.p} ${t.o}`.includes(kw))
    },

    isStageOpen(key) { return this.openStages.includes(key) },
    toggleStage(key) {
      const set = new Set(this.openStages)
      if (set.has(key)) set.delete(key)
      else set.add(key)
      this.openStages = Array.from(set)
    },
    openAllStages() { this.openStages = this.stageItems.map(x => x.key) },
    closeAllStages() { this.openStages = [] },

    safeText(v) {
      if (v == null) return '（无）'
      if (typeof v === 'string') return v
      return this.safePretty(v)
    },
    safePretty(v) {
      try { return JSON.stringify(v ?? null, null, 2) } catch { return String(v) }
    },

    async copyText(text) {
      const t = String(text ?? '')
      if (!t) return
      try {
        await navigator.clipboard.writeText(t)
        this.toastMsg('已复制到剪贴板')
      } catch {
        this.toastMsg('复制失败（权限限制）')
      }
    },

    downloadJson() {
      try {
        const blob = new Blob([this.prettyJson], { type: 'application/json;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `kg_query_${Date.now()}.json`
        a.click()
        URL.revokeObjectURL(url)
        this.toastMsg('已下载 JSON')
      } catch {
        this.toastMsg('下载失败')
      }
    },

    toastMsg(text) {
      this.toast.text = text
      this.toast.show = true
      if (this.toast.timer) clearTimeout(this.toast.timer)
      this.toast.timer = setTimeout(() => (this.toast.show = false), 1600)
    }
  }
}
</script>

<style scoped>
/* 页面背景做得更“产品化”，而不是纯白 */
.query-page{
  min-height: 100vh;
  background:
    radial-gradient(1200px 600px at 20% 0%, rgba(13,110,253,.10), rgba(0,0,0,0) 60%),
    linear-gradient(#f6f7fb, #f3f4f7);
}

/* 关键：内容居中 + max-width（类似 Bootstrap container 的思路） */
/* Bootstrap 容器就是在断点变化时给 max-width :contentReference[oaicite:1]{index=1} */
.content-wrap{
  max-width: 1120px;
  margin: 24px auto 56px;
  padding: 0 18px;
}

/* Hero 更“厚”、更像旧截图那种比例 */
.hero-card{
  position: relative;
  border-radius: 22px;
  background: #0b1b3a;
}
.hero-bg{
  position:absolute; inset:0;
  background: radial-gradient(1200px 600px at 12% 0%, rgba(13,110,253,.58), rgba(0,0,0,.58));
  transform: scale(1.03);
}
.hero-mask{
  position:absolute; inset:0;
  background: linear-gradient(120deg, rgba(0,0,0,.26), rgba(0,0,0,.62));
}
.hero-metrics{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  justify-content: flex-start;
}
@media (min-width: 992px){
  .hero-metrics{ justify-content: flex-end; }
}

.hero-pill{
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
  padding: 12px 14px;
  border-radius: 14px;
  min-width: 150px;
}
.hero-pill .k{ font-size: 12px; opacity: .8; }
.hero-pill .v{ font-weight: 800; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.hero-bottom{
  display:flex;
  flex-wrap: wrap;
  gap: 8px;
  opacity: .95;
}

/* 主卡片更厚、更圆润 */
.main-card{
  border-radius: 22px;
  overflow: hidden;
}
.result-surface{
  box-shadow: 0 10px 26px rgba(17,24,39,.06);
}

/* Tabs 内容区更像“嵌入式面板”而不是平铺 */
.tab-surface{
  background: #fff;
}

.template-chip { cursor: pointer; user-select: none; }
.template-chip:hover { filter: brightness(0.98); }

.stage-head { background:#fff; border:0; padding: 12px 14px; }
.stage-head:hover { background:#f8f9fa; }
.stage-body pre { white-space: pre-wrap; }

/* toast */
.toast-lite{
  position: fixed; right: 18px; bottom: 18px;
  background: #111; color: #fff;
  padding: 10px 12px; border-radius: 12px;
  box-shadow: 0 12px 30px rgba(0,0,0,.18);
  z-index: 2000; font-weight: 700;
}
</style>
