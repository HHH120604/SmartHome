<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <view class="nav-left" @click="goBack">
        <text class="nav-back">←</text>
      </view>
      <view class="nav-center">
        <text class="nav-title">{{ isEdit ? '编辑日程' : '添加日程' }}</text>
      </view>
      <view class="nav-right" @click="saveSchedule">
        <text class="nav-save" :class="{ disabled: !canSave }">保存</text>
      </view>
    </view>

    <!-- 表单内容 -->
    <scroll-view class="content" scroll-y>
      <!-- 日程标题 -->
      <view class="form-section">
        <view class="form-item">
          <text class="form-label">标题</text>
          <input 
            class="form-input" 
            v-model="formData.title" 
            placeholder="请输入日程标题"
            maxlength="30"
          />
        </view>
      </view>

      <!-- 日期时间 -->
      <view class="form-section">
        <view class="form-item">
          <text class="form-label">日期</text>
          <picker mode="date" :value="formData.date" @change="onDateChange">
            <view class="form-picker">
              <text class="picker-text">{{ formData.date || '请选择日期' }}</text>
              <text class="picker-arrow">></text>
            </view>
          </picker>
        </view>

        <view class="form-item">
          <text class="form-label">时间</text>
          <picker mode="time" :value="formData.time" @change="onTimeChange">
            <view class="form-picker">
              <text class="picker-text">{{ formData.time || '请选择时间' }}</text>
              <text class="picker-arrow">></text>
            </view>
          </picker>
        </view>
      </view>

      <!-- 优先级 -->
      <view class="form-section">
        <view class="section-title">
          <text class="form-label">优先级</text>
        </view>
        <view class="priority-grid">
          <view 
            v-for="priority in priorityOptions" 
            :key="priority.value"
            :class="['priority-card', priority.value, formData.priority === priority.value ? 'active' : '']"
            @click="selectPriority(priority.value)"
          >
            <text class="priority-text">{{ priority.label }}</text>
          </view>
        </view>
      </view>

      <!-- 地点 -->
      <view class="form-section">
        <view class="form-item">
          <text class="form-label">地点</text>
          <input 
            class="form-input" 
            v-model="formData.location" 
            placeholder="请输入地点"
            maxlength="50"
          />
        </view>
      </view>

      <!-- 描述 -->
      <view class="form-section">
        <view class="form-item">
          <text class="form-label">描述</text>
          <textarea 
            class="form-textarea" 
            v-model="formData.description" 
            placeholder="请输入日程描述"
            maxlength="200"
            auto-height
          ></textarea>
        </view>
      </view>

      <!-- 底部间距 -->
      <view class="bottom-space"></view>
    </scroll-view>
  </view>
</template>

<script>
import API_CONFIG from '../../utils/api-config.js'

