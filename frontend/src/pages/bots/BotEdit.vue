<template>
  <div class="app-container">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="title">编辑机器人</span>
          <el-button text @click="handleCancel">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        class="bot-form"
      >
        <!-- 基础配置 -->
        <el-divider content-position="left">基础配置</el-divider>

        <el-form-item label="机器人名称" prop="bot_name">
          <el-input
            v-model="form.bot_name"
            placeholder="请输入机器人名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="交易所账户">
          <el-input :value="exchangeName" disabled />
          <div class="form-tip">交易所账户不可修改</div>
        </el-form-item>

        <el-form-item label="统计开始时间">
          <el-input :value="formatDateTime(form.start_time)" disabled />
          <div class="form-tip">统计开始时间不可修改</div>
        </el-form-item>

        <!-- 市场配置 -->
        <el-divider content-position="left">市场配置</el-divider>

        <el-form-item label="市场1">
          <el-input :value="form.market1_symbol" disabled />
          <div class="form-tip">市场不可修改</div>
        </el-form-item>

        <el-form-item label="市场2">
          <el-input :value="form.market2_symbol" disabled />
          <div class="form-tip">市场不可修改</div>
        </el-form-item>

        <!-- 订单配置 -->
        <el-divider content-position="left">订单配置</el-divider>

        <el-form-item label="开仓订单类型" prop="order_type_open">
          <el-radio-group v-model="form.order_type_open">
            <el-radio value="market">市价单(Market)</el-radio>
            <el-radio value="limit">限价单(Limit)</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="平仓订单类型" prop="order_type_close">
          <el-radio-group v-model="form.order_type_close">
            <el-radio value="market">市价单(Market)</el-radio>
            <el-radio value="limit">限价单(Limit)</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="每单投资额" prop="investment_per_order">
          <el-input-number
            v-model="form.investment_per_order"
            :min="1"
            :max="100000"
            :precision="2"
            :step="10"
            style="width: 200px"
          />
          <span class="ml-2">USD</span>
        </el-form-item>

        <el-form-item label="最大持仓面值" prop="max_position_value">
          <el-input-number
            v-model="form.max_position_value"
            :min="form.investment_per_order"
            :max="1000000"
            :precision="2"
            :step="100"
            style="width: 200px"
          />
          <span class="ml-2">USD</span>
        </el-form-item>

        <el-form-item label="账户杠杆" prop="leverage">
          <el-radio-group v-model="form.leverage">
            <el-radio :value="1">1x</el-radio>
            <el-radio :value="2">2x</el-radio>
            <el-radio :value="3">3x</el-radio>
            <el-radio :value="5">5x</el-radio>
            <el-radio :value="10">10x</el-radio>
            <el-radio :value="20">20x</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- DCA配置 -->
        <el-divider content-position="left">DCA加仓配置</el-divider>

        <el-form-item label="下单次数" prop="max_dca_times">
          <el-input-number
            v-model="form.max_dca_times"
            :min="1"
            :max="10"
            @change="handleDcaTimesChange"
          />
        </el-form-item>

        <el-form-item label="DCA详细配置">
          <el-table :data="form.dca_config" border style="width: 100%">
            <el-table-column prop="times" label="次数" width="80" />
            <el-table-column label="下单价差(%)">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.spread"
                  :min="0.1"
                  :max="100"
                  :precision="2"
                  :step="0.1"
                  size="small"
                />
              </template>
            </el-table-column>
            <el-table-column label="倍投倍数">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.multiplier"
                  :min="0.1"
                  :max="100"
                  :precision="1"
                  :step="0.1"
                  size="small"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-form-item>

        <!-- 止盈止损 -->
        <el-divider content-position="left">止盈止损配置</el-divider>

        <el-form-item label="止盈模式" prop="profit_mode">
          <el-radio-group v-model="form.profit_mode">
            <el-radio value="position">仓位止盈</el-radio>
            <el-radio value="regression">回归止盈</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="止盈比例" prop="profit_ratio">
          <el-input-number
            v-model="form.profit_ratio"
            :min="-100"
            :max="100"
            :precision="2"
            :step="0.1"
            style="width: 200px"
          />
          <span class="ml-2">%</span>
        </el-form-item>

        <el-form-item label="止损比例" prop="stop_loss_ratio">
          <el-input-number
            v-model="form.stop_loss_ratio"
            :min="0"
            :max="100"
            :precision="2"
            :step="1"
            style="width: 200px"
          />
          <span class="ml-2">%</span>
          <div class="form-tip">
            整个仓位亏损达到此比例时触发止损<br />
            <span style="color: #e6a23c">💡 设置为 0 可禁用止损，一直扛单等待止盈（风险较高）</span>
          </div>
        </el-form-item>

        <el-form-item label="触发暂停" prop="pause_after_close">
          <el-switch
            v-model="form.pause_after_close"
            active-text="平仓后暂停"
            inactive-text="永不暂停"
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            保存修改
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { BotResponse, BotUpdateRequest } from '@/common/apis/bots/type'
import type { ExchangeAccountResponse } from '@/common/apis/exchanges/type'
import { getBotDetail, updateBot } from '@/common/apis/bots'
import { getExchangeAccountDetail } from '@/common/apis/exchanges'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)

