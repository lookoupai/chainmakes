<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">创建交易机器人</span>
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

        <el-form-item label="交易所账户" prop="exchange_account_id">
          <el-select
            v-model="form.exchange_account_id"
            placeholder="请选择交易所账户"
            style="width: 100%"
            @change="handleExchangeChange"
          >
            <el-option
              v-for="exchange in exchangeList"
              :key="exchange.id"
              :label="`${exchange.exchange_name} (${exchange.api_key ? exchange.api_key.slice(0, 8) + '...' : '未配置'})`"
              :value="exchange.id"
            />
          </el-select>
          <el-link
            type="primary"
            :underline="false"
            class="mt-2"
            @click="handleAddExchange"
          >
            + 添加新的交易所账户
          </el-link>
        </el-form-item>

        <el-form-item label="统计开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择统计开始时间(UTC)"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            style="width: 100%"
            :disabled-date="disabledFutureDate"
          />
          <div class="form-tip">
            <strong>统计开始时间(UTC时区):</strong><br>
            • 如果选择历史时间,系统将自动获取该时间点的历史价格作为起始价格<br>
            • 如果选择当前时间,系统将使用实时市场价格作为起始价格<br>
            • 所有价差计算都将基于此起始价格进行统计<br>
            • 建议选择有足够历史数据的时间点(如7天内)
          </div>
        </el-form-item>

        <!-- 市场配置 -->
        <el-divider content-position="left">市场配置</el-divider>

        <el-form-item label="市场1" prop="market1_symbol">
          <el-select
            v-model="form.market1_symbol"
            filterable
            placeholder="请选择交易对"
            style="width: 100%"
          >
            <el-option
              v-for="symbol in symbolList"
              :key="symbol"
              :label="symbol"
              :value="symbol"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="市场2" prop="market2_symbol">
          <el-select
            v-model="form.market2_symbol"
            filterable
            placeholder="请选择交易对"
            style="width: 100%"
          >
            <el-option
              v-for="symbol in symbolList"
              :key="symbol"
              :label="symbol"
              :value="symbol"
            />
          </el-select>
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
          <div class="form-tip">单次开仓的基础投资金额</div>
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
          <div class="form-tip">允许持有的双币种总仓位价值上限</div>
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
          <div class="form-tip">最多允许加仓的次数</div>
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
          <div class="form-tip mt-2">
            价差相对上次成交计算,倍投相对每单投资额计算
          </div>
        </el-form-item>

        <!-- 止盈止损 -->
        <el-divider content-position="left">止盈止损配置</el-divider>

        <el-form-item label="止盈模式" prop="profit_mode">
          <el-radio-group v-model="form.profit_mode">
            <el-radio value="position">仓位止盈</el-radio>
            <el-radio value="regression">回归止盈</el-radio>
          </el-radio-group>
          <div class="form-tip">
            仓位止盈: 多空两个仓位利润之和达到止盈比例<br>
            回归止盈: 价差回归到开仓附近并保证开仓单利润达标
          </div>
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
          <div class="form-tip">
            达到此比例时触发平仓,可设为0或负数以尽快平仓
          </div>
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
          <div class="form-tip">
            平仓后暂停: 止盈后机器人将停止运行<br>
            永不暂停: 止盈后自动进入下一循环
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            创建机器人
          </el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { BotCreateRequest, DCAConfig } from '@/common/apis/bots/type'
import type { ExchangeAccountResponse } from '@/common/apis/exchanges/type'
import { createBot } from '@/common/apis/bots'
import { getExchangeAccounts, getExchangeSymbols } from '@/common/apis/exchanges'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 表单数据
const form = reactive<BotCreateRequest>({
  bot_name: '',
  exchange_account_id: 0,
  market1_symbol: '',
  market2_symbol: '',
  start_time: new Date().toISOString(),
  leverage: 10,
  order_type_open: 'market',
  order_type_close: 'market',
  investment_per_order: 25,
  max_position_value: 250,
  max_dca_times: 6,
  dca_config: [],
  profit_mode: 'position',
  profit_ratio: 1.0,
  stop_loss_ratio: 10.0,
  pause_after_close: true
})

// 交易所列表
const exchangeList = ref<ExchangeAccountResponse[]>([])
const symbolList = ref<string[]>([])

// 表单验证规则
const rules = reactive<FormRules>({
  bot_name: [
    { required: true, message: '请输入机器人名称', trigger: 'blur' }
  ],
  exchange_account_id: [
    { required: true, message: '请选择交易所账户', trigger: 'change' }
  ],
  start_time: [
    { required: true, message: '请选择统计开始时间', trigger: 'change' }
  ],
  market1_symbol: [
    { required: true, message: '请选择市场1', trigger: 'change' }
  ],
  market2_symbol: [
    { required: true, message: '请选择市场2', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (value === form.market1_symbol) {
          callback(new Error('市场2不能与市场1相同'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  investment_per_order: [
    { required: true, message: '请输入每单投资额', trigger: 'blur' }
  ],
  max_position_value: [
    { required: true, message: '请输入最大持仓面值', trigger: 'blur' }
  ]
})

// 初始化DCA配置
const initDcaConfig = () => {
  form.dca_config = Array.from({ length: form.max_dca_times }, (_, index) => ({
    times: index + 1,
    spread: 1.0,
    multiplier: 1.0
  }))
}

// DCA次数变化处理
const handleDcaTimesChange = (value: number) => {
  const currentLength = form.dca_config.length
  if (value > currentLength) {
    // 添加新的配置
    for (let i = currentLength; i < value; i++) {
      form.dca_config.push({
        times: i + 1,
        spread: 1.0,
        multiplier: 1.0
      })
    }
  } else if (value < currentLength) {
    // 删除多余的配置
    form.dca_config = form.dca_config.slice(0, value)
  }
}

// 获取交易所列表
const fetchExchangeAccounts = async () => {
  try {
    exchangeList.value = await getExchangeAccounts()
  } catch (error) {
    ElMessage.error('获取交易所账户失败')
    console.error(error)
  }
}

// 交易所变化处理
const handleExchangeChange = async (accountId: number) => {
  const exchange = exchangeList.value.find(e => e.id === accountId)
  if (exchange) {
    try {
      const response: any = await getExchangeSymbols(exchange.exchange_name)
      // 后端返回 {symbols: [{symbol, base, quote}, ...]}
      // 提取symbol字段转为字符串数组
      if (response && response.symbols && Array.isArray(response.symbols)) {
        symbolList.value = response.symbols.map((item: any) => item.symbol)
      } else if (Array.isArray(response)) {
        // 兼容直接返回数组的情况
        symbolList.value = response.map((item: any) => item.symbol || item)
      } else {
        symbolList.value = []
        ElMessage.warning('交易对列表格式不正确')
      }
    } catch (error) {
      ElMessage.error('获取交易对列表失败')
      console.error(error)
    }
  }
}

// 添加交易所账户
const handleAddExchange = () => {
  router.push('/exchanges/list')
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await createBot(form)
      ElMessage.success('机器人创建成功')
      router.push('/bots/list')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '创建失败')
      console.error(error)
    } finally {
      submitting.value = false
    }
  })
}

// 禁用未来日期
const disabledFutureDate = (time: Date) => {
  return time.getTime() > Date.now()
}

// 取消操作
const handleCancel = () => {
  router.push('/bots/list')
}

// 初始化
onMounted(() => {
  fetchExchangeAccounts()
  initDcaConfig()
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