<template>
  <div class="app-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">账户设置</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">
              {{ userInfo?.username }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ userInfo?.email || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag v-for="role in userInfo?.roles" :key="role" type="primary" class="mr-2">
                {{ role }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 修改邮箱 -->
        <el-tab-pane label="修改邮箱" name="email">
          <el-form
            ref="emailFormRef"
            :model="emailForm"
            :rules="emailRules"
            label-width="100px"
            style="max-width: 500px"
          >
            <el-form-item label="当前邮箱">
              <el-input :value="userInfo?.email || '未设置'" disabled />
            </el-form-item>
            <el-form-item label="新邮箱" prop="email">
              <el-input v-model="emailForm.email" placeholder="请输入新邮箱" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="emailLoading" @click="handleUpdateEmail">
                更新邮箱
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="100px"
            style="max-width: 500px"
          >
            <el-form-item label="新密码" prop="password">
              <el-input
                v-model="passwordForm.password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordLoading" @click="handleUpdatePassword">
                更新密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { getCurrentUserApi, updateCurrentUserApi } from '@/common/apis/users'
import type { CurrentUserResponseData } from '@/common/apis/users/type'

const activeTab = ref('info')
const userInfo = ref<CurrentUserResponseData['data']>()

// 邮箱表单
const emailFormRef = ref<FormInstance>()
const emailLoading = ref(false)
const emailForm = reactive({
  email: ''
})

const emailRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 密码表单
const passwordFormRef = ref<FormInstance>()
const passwordLoading = ref(false)
const passwordForm = reactive({
  password: '',
  confirmPassword: ''
})

const validatePasswordConfirm = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== passwordForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validatePasswordConfirm, trigger: 'blur' }
  ]
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await getCurrentUserApi()
    userInfo.value = response.data
  } catch (error) {
    ElMessage.error('获取用户信息失败')
    console.error(error)
  }
}

// 更新邮箱
const handleUpdateEmail = async () => {
  if (!emailFormRef.value) return

  await emailFormRef.value.validate(async (valid) => {
    if (!valid) return

    emailLoading.value = true
    try {
      await updateCurrentUserApi({ email: emailForm.email })
      ElMessage.success('邮箱更新成功')
      await fetchUserInfo()
      emailForm.email = ''
      emailFormRef.value?.resetFields()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '邮箱更新失败')
      console.error(error)
    } finally {
      emailLoading.value = false
    }
  })
}

// 更新密码
const handleUpdatePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    passwordLoading.value = true
    try {
      await updateCurrentUserApi({ password: passwordForm.password })
      ElMessage.success('密码更新成功，请重新登录')

      // 清空表单
      passwordForm.password = ''
      passwordForm.confirmPassword = ''
      passwordFormRef.value?.resetFields()

      // 3秒后跳转到登录页
      setTimeout(() => {
        // 清除token并跳转
        localStorage.clear()
        window.location.href = '/login'
      }, 3000)
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '密码更新失败')
      console.error(error)
    } finally {
      passwordLoading.value = false
    }
  })
}

onMounted(() => {
  fetchUserInfo()
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

.mr-2 {
  margin-right: 8px;
}
</style>
