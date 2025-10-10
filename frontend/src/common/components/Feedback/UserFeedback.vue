<template>
  <div class="user-feedback">
    <!-- 反馈按钮 -->
    <el-button
      type="primary"
      :icon="ChatDotRound"
      circle
      class="feedback-button"
      @click="showFeedbackDialog = true"
    />
    
    <!-- 反馈对话框 -->
    <el-dialog
      v-model="showFeedbackDialog"
      title="用户反馈"
      width="500px"
      :before-close="handleClose"
    >
      <el-form
        ref="feedbackFormRef"
        :model="feedbackForm"
        :rules="feedbackRules"
        label-width="80px"
      >
        <el-form-item label="反馈类型" prop="type">
          <el-select
            v-model="feedbackForm.type"
            placeholder="请选择反馈类型"
            style="width: 100%"
          >
            <el-option label="功能建议" value="feature" />
            <el-option label="问题反馈" value="bug" />
            <el-option label="使用咨询" value="question" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="反馈内容" prop="content">
          <el-input
            v-model="feedbackForm.content"
            type="textarea"
            :rows="4"
            placeholder="请详细描述您的反馈内容..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="联系方式" prop="contact">
          <el-input
            v-model="feedbackForm.contact"
            placeholder="邮箱或手机号（可选）"
          />
        </el-form-item>
        
        <el-form-item label="截图">
          <el-upload
            ref="uploadRef"
            :action="uploadUrl"
            :headers="uploadHeaders"
            :before-upload="beforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :on-remove="handleRemove"
            :file-list="fileList"
            :limit="3"
            accept="image/*"
            list-type="picture-card"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                支持jpg/png文件，单个文件不超过2MB，最多3张
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">取消</el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="submitFeedback"
          >
            提交反馈
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 成功提示 -->
    <el-dialog
      v-model="showSuccessDialog"
      title="反馈提交成功"
      width="400px"
      :show-close="false"
      :close-on-click-modal="false"
    >
      <div class="success-content">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <p>感谢您的反馈！我们会尽快处理并回复您。</p>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="showSuccessDialog = false">
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, UploadInstance } from 'element-plus'
import { ChatDotRound, Plus, CircleCheck } from '@element-plus/icons-vue'
import { getToken } from '@/common/utils/cache/cookies'
import { request } from '@/http/axios'
import { useLoading } from '@/common/utils/loading'

// 反馈对话框显示状态
const showFeedbackDialog = ref(false)
const showSuccessDialog = ref(false)

// 表单引用
const feedbackFormRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()

// 加载状态
const { isLoading: submitting, setLoading: setSubmitting } = useLoading('feedback-submit')

// 文件列表
const fileList = ref<any[]>([])

// 上传URL
const uploadUrl = `${import.meta.env.VITE_BASE_API}/api/v1/feedback/upload`

// 上传头
const uploadHeaders = {
  Authorization: `Bearer ${getToken()}`
}

// 反馈表单
const feedbackForm = reactive({
  type: '',
  content: '',
  contact: '',
  images: [] as string[]
})

// 表单验证规则
const feedbackRules = {
  type: [
    { required: true, message: '请选择反馈类型', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入反馈内容', trigger: 'blur' },
    { min: 10, message: '反馈内容至少10个字符', trigger: 'blur' }
  ]
}

// 关闭对话框
const handleClose = () => {
  if (submitting.value) return
  
  feedbackFormRef.value?.resetFields()
  fileList.value = []
  feedbackForm.images = []
  showFeedbackDialog.value = false
}

// 上传前检查
const beforeUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过2MB!')
    return false
  }
  return true
}

// 上传成功
const handleUploadSuccess = (response: any, uploadFile: any) => {
  if (response.code === 0) {
    feedbackForm.images.push(response.data.url)
    ElMessage.success('图片上传成功')
  } else {
    ElMessage.error(response.message || '图片上传失败')
    // 移除失败的文件
    const index = fileList.value.findIndex(file => file.uid === uploadFile.uid)
    if (index > -1) {
      fileList.value.splice(index, 1)
    }
  }
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('图片上传失败')
}

// 移除文件
const handleRemove = (uploadFile: any) => {
  const index = feedbackForm.images.findIndex(url => url === uploadFile.url)
  if (index > -1) {
    feedbackForm.images.splice(index, 1)
  }
}

// 提交反馈
const submitFeedback = async () => {
  if (!feedbackFormRef.value) return
  
  try {
    // 验证表单
    await feedbackFormRef.value.validate()
    
    setSubmitting(true)
    
    // 提交反馈
    const response = await request.post('/api/v1/feedback', {
      type: feedbackForm.type,
      content: feedbackForm.content,
      contact: feedbackForm.contact,
      images: feedbackForm.images
    })
    
    if (response.code === 0) {
      // 关闭反馈对话框
      handleClose()
      
      // 显示成功对话框
      showSuccessDialog.value = true
    } else {
      ElMessage.error(response.message || '反馈提交失败')
    }
  } catch (error) {
    console.error('提交反馈失败:', error)
    ElMessage.error('反馈提交失败，请稍后重试')
  } finally {
    setSubmitting(false)
  }
}
</script>

<style scoped>
.user-feedback {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.feedback-button {
  width: 50px;
  height: 50px;
  font-size: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.feedback-button:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.success-content {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  font-size: 48px;
  color: var(--el-color-success);
  margin-bottom: 16px;
}

.success-content p {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.dialog-footer {
  text-align: right;
}

:deep(.el-upload--picture-card) {
  width: 80px;
  height: 80px;
  line-height: 80px;
}

:deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 80px;
  height: 80px;
}
</style>