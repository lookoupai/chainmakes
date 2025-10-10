<template>
  <div class="app-container">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          添加交易所账户
        </el-button>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col v-for="account in accountList" :key="account.id" :span="8" class="mb-3">
        <el-card class="exchange-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <div class="exchange-title">
                <el-icon :size="24" class="mr-2"><Connection /></el-icon>
                <span class="exchange-name">{{ account.exchange_name.toUpperCase() }}</span>
                <el-tag
                  :type="account.is_active ? 'success' : 'info'"
                  size="small"
                  class="ml-2"
                >
                  {{ account.is_active ? '已启用' : '已禁用' }}
                </el-tag>
              </div>
              <el-dropdown @command="(cmd) => handleCommand(cmd, account)">
                <el-button text circle>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="test">测试连接</el-dropdown-item>
                    <el-dropdown-item command="toggle">
                      {{ account.is_active ? '禁用' : '启用' }}
                    </el-dropdown-item>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <div class="account-info">
            <div class="info-item">
              <span class="label">API Key:</span>
              <span class="value masked">{{ maskApiKey(account.api_key) }}</span>
            </div>
            <div class="info-item">
              <span class="label">创建时间:</span>
              <span class="value">{{ formatDate(account.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">更新时间:</span>
              <span class="value">{{ formatDate(account.updated_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="accountList.length === 0 && !loading" description="还没有添加交易所账户">
      <el-button type="primary" @click="handleAdd">添加第一个账户</el-button>
    </el-empty>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="交易所" prop="exchange_name">
          <el-select
            v-model="form.exchange_name"
            placeholder="请选择交易所"
            :disabled="isEdit"
            style="width: 100%"
          >
            <el-option label="OKX" value="okx" />
            <el-option label="Binance" value="binance" disabled />
            <el-option label="Bybit" value="bybit" disabled />
          </el-select>
          <div v-if="isEdit" class="form-tip">交易所类型不可修改</div>
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            placeholder="请输入API Key"
            show-password
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="API Secret" prop="api_secret">
          <el-input
            v-model="form.api_secret"
            type="password"
            placeholder="请输入API Secret"
            show-password
            maxlength="200"
          />
        </el-form-item>

        <el-form-item
          v-if="form.exchange_name === 'okx'"
          label="Passphrase"
          prop="passphrase"
        >
          <el-input
            v-model="form.passphrase"
            type="password"
            placeholder="请输入Passphrase (OKX必填)"
            show-password
            maxlength="100"
          />
        </el-form-item>

        <el-alert
          type="warning"
          :closable="false"
          class="mb-3"
        >
          <template #title>
            <div>安全提示:</div>
            <ul style="margin: 8px 0 0 20px; font-size: 13px;">
              <li>请确保API密钥仅用于交易,不要授予提现权限</li>
              <li>建议设置IP白名单限制API访问</li>
              <li>API密钥将被加密存储</li>
            </ul>
          </template>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import type {
  ExchangeAccountResponse,
  ExchangeAccountCreateRequest,
  ExchangeAccountUpdateRequest
} from '@/common/apis/exchanges/type'
import {
  getExchangeAccounts,
  createExchangeAccount,
  updateExchangeAccount,
  deleteExchangeAccount,
  testExchangeConnection,
  toggleExchangeAccount
} from '@/common/apis/exchanges'

const loading = ref(false)
const accountList = ref<ExchangeAccountResponse[]>([])

// 对话框相关
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const editingId = ref(0)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive<ExchangeAccountCreateRequest>({
  exchange_name: 'okx',
  api_key: '',
  api_secret: '',
  passphrase: ''
})

const rules = reactive<FormRules>({
  exchange_name: [
    { required: true, message: '请选择交易所', trigger: 'change' }
  ],
  api_key: [
    { required: true, message: '请输入API Key', trigger: 'blur' }
  ],
  api_secret: [
    { required: true, message: '请输入API Secret', trigger: 'blur' }
  ],
  passphrase: [
    {
      validator: (rule, value, callback) => {
        if (form.exchange_name === 'okx' && !value) {
          callback(new Error('OKX交易所的Passphrase为必填项'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

// 脱敏显示API Key
const maskApiKey = (apiKey: string) => {
  if (!apiKey || apiKey.length < 16) return '****'
  return `${apiKey.slice(0, 8)}...${apiKey.slice(-4)}`
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取账户列表
const fetchAccounts = async () => {
  loading.value = true
  try {
    accountList.value = await getExchangeAccounts()
  } catch (error) {
    ElMessage.error('获取交易所账户列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 添加账户
const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '添加交易所账户'
  resetForm()
  dialogVisible.value = true
}

// 编辑账户
const handleEdit = (account: ExchangeAccountResponse) => {
  isEdit.value = true
  editingId.value = account.id
  dialogTitle.value = '编辑交易所账户'
  
  Object.assign(form, {
    exchange_name: account.exchange_name,
    api_key: account.api_key,
    api_secret: '',  // 出于安全考虑,不回显Secret
    passphrase: ''
  })
  
  dialogVisible.value = true
}

// 测试连接
const handleTestConnection = async (account: ExchangeAccountResponse) => {
  const loading = ElMessage({
    message: '正在测试连接...',
    type: 'info',
    duration: 0
  })

  try {
    const result = await testExchangeConnection(account.id)
    loading.close()
    
    if (result.success) {
      // 构建成功消息，包含余额信息
      let message = result.message || '连接测试成功'
      
      if (result.balance && result.balance.total) {
        const balances = Object.entries(result.balance.total)
          .filter(([_, amount]) => Number(amount) > 0)
          .map(([currency, amount]) => `${currency}: ${Number(amount).toFixed(2)}`)
          .slice(0, 5) // 只显示前5个币种
        
        if (balances.length > 0) {
          message += `\n\n账户余额:\n${balances.join('\n')}`
        }
      }
      
      ElMessageBox.alert(message, '连接测试成功', {
        confirmButtonText: '确定',
        type: 'success',
        dangerouslyUseHTMLString: false
      })
    } else {
      ElMessage.error(result.message || '连接测试失败')
    }
  } catch (error: any) {
    loading.close()
    ElMessage.error(error.response?.data?.detail || '连接测试失败')
    console.error(error)
  }
}

// 切换启用状态
const handleToggle = async (account: ExchangeAccountResponse) => {
  try {
    await toggleExchangeAccount(account.id, !account.is_active)
    ElMessage.success(account.is_active ? '已禁用' : '已启用')
    fetchAccounts()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  }
}

// 删除账户
const handleDelete = async (account: ExchangeAccountResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除交易所账户"${account.exchange_name.toUpperCase()}"吗?此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await deleteExchangeAccount(account.id)
    ElMessage.success('删除成功')
    fetchAccounts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

// 下拉菜单命令处理
const handleCommand = (command: string, account: ExchangeAccountResponse) => {
  switch (command) {
    case 'test':
      handleTestConnection(account)
      break
    case 'toggle':
      handleToggle(account)
      break
    case 'edit':
      handleEdit(account)
      break
    case 'delete':
      handleDelete(account)
      break
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        const updateData: ExchangeAccountUpdateRequest = {}
        if (form.api_key) updateData.api_key = form.api_key
        if (form.api_secret) updateData.api_secret = form.api_secret
        if (form.passphrase) updateData.passphrase = form.passphrase
        
        await updateExchangeAccount(editingId.value, updateData)
        ElMessage.success('更新成功')
      } else {
        await createExchangeAccount(form)
        ElMessage.success('添加成功')
      }
      
      dialogVisible.value = false
      fetchAccounts()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
      console.error(error)
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    exchange_name: 'okx',
    api_key: '',
    api_secret: '',
    passphrase: ''
  })
  formRef.value?.clearValidate()
}

// 对话框关闭
const handleDialogClose = () => {
  resetForm()
}

// 初始化
onMounted(() => {
  fetchAccounts()
})
</script>

<style scoped lang="scss">
.app-container {
  padding: 20px;
}

.exchange-card {
  height: 100%;

  :deep(.el-card__header) {
    padding: 15px 20px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .exchange-title {
    display: flex;
    align-items: center;

    .exchange-name {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
}

.account-info {
  .info-item {
    margin-bottom: 12px;
    display: flex;
    align-items: flex-start;

    .label {
      color: var(--el-text-color-secondary);
      margin-right: 8px;
      min-width: 80px;
    }

    .value {
      color: var(--el-text-color-primary);
      flex: 1;
      word-break: break-all;

      &.masked {
        font-family: 'Courier New', monospace;
      }
    }
  }
}

.form-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 4px;
}
</style>