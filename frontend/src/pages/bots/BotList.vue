<template>
  <div class="app-container">
    <!-- 顶部操作栏 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建机器人
        </el-button>
      </el-col>
      <el-col :span="6">
        <el-select v-model="filterStatus" placeholder="筛选状态" clearable @change="handleFilter">
          <el-option label="全部" value="" />
          <el-option label="运行中" value="running" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已停止" value="stopped" />
        </el-select>
      </el-col>
    </el-row>

    <!-- 机器人列表卡片 -->
    <el-row :gutter="20">
      <el-col v-for="bot in botList" :key="bot.id" :span="24" class="mb-3">
        <el-card class="bot-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="bot-title">
                <el-icon :size="20" class="mr-2"><Robot /></el-icon>
                <span class="bot-name">{{ bot.bot_name }}</span>
                <el-tag :type="getStatusType(bot.status)" size="small" class="ml-2">
                  {{ getStatusText(bot.status) }}
                </el-tag>
              </div>
              <div class="bot-actions">
                <el-button-group>
                  <el-button
                    v-if="bot.status === 'stopped' || bot.status === 'paused'"
                    type="success"
                    size="small"
                    @click="handleStart(bot)"
                  >
                    启动
                  </el-button>
                  <el-button
                    v-if="bot.status === 'running'"
                    type="warning"
                    size="small"
                    @click="handlePause(bot)"
                  >
                    暂停
                  </el-button>
                  <el-button
                    v-if="bot.status === 'running' || bot.status === 'paused'"
                    type="danger"
                    size="small"
                    @click="handleStop(bot)"
                  >
                    停止
                  </el-button>
                  <el-button size="small" @click="handleEdit(bot)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" plain @click="handleDelete(bot)">
                    删除
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </template>

          <!-- 机器人信息 -->
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <span class="label">市场对:</span>
                <span class="value">
                  {{ bot.market1_symbol }} / {{ bot.market2_symbol }}
                </span>
              </div>
              <div class="info-item">
                <span class="label">杠杆:</span>
                <span class="value">{{ bot.leverage }}x</span>
              </div>
              <div class="info-item">
                <span class="label">止盈模式:</span>
                <span class="value">{{ bot.profit_mode === 'position' ? '仓位止盈' : '回归止盈' }}</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="label">每单投资:</span>
                <span class="value">${{ bot.investment_per_order }}</span>
              </div>
              <div class="info-item">
                <span class="label">最大持仓:</span>
                <span class="value">${{ bot.max_position_value }}</span>
              </div>
              <div class="info-item">
                <span class="label">加仓次数:</span>
                <span class="value">{{ bot.max_dca_times }}次</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <span class="label">当前循环:</span>
                <span class="value">第{{ bot.current_cycle }}轮</span>
              </div>
              <div class="info-item">
                <span class="label">总收益:</span>
                <span :class="['value', Number(bot.total_profit) >= 0 ? 'profit' : 'loss']">
                  ${{ Number(bot.total_profit).toFixed(2) }}
                </span>
              </div>
              <div class="info-item">
                <span class="label">总交易:</span>
                <span class="value">{{ bot.total_trades }}笔</span>
              </div>
            </el-col>
          </el-row>

          <!-- 底部操作 -->
          <template #footer>
            <div class="card-footer">
              <span class="created-time">
                创建时间: {{ formatDate(bot.created_at) }}
              </span>
              <el-button type="primary" link @click="handleViewDetail(bot)">
                查看详情 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <el-pagination
      v-if="total > 0"
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next, jumper"
      class="mt-4"
      @size-change="handleSizeChange"
      @current-change="handlePageChange"
    />

    <!-- 空状态 -->
    <el-empty v-if="(!botList || botList.length === 0) && !loading" description="还没有创建机器人">
      <el-button type="primary" @click="handleCreate">创建第一个机器人</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { BotResponse } from '@/common/apis/bots/type'
import {
  getBotList,
  startBot,
  pauseBot,
  stopBot,
  deleteBot
} from '@/common/apis/bots'

const router = useRouter()

// 数据状态
const botList = ref<BotResponse[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')

// 获取机器人列表
const fetchBotList = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined
    }
    const response = await getBotList(params)
    botList.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    ElMessage.error('获取机器人列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 状态显示
const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    running: 'success',
    paused: 'warning',
    stopped: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止'
  }
  return texts[status] || status
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 操作处理
const handleCreate = () => {
  router.push('/bots/create')
}

const handleEdit = (bot: BotResponse) => {
  router.push(`/bots/edit/${bot.id}`)
}

const handleViewDetail = (bot: BotResponse) => {
  router.push(`/bots/${bot.id}`)
}

const handleStart = async (bot: BotResponse) => {
  try {
    await startBot(bot.id)
    ElMessage.success('机器人已启动')
    fetchBotList()
  } catch (error) {
    ElMessage.error('启动失败')
    console.error(error)
  }
}

const handlePause = async (bot: BotResponse) => {
  try {
    await pauseBot(bot.id)
    ElMessage.success('机器人已暂停')
    fetchBotList()
  } catch (error) {
    ElMessage.error('暂停失败')
    console.error(error)
  }
}

const handleStop = async (bot: BotResponse) => {
  try {
    await ElMessageBox.confirm(
      `停止机器人"${bot.bot_name}"后将关闭所有持仓，确定要停止吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )
    await stopBot(bot.id)
    ElMessage.success('机器人已停止')
    fetchBotList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败')
      console.error(error)
    }
  }
}

const handleDelete = async (bot: BotResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除机器人"${bot.bot_name}"吗?此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    await deleteBot(bot.id)
    ElMessage.success('删除成功')
    fetchBotList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const handleFilter = () => {
  currentPage.value = 1
  fetchBotList()
}

const handlePageChange = () => {
  fetchBotList()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchBotList()
}

// 初始化
onMounted(() => {
  fetchBotList()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}

.bot-card {
  :deep(.el-card__header) {
    padding: 15px 20px;
    border-bottom: 1px solid var(--el-border-color-light);
  }

  :deep(.el-card__body) {
    padding: 20px;
  }

  :deep(.el-card__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--el-border-color-light);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .bot-title {
    display: flex;
    align-items: center;
    font-weight: 600;
    font-size: 16px;

    .bot-name {
      color: var(--el-text-color-primary);
    }
  }
}

.info-item {
  margin-bottom: 12px;
  display: flex;
  align-items: center;

  .label {
    color: var(--el-text-color-secondary);
    margin-right: 8px;
    min-width: 80px;
  }

  .value {
    color: var(--el-text-color-primary);
    font-weight: 500;

    &.profit {
      color: var(--el-color-success);
    }

    &.loss {
      color: var(--el-color-danger);
    }
  }
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .created-time {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
}
</style>