export default {
  data() {
    return {
      isEdit: false,
      editId: null,
      formData: {
        title: '',
        date: '',
        time: '',
        location: '',
        description: '',
        priority: 'medium',
        completed: false
      },
      priorityOptions: [
        { label: '低', value: 'low' },
        { label: '中', value: 'medium' },
        { label: '高', value: 'high' }
      ],
      saving: false
    };
  },
  computed: {
    canSave() {
      return this.formData.title.trim() && this.formData.date && this.formData.time && !this.saving;
    }
  },
  onLoad(options) {
    // 获取传递的参数
    if (options.date) {
      this.formData.date = options.date;
    } else {
      this.formData.date = this.getTodayString();
    }
    
    if (options.time) {
      this.formData.time = options.time;
    } else {
      this.formData.time = this.getCurrentTime();
    }

    // 如果是编辑模式
    if (options.id) {
      this.isEdit = true;
      this.editId = options.id;
      this.loadEditData();
    }
  },
  methods: {
    // 加载编辑数据
    async loadEditData() {
      try {
        const response = await this.makeRequest('GET', `${API_CONFIG.ENDPOINTS.GET_SCHEDULES}/${this.editId}`);
        
        if (response) {
          this.formData = {
            title: response.title || '',
            date: this.formatDate(new Date(response.date)),
            time: this.formatTime(response.startTime),
            location: response.location || '',
            description: response.description || '',
            priority: response.priority || 'medium',
            completed: response.completed || false
          };
        }
      } catch (error) {
        console.error('加载编辑数据失败:', error);
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        });
      }
    },

    // 通用HTTP请求方法
    makeRequest(method, url, data = null) {
      return new Promise((resolve, reject) => {
        const requestOptions = {
          url: `${API_CONFIG.BASE_URL}${url}`,
          method: method,
          timeout: API_CONFIG.TIMEOUT,
          header: API_CONFIG.HEADERS,
          success: (res) => {
            if (res.statusCode === 200 || res.statusCode === 201) {
              resolve(res.data);
            } else {
              reject(new Error(`HTTP ${res.statusCode}: ${res.data?.message || '请求失败'}`));
            }
          },
          fail: (err) => {
            reject(err);
          }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
          requestOptions.data = data;
        }
        
        uni.request(requestOptions);
      });
    },

    // 格式化日期
    formatDate(date) {
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      return `${year}-${month}-${day}`;
    },

    // 格式化时间
    formatTime(timeString) {
      if (!timeString) return '09:00';
      
      if (typeof timeString === 'number') {
        const time = new Date(timeString);
        const hours = time.getHours().toString().padStart(2, '0');
        const minutes = time.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
      }
      
      if (typeof timeString === 'string' && timeString.includes(':')) {
        return timeString;
      }
      
      return '09:00';
    },

    // 获取今天日期字符串
    getTodayString() {
      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth() + 1;
      const day = today.getDate();
      return `${year}-${month < 10 ? '0' + month : month}-${day < 10 ? '0' + day : day}`;
    },

    // 获取当前时间
    getCurrentTime() {
      const now = new Date();
      let hours = now.getHours();
      let minutes = Math.ceil(now.getMinutes() / 15) * 15;
      
      if (minutes >= 60) {
        hours += 1;
        minutes = 0;
      }
      
      return `${hours < 10 ? '0' + hours : hours}:${minutes === 0 ? '00' : (minutes < 10 ? '0' + minutes : minutes)}`;
    },

    // 日期选择
    onDateChange(e) {
      this.formData.date = e.detail.value;
    },

    // 时间选择
    onTimeChange(e) {
      this.formData.time = e.detail.value;
    },

    // 选择优先级
    selectPriority(priority) {
      this.formData.priority = priority;
    },

    // 保存日程
    async saveSchedule() {
      if (!this.canSave) {
        uni.showToast({
          title: '请填写必填项',
          icon: 'none'
        });
        return;
      }

      this.saving = true;

      try {
        const scheduleData = {
              title: this.formData.title.trim(),
              date: this.formData.date,
              time: this.formData.time, // 将 startTime 修改为 time
              // endTime: this.calculateEndTime(this.formData.time), // 移除 endTime 字段
              location: this.formData.location.trim(),
              description: this.formData.description.trim(),
              priority: this.formData.priority,
              // completed: this.formData.completed, // 移除 completed 字段
              // 如果后端需要，可以添加一个默认的 reminder 字段
              reminder: '15' // 例如，或者从表单获取
            };
			
        let response;
       if (this.isEdit) {
             // 注意：编辑模式(PUT)可能需要不同的数据结构，
             // 如果编辑也报错，需要检查后端的 ScheduleUpdate 模型
             response = await this.makeRequest('PUT', `${API_CONFIG.ENDPOINTS.UPDATE_SCHEDULE}/${this.editId}`, scheduleData);
           } else {
             // 新增模式 - 创建日程
             response = await this.makeRequest('POST', API_CONFIG.ENDPOINTS.ADD_SCHEDULE, scheduleData);
           }
           
           // ... (后面的代码不变, 但需要修改成功判断的逻辑)
           // 后端成功后直接返回数据，而不是 { success: true }
           if (response) {
               uni.showToast({
                 title: this.isEdit ? '更新成功' : '添加成功',
                 icon: 'success'
               });
       
               // 延迟返回，让用户看到成功提示
               setTimeout(() => {
                 this.goBack();
               }, 1500);
           } else {
             throw new Error(response?.message || '操作失败');
           }

      } catch (error) {
        console.error('保存日程失败:', error);
        uni.showToast({
          title: error.message || '保存失败',
          icon: 'none'
        });
      } finally {
        this.saving = false;
      }
    },

    // 计算结束时间（默认1小时后）
    calculateEndTime(startTime) {
      const [hours, minutes] = startTime.split(':').map(Number);
      let endHours = hours + 1;
      let endMinutes = minutes;

      if (endHours >= 24) {
        endHours = 23;
        endMinutes = 59;
      }

      return `${endHours.toString().padStart(2, '0')}:${endMinutes.toString().padStart(2, '0')}`;
    },

    // 返回
    goBack() {
      uni.navigateBack();
    }
  }
};
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f8f9fa;
}

.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #e6e6e6;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.nav-left {
  width: 120rpx;
}

.nav-back {
  font-size: 36rpx;
  color: #007AFF;
  font-weight: bold;
}

.nav-center {
  flex: 1;
  text-align: center;
}

.nav-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.nav-right {
  width: 120rpx;
  text-align: right;
}

.nav-save {
  font-size: 28rpx;
  color: #007AFF;
  font-weight: 500;
}

.nav-save.disabled {
  color: #ccc;
}

.content {
  padding-top: 88rpx;
  height: calc(100vh - 88rpx);
}

.form-section {
  background: #fff;
  margin-bottom: 20rpx;
  padding: 32rpx;
}

.form-item {
  display: flex;
  align-items: center;
  min-height: 88rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.form-item:last-child {
  border-bottom: none;
}

.form-label {
  width: 120rpx;
  font-size: 28rpx;
  color: #333;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  font-size: 28rpx;
  color: #333;
  padding: 20rpx 0;
}

.form-picker {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
}

.picker-text {
  font-size: 28rpx;
  color: #333;
}

.picker-arrow {
  font-size: 24rpx;
  color: #ccc;
}

.form-textarea {
  flex: 1;
  min-height: 200rpx;
  font-size: 28rpx;
  color: #333;
  padding: 20rpx 0;
  line-height: 1.5;
}

.section-title {
  margin-bottom: 24rpx;
}

.priority-grid {
  display: flex;
  gap: 24rpx;
}

.priority-card {
  flex: 1;
  padding: 24rpx 16rpx;
  text-align: center;
  background: #f8f9fa;
  border-radius: 12rpx;
  border: 2rpx solid transparent;
}

.priority-card:active {
  opacity: 0.7;
}

.priority-card.active {
  background: rgba(0, 122, 255, 0.1);
  border-color: #007AFF;
}

.priority-card.high.active {
  background: rgba(255, 71, 87, 0.1);
  border-color: #ff4757;
}

.priority-card.low.active {
  background: rgba(46, 213, 115, 0.1);
  border-color: #2ed573;
}

.priority-text {
  font-size: 26rpx;
  color: #666;
}

.priority-card.active .priority-text {
  color: #007AFF;
  font-weight: 500;
}

.priority-card.high.active .priority-text {
  color: #ff4757;
}

.priority-card.low.active .priority-text {
  color: #2ed573;
}

.bottom-space {
  height: 100rpx;
}
</style>