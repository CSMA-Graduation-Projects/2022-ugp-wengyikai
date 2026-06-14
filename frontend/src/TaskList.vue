<template>
  <div class="task-list-wrapper">
    <div v-if="tasks && tasks.length" class="filter-bar">
      <el-select
        v-model="selectedType"
        size="small"
        placeholder="按任务类型筛选"
        clearable
        class="filter-select"
      >
        <el-option label="前端任务" value="frontend" />
        <el-option label="后端任务" value="backend" />
        <el-option label="数据库任务" value="database" />
      </el-select>

      <el-input
        v-model="keyword"
        size="small"
        placeholder="搜索任务名称 / 故事"
        clearable
        class="filter-input"
      >
        <i slot="prefix" class="el-input__icon el-icon-search"></i>
      </el-input>

      <el-tag size="small" type="info">共 {{ filteredTasks.length }} 条</el-tag>
    </div>

    <el-table
      v-if="tasks && tasks.length"
      :data="filteredTasks"
      stripe
      border
      size="small"
      height="420"
      highlight-current-row
      @row-click="handleRowClick"
    >
      <el-table-column prop="id" label="任务ID" width="85" />
      <el-table-column prop="name" label="任务名称" min-width="180" />

      <el-table-column label="类型" width="100">
        <template slot-scope="scope">
          <el-tag size="mini" :type="taskTypeTag(scope.row.type)">
            {{ taskTypeText(scope.row.type) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="所属故事" min-width="200" show-overflow-tooltip>
        <template slot-scope="scope">
          {{ scope.row.story || '无' }}
        </template>
      </el-table-column>

      <el-table-column label="前置依赖" min-width="120">
        <template slot-scope="scope">
          <span v-if="scope.row.depends_on && scope.row.depends_on.length">
            {{ scope.row.depends_on.join(', ') }}
          </span>
          <span v-else class="empty-text">无</span>
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-else
      description="暂无任务清单数据"
      :image-size="90"
    />
  </div>
</template>

<script>
export default {
  name: 'TaskList',
  props: {
    tasks: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedType: '',
      keyword: ''
    }
  },
  computed: {
    filteredTasks() {
      return this.tasks.filter(task => {
        const matchType = this.selectedType
          ? task.type === this.selectedType
          : true

        const searchText = `${task.id || ''} ${task.name || ''} ${task.story || ''} ${(task.depends_on || []).join(' ')}`.toLowerCase()
        const matchKeyword = this.keyword
          ? searchText.includes(this.keyword.toLowerCase())
          : true

        return matchType && matchKeyword
      })
    }
  },
  methods: {
    taskTypeTag(type) {
      if (type === 'frontend') return 'primary'
      if (type === 'backend') return 'success'
      if (type === 'database') return 'warning'
      return 'info'
    },
    taskTypeText(type) {
      if (type === 'frontend') return '前端'
      if (type === 'backend') return '后端'
      if (type === 'database') return '数据库'
      return type || '未知'
    },
    handleRowClick(row) {
      this.$emit('select-story', row.story || '')
    }
  }
}
</script>

<style scoped>
.task-list-wrapper {
  width: 100%;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  align-items: center;
}

.filter-select {
  width: 160px;
}

.filter-input {
  flex: 1;
  min-width: 220px;
}

.empty-text {
  color: #909399;
}
</style>