// 表单数据
const form = reactive<BotUpdateRequest>({
  bot_name: '',
  order_type_open: 'market',
  order_type_close: 'market',
  investment_per_order: 0,
  max_position_value: 0,
  leverage: 10,
  max_dca_times: 6,
  dca_config: [],
  profit_mode: 'position',
  profit_ratio: 1.0,
  stop_loss_ratio: 10.0,
  pause_after_close: true
})

const originalBot = ref<BotResponse>()
const exchangeName = ref('')

// 表单验证规则
const rules = reactive<FormRules>({
  bot_name: [
    { required: true, message: '请输入机器人名称', trigger: 'blur' }
  ]
})

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// DCA次数变化处理
const handleDcaTimesChange = (value: number) => {
  const currentLength = form.dca_config!.length
  if (value > currentLength) {
    for (let i = currentLength; i < value; i++) {
      form.dca_config!.push({
        times: i + 1,
        spread: 1.0,
        multiplier: 1.0
      })
    }
  } else if (value < currentLength) {
    form.dca_config = form.dca_config!.slice(0, value)
  }
}

// 获取机器人详情
const fetchBotDetail = async () => {
  const botId = Number(route.params.id)
  if (!botId) {
    ElMessage.error('机器人ID无效')
    router.push('/bots/list')
    return
  }

  loading.value = true
  try {
    const bot = await getBotDetail(botId)
    originalBot.value = bot

    // 填充表单
    Object.assign(form, {
      bot_name: bot.bot_name,
      order_type_open: bot.order_type_open,
      order_type_close: bot.order_type_close,
      investment_per_order: bot.investment_per_order,
      max_position_value: bot.max_position_value,
      leverage: bot.leverage,
      max_dca_times: bot.max_dca_times,
      dca_config: JSON.parse(JSON.stringify(bot.dca_config)),
      profit_mode: bot.profit_mode,
      profit_ratio: bot.profit_ratio,
      stop_loss_ratio: bot.stop_loss_ratio,
      pause_after_close: bot.pause_after_close,
      market1_symbol: bot.market1_symbol,
      market2_symbol: bot.market2_symbol,
      start_time: bot.start_time
    })

    // 获取交易所名称
    const exchange = await getExchangeAccountDetail(bot.exchange_account_id)
    exchangeName.value = exchange.exchange_name
  } catch (error) {
    ElMessage.error('获取机器人详情失败')
    console.error(error)
    router.push('/bots/list')
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value || !originalBot.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await updateBot(originalBot.value!.id, form)
      ElMessage.success('机器人更新成功')
      router.push('/bots/list')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '更新失败')
      console.error(error)
    } finally {
      submitting.value = false
    }
  })
}

// 取消操作
const handleCancel = () => {
  router.push('/bots/list')
}

// 初始化
onMounted(() => {
  fetchBotDetail()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title {
    font-size: 18px;
    font-weight: 600;
  }
}

.bot-form {
  max-width: 800px;

  .form-tip {
    color: var(--el-text-color-secondary);
    font-size: 12px;
    line-height: 1.5;
    margin-top: 4px;
  }
}
</style>