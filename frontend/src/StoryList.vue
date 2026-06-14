<template>
  <div class="story-list-wrapper">
    <div v-if="stories && stories.length" class="story-list">
      <div
        v-for="(story, index) in stories"
        :key="index"
        :ref="'story-card-' + index"
        class="story-card"
        :class="{ active: selectedStory === story }"
        @click="handleClick(story, index)"
      >
        <div class="story-card-header">
          <div class="story-index">STORY-{{ index + 1 }}</div>
          <el-tag
            size="mini"
            :type="selectedStory === story ? 'danger' : 'primary'"
            effect="plain"
          >
            {{ selectedStory === story ? '当前选中' : '用户故事' }}
          </el-tag>
        </div>

        <div class="story-content">
          {{ story }}
        </div>

        <div class="story-footer">
          <span class="story-role">
            <i class="el-icon-user-solid"></i>
            {{ extractRole(story) || '未识别角色' }}
          </span>
          <span class="story-goal">
            <i class="el-icon-s-flag"></i>
            {{ extractGoal(story) || '未识别目标' }}
          </span>
        </div>
      </div>
    </div>

    <el-empty
      v-else
      description="暂无用户故事数据"
      :image-size="90"
    />
  </div>
</template>

<script>
export default {
  name: 'StoryList',
  props: {
    stories: {
      type: Array,
      default: () => []
    },
    selectedStory: {
      type: String,
      default: ''
    }
  },
  watch: {
    selectedStory(newVal) {
      if (!newVal) return
      const index = this.stories.findIndex(item => item === newVal)
      if (index !== -1) {
        this.$nextTick(() => {
          this.scrollToCard(index)
        })
      }
    }
  },
  methods: {
    handleClick(story, index) {
      this.$emit('select-story', story)
      this.scrollToCard(index)
    },

    scrollToCard(index) {
      const refName = 'story-card-' + index
      const target = this.$refs[refName]
      if (!target) return

      const el = Array.isArray(target) ? target[0] : target
      if (el && el.scrollIntoView) {
        el.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        })
      }
    },

    extractRole(story) {
      if (!story) return ''
      const match = story.match(/作为(.*?)，我想要/)
      return match ? match[1].trim() : ''
    },

    extractGoal(story) {
      if (!story) return ''
      const match = story.match(/以便(.*)$/)
      return match ? match[1].trim() : ''
    }
  }
}
</script>

<style scoped>
.story-list-wrapper {
  width: 100%;
  height: 100%;
}

.story-list {
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
}

.story-card {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #ffffff;
  padding: 14px 14px 12px;
  margin-bottom: 12px;
  transition: all 0.25s ease;
  cursor: pointer;
}

.story-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #c6e2ff;
  transform: translateY(-1px);
}

.story-card.active {
  border-color: #f56c6c;
  background: #fff7f7;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.12);
}

.story-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.story-index {
  font-size: 13px;
  font-weight: 700;
  color: #409eff;
  letter-spacing: 0.5px;
}

.story-content {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  word-break: break-word;
  margin-bottom: 12px;
}

.story-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #606266;
}

.story-role,
.story-goal {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f5f7fa;
  border-radius: 14px;
  padding: 4px 10px;
}

.story-list::-webkit-scrollbar {
  width: 6px;
}

.story-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.story-list::-webkit-scrollbar-track {
  background: transparent;
}
</style>