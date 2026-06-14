<template>
  <div class="app-container">
    <el-container>
      <el-header class="app-header">
        <div class="header-title">智能用户故事生成系统</div>
        <div class="header-subtitle">
          基于大语言模型与数据库知识库的需求解析、用户故事生成、任务拆解、代码生成与实验评估平台
        </div>
      </el-header>

      <el-main class="app-main">
        <!-- ==================== 两个输入卡片行 ==================== -->
        <el-row :gutter="20" class="section-row">
          <!-- 自然语言需求卡片 -->
          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card input-card">
              <div slot="header" class="card-header">
                <span>📝 自然语言需求输入</span>
              </div>

              <el-input
                v-model="requirement"
                type="textarea"
                :rows="8"
                placeholder="请输入自然语言需求，例如：用户可以注册并登录系统查看个人信息，还可以上传头像。"
                resize="none"
              />

              <div class="demo-bar">
                <span class="demo-label">快速示例：</span>
                <el-button size="mini" plain @click="fillRequirementExample('login')">登录注册类</el-button>
                <el-button size="mini" plain @click="fillRequirementExample('shop')">电商订单支付类</el-button>
                <el-button size="mini" plain @click="fillRequirementExample('user')">用户管理类</el-button>
                <el-button size="mini" plain @click="fillRequirementExample('approval')">审批工单类</el-button>
              </div>

              <div class="action-bar">
                <el-button
                  type="primary"
                  :loading="loadingRequirement"
                  @click="generateFromRequirement"
                >
                  {{ loadingRequirement ? '生成中...' : '从需求生成并评估' }}
                </el-button>
                <el-button size="mini" plain @click="requirement = ''">清空</el-button>
              </div>
            </el-card>
          </el-col>

          <!-- 代码片段输入卡片 -->
          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card input-card">
              <div slot="header" class="card-header">
                <span>💻 代码片段输入</span>
              </div>

              <el-input
                v-model="codeInput"
                type="textarea"
                :rows="8"
                placeholder="请粘贴代码，例如 FastAPI 接口、Vue 组件、数据库定义等..."
                resize="none"
              />

              <div class="demo-bar">
                <span class="demo-label">快速示例：</span>
                <el-button size="mini" plain @click="fillCodeExample('login-api')">登录 API</el-button>
                <el-button size="mini" plain @click="fillCodeExample('cart-api')">购物车 API</el-button>
                <el-button size="mini" plain @click="fillCodeExample('user-profile')">个人信息接口</el-button>
              </div>

              <div class="action-bar">
                <el-button
                  type="success"
                  :loading="loadingCode"
                  @click="generateFromCode"
                >
                  {{ loadingCode ? '生成中...' : '从代码生成故事' }}
                </el-button>
                <el-button size="mini" plain @click="codeInput = ''">清空</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 公共操作栏（导出 & 全局重置） -->
        <div class="global-actions">
          <el-button
            type="success"
            plain
            :disabled="!canExport"
            @click="exportMarkdown"
          >
            导出 Markdown
          </el-button>

          <el-button
            type="info"
            plain
            @click="resetAll"
          >
            重置页面
          </el-button>
        </div>

        <el-alert
          v-if="message"
          :title="message"
          :type="messageType"
          show-icon
          :closable="true"
          class="section-alert"
          @close="message = ''"
        />

        <!-- ==================== 结果展示区（完全保留原有内容） ==================== -->

        <!-- 第二层：知识增强 + 结构化需求 -->
        <el-row :gutter="20" class="section-row">
          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card fixed-card">
              <div slot="header" class="card-header">
                <span>知识增强上下文</span>
              </div>

              <div v-if="knowledgeContext" class="context-box">
                <pre>{{ knowledgeContext }}</pre>
              </div>
              <el-empty
                v-else
                description="暂无知识增强内容"
                :image-size="80"
              />
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card fixed-card">
              <div slot="header" class="card-header">
                <span>结构化需求表示</span>
              </div>

              <div v-if="hasStructuredRequirement" class="structured-wrapper">
                <div class="structured-group">
                  <div class="structured-label">角色</div>
                  <div class="tag-group">
                    <el-tag
                      v-for="(item, index) in structuredRequirement.roles"
                      :key="'role-' + index"
                      size="small"
                      effect="plain"
                      class="tag-item"
                    >
                      {{ item }}
                    </el-tag>
                    <span v-if="!structuredRequirement.roles.length" class="empty-text">暂无</span>
                  </div>
                </div>

                <div class="structured-group">
                  <div class="structured-label">行为</div>
                  <div class="tag-group">
                    <el-tag
                      v-for="(item, index) in structuredRequirement.actions"
                      :key="'action-' + index"
                      size="small"
                      type="success"
                      effect="plain"
                      class="tag-item"
                    >
                      {{ item }}
                    </el-tag>
                    <span v-if="!structuredRequirement.actions.length" class="empty-text">暂无</span>
                  </div>
                </div>

                <div class="structured-group">
                  <div class="structured-label">条件</div>
                  <div class="tag-group">
                    <el-tag
                      v-for="(item, index) in structuredRequirement.conditions"
                      :key="'condition-' + index"
                      size="small"
                      type="warning"
                      effect="plain"
                      class="tag-item"
                    >
                      {{ item }}
                    </el-tag>
                    <span v-if="!structuredRequirement.conditions.length" class="empty-text">暂无</span>
                  </div>
                </div>

                <div class="structured-group">
                  <div class="structured-label">目标</div>
                  <div class="tag-group">
                    <el-tag
                      v-for="(item, index) in structuredRequirement.goals"
                      :key="'goal-' + index"
                      size="small"
                      type="danger"
                      effect="plain"
                      class="tag-item"
                    >
                      {{ item }}
                    </el-tag>
                    <span v-if="!structuredRequirement.goals.length" class="empty-text">暂无</span>
                  </div>
                </div>
              </div>

              <el-empty
                v-else
                description="暂无结构化需求结果"
                :image-size="80"
              />
            </el-card>
          </el-col>
        </el-row>

        <el-row v-if="runtimeTrace" :gutter="20" class="section-row">
          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card">
              <div slot="header" class="card-header">
                <span>知识命中证据</span>
              </div>

              <div class="trace-grid">
                <div class="trace-item">
                  <span class="trace-label">上下文来源</span>
                  <span class="trace-value">{{ knowledgeContextSourceLabel((runtimeTrace.knowledge || {}).context_source) }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">命中模块数</span>
                  <span class="trace-value">{{ (runtimeTrace.knowledge || {}).matched_count || 0 }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">知识模块总数</span>
                  <span class="trace-value">{{ (runtimeTrace.knowledge || {}).knowledge_module_total || 0 }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">覆盖分类数</span>
                  <span class="trace-value">{{ (runtimeTrace.knowledge || {}).category_total || 0 }}</span>
                </div>
              </div>

              <div class="trace-section">
                <div class="trace-label">命中模块</div>
                <div class="tag-group">
                  <el-tag
                    v-for="(item, index) in (runtimeTrace.knowledge || {}).matched_modules || []"
                    :key="'trace-module-' + index"
                    size="small"
                    type="success"
                    effect="plain"
                    class="tag-item"
                  >
                    {{ item }}
                  </el-tag>
                  <span v-if="!((runtimeTrace.knowledge || {}).matched_modules || []).length" class="empty-text">当前需求未命中专用知识库</span>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card">
              <div slot="header" class="card-header">
                <span>运行耗时证据</span>
              </div>

              <div class="trace-grid">
                <div class="trace-item">
                  <span class="trace-label">总耗时</span>
                  <span class="trace-value">{{ formatMs((runtimeTrace.performance || {}).total_ms) }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">模型耗时</span>
                  <span class="trace-value">{{ formatMs((runtimeTrace.performance || {}).model_inference_ms) }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">本地处理耗时</span>
                  <span class="trace-value">{{ formatMs((runtimeTrace.performance || {}).local_processing_ms) }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">知识匹配耗时</span>
                  <span class="trace-value">{{ formatMs((runtimeTrace.performance || {}).knowledge_processing_ms) }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">结果评估耗时</span>
                  <span class="trace-value">{{ formatMs((runtimeTrace.performance || {}).evaluation_ms) }}</span>
                </div>
                <div class="trace-item">
                  <span class="trace-label">模型状态</span>
                  <span class="trace-value">{{ generationStatusLabel((runtimeTrace.generation || {}).result_status) }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 第三层：故事列表 + 任务清单 -->
        <el-row :gutter="20" class="section-row">
          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card content-card">
              <div slot="header" class="card-header">
                <span>用户故事列表</span>
                <el-tag size="mini" type="primary">{{ stories.length }}</el-tag>
              </div>

              <StoryList
                :stories="stories"
                :selected-story="selectedStory"
                @select-story="handleSelectStory"
              />
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card shadow="hover" class="section-card content-card">
              <div slot="header" class="card-header">
                <span>任务清单</span>
                <el-tag size="mini" type="success">{{ tasks.length }}</el-tag>
              </div>

              <TaskList
                :tasks="tasks"
                @select-story="handleSelectStory"
              />
            </el-card>
          </el-col>
        </el-row>

        <!-- 第四层：用户故事相关代码生成 -->
        <el-card shadow="hover" class="section-card">
          <div slot="header" class="card-header">
            <span>用户故事相关代码生成</span>
            <el-button
              type="primary"
              size="mini"
              :loading="codeLoading"
              :disabled="!selectedStory"
              @click="generateCodeByStory"
            >
              {{ codeLoading ? '生成中...' : '一键生成相关代码' }}
            </el-button>
          </div>

          <div v-if="selectedStory" class="selected-story-box">
            <strong>当前选中用户故事：</strong>{{ selectedStory }}
          </div>
          <el-empty
            v-else
            description="请先在用户故事列表、任务清单或依赖图中选择一条用户故事"
            :image-size="80"
          />

          <div v-if="generatedCode" class="code-result-wrapper">
            <div v-if="codeGenerationTrace" class="trace-banner">
              代码生成耗时：{{ formatMs(((codeGenerationTrace.performance || {}).total_ms)) }}
              ，模型耗时：{{ formatMs((((codeGenerationTrace.generation || {}).llm_inference_ms))) }}
              ，状态：{{ generationStatusLabel((codeGenerationTrace.generation || {}).result_status) }}
            </div>

            <el-tabs type="border-card">
              <el-tab-pane label="项目结构">
                <pre>{{ formatProjectStructure(generatedCode.project_structure) }}</pre>
              </el-tab-pane>

              <el-tab-pane label="前端代码">
                <pre>{{ generatedCode.frontend_code || '暂无前端代码' }}</pre>
              </el-tab-pane>

              <el-tab-pane label="后端代码">
                <pre>{{ generatedCode.backend_code || '暂无后端代码' }}</pre>
              </el-tab-pane>

              <el-tab-pane label="数据库 SQL">
                <pre>{{ generatedCode.database_sql || '暂无数据库 SQL' }}</pre>
              </el-tab-pane>

              <el-tab-pane label="使用说明">
                <ul v-if="generatedCode.usage_notes && generatedCode.usage_notes.length" class="note-list">
                  <li
                    v-for="(note, index) in generatedCode.usage_notes"
                    :key="index"
                  >
                    {{ note }}
                  </li>
                </ul>
                <span v-else class="empty-text">暂无使用说明</span>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-card>

        <!-- 第五层：依赖图 -->
        <el-card shadow="hover" class="section-card graph-card">
          <div slot="header" class="card-header">
            <span>任务依赖关系图</span>
          </div>

          <TaskGraph
            :tasks="tasks"
            @select-story="handleSelectStory"
          />
        </el-card>

        <!-- 第六层：实验评估体系 -->
        <el-card shadow="hover" class="section-card">
          <div slot="header" class="card-header">
            <span>实验评估体系</span>
          </div>

          <div v-if="evaluation">
            <el-row :gutter="20">
              <el-col :xs="24" :md="8">
                <div class="score-box">
                  <div class="score-title">综合得分</div>
                  <div class="score-value">{{ evaluation.total_score }}</div>
                </div>
              </el-col>

              <el-col :xs="24" :md="16">
                <div class="score-summary">
                  <div class="score-title">评估结论</div>
                  <div class="score-text">{{ evaluation.summary }}</div>
                  <el-progress
                    :percentage="evaluation.total_score"
                    :stroke-width="18"
                    style="margin-top: 12px;"
                  />
                </div>
              </el-col>
            </el-row>

            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :xs="24" :md="12">
                <el-card shadow="never" class="inner-card">
                  <div slot="header">维度评分</div>
                  <p>结构化完整度：{{ safeDimensionScore('structured_completeness') }}</p>
                  <p>用户故事质量：{{ safeDimensionScore('story_quality') }}</p>
                  <p>任务拆解质量：{{ safeDimensionScore('task_quality') }}</p>
                  <p>依赖关系质量：{{ safeDimensionScore('dependency_quality') }}</p>
                </el-card>
              </el-col>

              <el-col :xs="24" :md="12">
                <el-card shadow="never" class="inner-card">
                  <div slot="header">改进建议</div>
                  <div v-if="evaluation.suggestions && evaluation.suggestions.length">
                    <el-tag
                      v-for="(item, index) in evaluation.suggestions"
                      :key="index"
                      type="warning"
                      effect="plain"
                      class="suggestion-tag"
                    >
                      {{ item }}
                    </el-tag>
                  </div>
                  <span v-else class="empty-text">暂无建议</span>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <el-empty
            v-else
            description="暂无评估结果"
            :image-size="80"
          />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import StoryList from './StoryList.vue'
import TaskList from './TaskList.vue'
import TaskGraph from './TaskGraph.vue'

const apiBaseUrl = (process.env.VUE_APP_API_BASE_URL || '/api').replace(/\/$/, '')

function buildApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${apiBaseUrl}${normalizedPath}`
}

export default {
  name: 'App',
  components: {
    StoryList,
    TaskList,
    TaskGraph
  },
  data() {
    return {
      // 两个输入框
      requirement: '',
      codeInput: '',

      // 各自的 loading
      loadingRequirement: false,
      loadingCode: false,
      codeLoading: false,

      message: '',
      messageType: 'info',

      // 共享结果
      knowledgeContext: '',
      runtimeTrace: null,
      structuredRequirement: {
        roles: [],
        actions: [],
        conditions: [],
        goals: []
      },

      stories: [],
      tasks: [],
      selectedStory: '',
      evaluation: null,
      generatedCode: null,
      codeGenerationTrace: null
    }
  },
  computed: {
    hasStructuredRequirement() {
      const s = this.structuredRequirement || {}
      return !!(
        (s.roles && s.roles.length) ||
        (s.actions && s.actions.length) ||
        (s.conditions && s.conditions.length) ||
        (s.goals && s.goals.length)
      )
    },
    canExport() {
      return !!(
        this.requirement ||
        this.codeInput ||
        this.knowledgeContext ||
        this.stories.length ||
        this.tasks.length ||
        this.evaluation ||
        this.generatedCode
      )
    }
  },
  methods: {
    // ==================== 通用请求 ====================
    async request(url, method = 'GET', body = null) {
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json'
        }
      }
      if (body) {
        options.body = JSON.stringify(body)
      }

      const response = await fetch(buildApiUrl(url), options)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || '请求失败')
      }

      if (typeof data.success !== 'undefined') {
        if (!data.success) {
          throw new Error(data.message || '请求失败')
        }
        return data.data || {}
      }

      return data
    },

    // 统一标准化后端返回
    normalizePayload(payload) {
      if (payload && payload.result) {
        return {
          knowledge_context: payload.knowledge_context || '',
          result: payload.result,
          evaluation: payload.evaluation || null,
          trace: payload.trace || null
        }
      }

      return {
        knowledge_context: '',
        result: {
          structured_requirement: payload.structured_requirement || {
            roles: [],
            actions: [],
            conditions: [],
            goals: []
          },
          user_stories: payload.user_stories || [],
          tasks: payload.tasks || []
        },
        evaluation: payload.evaluation || null,
        trace: payload.trace || null
      }
    },

    // 将标准化后的数据应用到页面
    applyResult(normalized) {
      const result = normalized.result || {}

      this.knowledgeContext = normalized.knowledge_context || ''
      this.structuredRequirement = result.structured_requirement || {
        roles: [],
        actions: [],
        conditions: [],
        goals: []
      }
      this.stories = result.user_stories || []
      this.tasks = result.tasks || []
      this.evaluation = normalized.evaluation || null
      this.runtimeTrace = normalized.trace || null
    },

    // ==================== 从自然语言需求生成 ====================
    async generateFromRequirement() {
      const text = this.requirement.trim()
      if (!text) {
        this.showMessage('请输入自然语言需求', 'warning')
        return
      }

      this.loadingRequirement = true
      this.clearResults()

      try {
        let payload
        try {
          payload = await this.request('/generate_and_evaluate', 'POST', {
            requirement: text
          })
        } catch (e) {
          payload = await this.request('/generate_story', 'POST', {
            requirement: text
          })
        }

        const normalized = this.normalizePayload(payload)
        this.applyResult(normalized)

        if (!this.knowledgeContext) {
          await this.fetchContextPreview()
        }

        this.showMessage('生成成功，可选择一条用户故事继续生成相关代码', 'success')
      } catch (error) {
        this.clearResults()
        this.showMessage(error.message || '生成失败', 'error')
      } finally {
        this.loadingRequirement = false
      }
    },

    // ==================== 从代码生成故事 ====================
async generateFromCode() {
  const code = this.codeInput.trim()
  if (!code) {
    this.showMessage('请粘贴代码片段', 'warning')
    return
  }

  this.loadingCode = true
  this.clearResults()

  try {
    const data = await this.request('/generate_story_from_code', 'POST', {
      code: code
    })
    // 现在后端会返回 evaluation
    const normalized = {
      knowledge_context: data.knowledge_context || '',
      result: data.result || {},
      evaluation: data.evaluation || null,
      trace: data.trace || null
    }
    this.applyResult(normalized)

    if (!this.knowledgeContext) {
      // 如果知识上下文为空可以不处理或尝试预览
    }

    this.showMessage('代码解析完成，已生成用户故事', 'success')
  } catch (error) {
    this.clearResults()
    this.showMessage(error.message || '代码分析失败', 'error')
  } finally {
    this.loadingCode = false
  }
},

    // 尝试获取知识增强上下文（用于自然语言模式）
    async fetchContextPreview() {
      try {
        const payload = await this.request('/preview_context', 'POST', {
          requirement: this.requirement.trim()
        })
        this.knowledgeContext = payload.knowledge_context || ''
      } catch (e) {
        this.knowledgeContext = ''
      }
    },

    // ==================== 根据选中故事生成相关代码 ====================
    async generateCodeByStory() {
      if (!this.selectedStory) {
        this.showMessage('请先选择一条用户故事', 'warning')
        return
      }

      const relatedTasks = this.tasks.filter(task => task.story === this.selectedStory)

      this.codeLoading = true
      this.generatedCode = null
      this.message = ''

      try {
        const payload = await this.request('/generate_code', 'POST', {
          requirement: this.requirement,
          story: this.selectedStory,
          tasks: relatedTasks
        })

        this.generatedCode = payload.code_result || null
        this.codeGenerationTrace = payload.trace || null
        this.showMessage('相关代码生成成功', 'success')
      } catch (error) {
        this.generatedCode = null
        this.codeGenerationTrace = null
        this.showMessage(error.message || '代码生成失败', 'error')
      } finally {
        this.codeLoading = false
      }
    },

    // ==================== 故事选中 ====================
    handleSelectStory(story) {
      this.selectedStory = story || ''
      this.generatedCode = null
      this.codeGenerationTrace = null
    },

    // ==================== 示例填充 ====================
    fillRequirementExample(type) {
      if (type === 'login') {
        this.requirement = '用户可以注册账号并登录系统查看个人信息，还可以上传头像，系统需要支持密码校验和登录失败提示。'
      } else if (type === 'shop') {
        this.requirement = '用户可以浏览商品，加入购物车，提交订单并完成在线支付，同时可以查看订单状态和支付结果。'
      } else if (type === 'user') {
        this.requirement = '管理员登录后可以查看用户列表、修改用户状态、重置用户密码，并对不同角色分配访问权限。'
      } else if (type === 'approval') {
        this.requirement = '员工可以提交工单申请，部门负责人可以审批工单，系统需要记录审批意见并向申请人发送消息通知。'
      }
    },

    fillCodeExample(type) {
      const examples = {
        'login-api': `from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    # 模拟用户验证
    if req.username != "admin" or req.password != "123456":
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": "fake-jwt-token"}`,
        'cart-api': `@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int, user_id: int):
    # 检查库存
    stock = db.query(Item).filter(Item.id == item_id).first().stock
    if stock < quantity:
        raise HTTPException(status_code=400, detail="库存不足")
    cart_item = CartItem(user_id=user_id, item_id=item_id, quantity=quantity)
    db.add(cart_item)
    db.commit()
    return {"message": "加入购物车成功"}`,
        'user-profile': `@app.get("/user/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "avatar": current_user.avatar
    }`
      }
      this.codeInput = examples[type] || ''
    },

    // ==================== 清空 & 重置 ====================
    clearResults() {
      this.knowledgeContext = ''
      this.runtimeTrace = null
      this.structuredRequirement = {
        roles: [],
        actions: [],
        conditions: [],
        goals: []
      }
      this.stories = []
      this.tasks = []
      this.selectedStory = ''
      this.evaluation = null
      this.generatedCode = null
      this.codeGenerationTrace = null
    },

    resetAll() {
      this.requirement = ''
      this.codeInput = ''
      this.clearResults()
      this.loadingRequirement = false
      this.loadingCode = false
      this.codeLoading = false
      this.message = ''
      this.messageType = 'info'
    },

    showMessage(msg, type = 'info') {
      this.message = msg
      this.messageType = type
    },

    // ==================== 辅助函数 ====================
    safeDimensionScore(key) {
      if (!this.evaluation || !this.evaluation.dimension_scores) {
        return 0
      }
      return this.evaluation.dimension_scores[key] || 0
    },

    formatMs(value) {
      return `${Number(value || 0).toFixed(2)} ms`
    },

    knowledgeContextSourceLabel(source) {
      if (source === 'knowledge_base_hit') {
        return '知识库命中'
      }
      if (source === 'fallback_general_engineering') {
        return '通用工程回退'
      }
      if (source === 'empty_knowledge_base') {
        return '知识库为空'
      }
      return '未记录'
    },

    generationStatusLabel(status) {
      if (status === 'success') {
        return '成功'
      }
      if (status === 'error') {
        return '失败'
      }
      return '未记录'
    },

    formatProjectStructure(projectStructure) {
      if (!projectStructure || !projectStructure.length) {
        return '暂无项目结构'
      }
      return projectStructure.join('\n')
    },

    // ==================== 导出 Markdown ====================
    exportMarkdown() {
      const lines = []

      lines.push('# 智能用户故事生成结果')
      lines.push('')

      lines.push('## 输入内容')
      lines.push('')
      if (this.requirement) {
        lines.push('### 自然语言需求')
        lines.push('')
        lines.push(this.requirement)
        lines.push('')
      }
      if (this.codeInput) {
        lines.push('### 代码片段')
        lines.push('')
        lines.push('```')
        lines.push(this.codeInput)
        lines.push('```')
        lines.push('')
      }

      lines.push('## 知识增强上下文')
      lines.push('')
      lines.push('```')
      lines.push(this.knowledgeContext || '无')
      lines.push('```')
      lines.push('')

      lines.push('## 运行证据')
      lines.push('')
      if (this.runtimeTrace) {
        lines.push(`- 上下文来源：${this.knowledgeContextSourceLabel((this.runtimeTrace.knowledge || {}).context_source)}`)
        lines.push(`- 命中模块：${((this.runtimeTrace.knowledge || {}).matched_modules || []).join('、') || '无'}`)
        lines.push(`- 知识模块总数：${(this.runtimeTrace.knowledge || {}).knowledge_module_total || 0}`)
        lines.push(`- 覆盖分类数：${(this.runtimeTrace.knowledge || {}).category_total || 0}`)
        lines.push(`- 总耗时：${this.formatMs((this.runtimeTrace.performance || {}).total_ms)}`)
        lines.push(`- 模型耗时：${this.formatMs((this.runtimeTrace.performance || {}).model_inference_ms)}`)
        lines.push(`- 本地处理耗时：${this.formatMs((this.runtimeTrace.performance || {}).local_processing_ms)}`)
      } else {
        lines.push('无')
      }
      lines.push('')

      lines.push('## 结构化需求表示')
      lines.push('')
      lines.push(`- 角色：${(this.structuredRequirement.roles || []).join('、') || '无'}`)
      lines.push(`- 行为：${(this.structuredRequirement.actions || []).join('、') || '无'}`)
      lines.push(`- 条件：${(this.structuredRequirement.conditions || []).join('、') || '无'}`)
      lines.push(`- 目标：${(this.structuredRequirement.goals || []).join('、') || '无'}`)
      lines.push('')

      lines.push('## 用户故事列表')
      lines.push('')
      if (this.stories.length) {
        this.stories.forEach((story, index) => {
          lines.push(`${index + 1}. ${story}`)
        })
      } else {
        lines.push('无')
      }
      lines.push('')

      lines.push('## 任务清单')
      lines.push('')
      if (this.tasks.length) {
        lines.push('| 任务ID | 任务名称 | 类型 | 所属故事 | 前置依赖 |')
        lines.push('| --- | --- | --- | --- | --- |')
        this.tasks.forEach(task => {
          lines.push(
            `| ${task.id || ''} | ${task.name || ''} | ${task.type || ''} | ${task.story || ''} | ${(task.depends_on || []).join('、') || '无'} |`
          )
        })
      } else {
        lines.push('无')
      }
      lines.push('')

      lines.push('## 用户故事相关代码生成')
      lines.push('')
      if (this.generatedCode) {
        lines.push(`- 当前选中用户故事：${this.selectedStory || '无'}`)
        lines.push('')
        lines.push('### 项目结构')
        lines.push('```')
        lines.push(this.formatProjectStructure(this.generatedCode.project_structure))
        lines.push('```')
        lines.push('')
        lines.push('### 前端代码')
        lines.push('```vue')
        lines.push(this.generatedCode.frontend_code || '暂无前端代码')
        lines.push('```')
        lines.push('')
        lines.push('### 后端代码')
        lines.push('```python')
        lines.push(this.generatedCode.backend_code || '暂无后端代码')
        lines.push('```')
        lines.push('')
        lines.push('### 数据库 SQL')
        lines.push('```sql')
        lines.push(this.generatedCode.database_sql || '暂无数据库 SQL')
        lines.push('```')
        lines.push('')
        lines.push('### 使用说明')
        if (this.generatedCode.usage_notes && this.generatedCode.usage_notes.length) {
          this.generatedCode.usage_notes.forEach((note, index) => {
            lines.push(`${index + 1}. ${note}`)
          })
        } else {
          lines.push('无')
        }
        lines.push('')
        lines.push('### 代码生成证据')
        if (this.codeGenerationTrace) {
          lines.push(`- 总耗时：${this.formatMs(((this.codeGenerationTrace.performance || {}).total_ms))}`)
          lines.push(`- 模型耗时：${this.formatMs((((this.codeGenerationTrace.generation || {}).llm_inference_ms)))}`)
          lines.push(`- 生成状态：${this.generationStatusLabel((this.codeGenerationTrace.generation || {}).result_status)}`)
        } else {
          lines.push('无')
        }
      } else {
        lines.push('未生成相关代码')
      }
      lines.push('')

      lines.push('## 实验评估体系')
      lines.push('')
      if (this.evaluation) {
        lines.push(`- 综合得分：${this.evaluation.total_score}`)
        lines.push(`- 评估结论：${this.evaluation.summary}`)
        lines.push(`- 结构化完整度：${this.safeDimensionScore('structured_completeness')}`)
        lines.push(`- 用户故事质量：${this.safeDimensionScore('story_quality')}`)
        lines.push(`- 任务拆解质量：${this.safeDimensionScore('task_quality')}`)
        lines.push(`- 依赖关系质量：${this.safeDimensionScore('dependency_quality')}`)
        lines.push('')
        lines.push('### 改进建议')
        if (this.evaluation.suggestions && this.evaluation.suggestions.length) {
          this.evaluation.suggestions.forEach((item, index) => {
            lines.push(`${index + 1}. ${item}`)
          })
        } else {
          lines.push('无')
        }
      } else {
        lines.push('无')
      }

      const content = lines.join('\n')
      const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'user-story-result.md'
      link.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.app-header {
  height: auto !important;
  padding: 24px 20px 16px;
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: #fff;
}

.header-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.header-subtitle {
  font-size: 14px;
  opacity: 0.95;
}

.app-main {
  padding: 20px;
}

.section-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.input-card {
  min-height: 340px;
}

.fixed-card {
  min-height: 320px;
}

.content-card {
  min-height: 520px;
}

.graph-card {
  min-height: 560px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.action-bar {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.demo-bar {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.demo-label {
  font-size: 13px;
  color: #606266;
}

.global-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.section-alert {
  margin-bottom: 20px;
}

.context-box {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  min-height: 220px;
}

.context-box pre,
.code-result-wrapper pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  font-size: 13px;
  color: #606266;
}

.code-result-wrapper pre {
  background: #f8f8f8;
  border-radius: 8px;
  padding: 12px;
  max-height: 520px;
  overflow-y: auto;
}

.structured-wrapper {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.structured-group {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fafafa;
}

.structured-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  margin-right: 0;
}

.empty-text {
  color: #909399;
  font-size: 13px;
}

.selected-story-box {
  padding: 12px;
  background: #f5f7fa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  line-height: 1.8;
  color: #303133;
}

.code-result-wrapper {
  margin-top: 16px;
}

.trace-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.trace-item {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
}

.trace-label {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.trace-value {
  font-size: 15px;
  color: #303133;
  font-weight: 600;
}

.trace-section {
  margin-top: 14px;
}

.trace-banner {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  color: #606266;
  line-height: 1.8;
}

.note-list {
  margin: 0;
  padding-left: 20px;
  line-height: 1.9;
  color: #606266;
}

.score-box,
.score-summary {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  min-height: 120px;
}

.score-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.score-value {
  font-size: 42px;
  font-weight: 700;
  color: #409EFF;
  line-height: 1;
}

.score-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
}

.inner-card {
  min-height: 180px;
}

.suggestion-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .header-title {
    font-size: 22px;
  }

  .app-main {
    padding: 12px;
  }

  .global-actions {
    flex-direction: column;
  }

  .action-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .demo-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .trace-grid {
    grid-template-columns: 1fr;
  }
}
</style>