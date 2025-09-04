<template>
  <view class="page-container">
    <view class="page" :style="{ 
      backgroundImage: 'url(/static/img/home_bg.png)', 
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundAttachment: 'fixed'
    }">
      <!-- 顶部标题 -->
      <view class="header">
        <text class="title">日程管理</text>
      </view>

      <!-- 月份切换器 -->
      <view class="month-switcher">
        <view class="month-btn" @click="changeMonth(-1)">
          <image src="/static/icon/arrow-left.png" class="arrow-icon" />
        </view>
        <view class="month-display">
          <text class="current-month">{{ currentYear }}年{{ currentMonth }}月</text>
        </view>
        <view class="month-btn" @click="changeMonth(1)">
          <image src="/static/icon/arrow-right.png" class="arrow-icon" />
        </view>
      </view>

      <!-- 日历模块 -->
      <view class="calendar-container">
        <view class="calendar-card">
          <!-- 星期标题 -->
          <view class="weekdays">
            <text 
              v-for="day in weekdays" 
              :key="day" 
              class="weekday-item"
            >
              {{ day }}
            </text>
          </view>
          
          <!-- 日期网格 -->
          <view class="calendar-grid">
            <view 
              v-for="(date, index) in calendarDates" 
              :key="index"
              :class="getDateClass(date)"
              @click="selectDate(date)"
            >
              <text class="date-number">{{ date.day }}</text>
              <!-- 有日程的标记点 -->
              <view 
                v-if="date.hasSchedule && date.isCurrentMonth" 
                class="schedule-dot"
                :class="{ 'active-dot': date.isSelected }"
              ></view>
            </view>
          </view>
        </view>
      </view>

      <!-- 当日行程模块 -->
      <view class="today-schedule">
        <!-- 日期显示 -->
        <view class="schedule-header">
          <text class="schedule-date">{{ selectedDateText }}</text>
          <view class="add-btn" @click="addSchedule">
            <image src="/static/icon/add.png" class="add-icon" />
            <text class="add-text">添加</text>
          </view>
        </view>

        <!-- 行程列表 -->
        <scroll-view class="schedule-scroll" scroll-y>
          <view class="schedule-list">
            <!-- 无行程时的提示 -->
            <view v-if="todaySchedules.length === 0" class="empty-schedule">
              <image src="/static/icon/calendar.png" class="empty-icon" />
              <text class="empty-text">暂无行程安排</text>
            </view>
            
            <!-- 行程项目 -->
            <view 
              v-for="(schedule, index) in todaySchedules" 
              :key="schedule.id"
              class="schedule-item"
              :class="{ 'completed': schedule.completed }"
              @click="toggleSchedule(schedule)"
            >
              <view class="schedule-left">
                <view class="time-tag" :class="schedule.priority">
                  {{ schedule.time }}
                </view>
                <view class="schedule-info">
                  <text class="schedule-title">{{ schedule.title }}</text>
                  <text class="schedule-desc" v-if="schedule.description">{{ schedule.description }}</text>
                  <text class="schedule-location" v-if="schedule.location">📍 {{ schedule.location }}</text>
                </view>
              </view>
              
              <view class="schedule-right">
                <view 
                  class="status-indicator"
                  :class="{ 
                    'completed': schedule.completed,
                    'pending': !schedule.completed && !isScheduleOverdue(schedule),
                    'overdue': isScheduleOverdue(schedule)
                  }"
                >
                  {{ getScheduleStatus(schedule) }}
                </view>
                <view class="more-btn" @click.stop="showScheduleMenu(schedule)">⋯</view>
              </view>
            </view>
          </view>
          
          <!-- 底部留白 -->
          <view class="bottom-space"></view>
        </scroll-view>
      </view>
    </view>
    
    <!-- 安全区域占位 -->
    <view class="safe-area-bottom"></view>
  </view>
</template>

<script>
import API_CONFIG from '../../utils/api-config.js'

export default {
  data() {
    return {
      currentYear: 2025,
      currentMonth: 8,
      selectedDate: null,
      weekdays: ['日', '一', '二', '三', '四', '五', '六'],
      
      // 后端数据相关
      schedules: [],
      loadingSchedules: false,
      scheduleTimer: null
    };
  },
  computed: {
    // 当前月日历数据
    calendarDates() {
      const year = this.currentYear;
      const month = this.currentMonth;
      
      // 获取当月第一天是星期几
      const firstDay = new Date(year, month - 1, 1).getDay();
      // 获取当月有多少天
      const daysInMonth = new Date(year, month, 0).getDate();
      // 获取上个月有多少天
      const prevMonthDays = new Date(year, month - 1, 0).getDate();
      
      const dates = [];
      
      // 添加上个月的日期（补齐第一行）
      for (let i = firstDay - 1; i >= 0; i--) {
        const day = prevMonthDays - i;
        const dateStr = `${year}-${month === 1 ? 12 : month - 1 < 10 ? '0' + (month - 1) : month - 1}-${day < 10 ? '0' + day : day}`;
        dates.push({
          day,
          dateStr,
          isCurrentMonth: false,
          hasSchedule: this.hasScheduleOnDate(dateStr),
          isSelected: this.isDateSelected(dateStr),
          isToday: this.isToday(dateStr)
        });
      }
      
      // 添加当月的日期
      for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${month < 10 ? '0' + month : month}-${day < 10 ? '0' + day : day}`;
        dates.push({
          day,
          dateStr,
          isCurrentMonth: true,
          hasSchedule: this.hasScheduleOnDate(dateStr),
          isSelected: this.isDateSelected(dateStr),
          isToday: this.isToday(dateStr)
        });
      }
      
      // 添加下个月的日期（补齐最后一行）
      const remainingCells = 42 - dates.length;
      for (let day = 1; day <= remainingCells; day++) {
        const nextMonth = month === 12 ? 1 : month + 1;
        const nextYear = month === 12 ? year + 1 : year;
        const dateStr = `${nextYear}-${nextMonth < 10 ? '0' + nextMonth : nextMonth}-${day < 10 ? '0' + day : day}`;
        dates.push({
          day,
          dateStr,
          isCurrentMonth: false,
          hasSchedule: this.hasScheduleOnDate(dateStr),
          isSelected: this.isDateSelected(dateStr),
          isToday: this.isToday(dateStr)
        });
      }
      
      return dates;
    },
    
    // 选中日期的文本显示
    selectedDateText() {
      if (!this.selectedDate) {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        const day = today.getDate();
        return `今天 ${month}月${day}日`;
      }
      
      const date = new Date(this.selectedDate);
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const weekday = ['日', '一', '二', '三', '四', '五', '六'][date.getDay()];
      
      if (this.isToday(this.selectedDate)) {
        return `今天 ${month}月${day}日 星期${weekday}`;
      }
      
      return `${month}月${day}日 星期${weekday}`;
    },
    
    // 当日行程列表
    todaySchedules() {
      const targetDate = this.selectedDate || this.getTodayString();
      return this.schedules.filter(schedule => 
        schedule.date === targetDate
      ).sort((a, b) => a.time.localeCompare(b.time));
    }
  },
  
  onLoad() {
    // 初始化选中今天
    this.selectedDate = this.getTodayString();
    
    // 设置当前年月为今天的年月
    const today = new Date();
    this.currentYear = today.getFullYear();
    this.currentMonth = today.getMonth() + 1;
    
    // 从后端获取日程数据
    this.fetchSchedules();
    
    // 定期刷新数据
    this.scheduleTimer = setInterval(() => {
      this.fetchSchedules();
    }, 30000); // 30秒刷新一次
  },
  
  onShow() {
    // 页面显示时刷新数据
    this.fetchSchedules();
  },
  
  onUnload() {
    if (this.scheduleTimer) {
      clearInterval(this.scheduleTimer);
    }
  },
  
  methods: {
    // 从后端获取日程数据
    async fetchSchedules() {
      if (this.loadingSchedules) return;
      
      this.loadingSchedules = true;
      try {
        const response = await this.makeRequest('GET', API_CONFIG.ENDPOINTS.GET_SCHEDULES);
        
         if (response && Array.isArray(response.schedules)) {
              // 从 response.schedules 中获取日程数组
              this.schedules = response.schedules.map(schedule => {
                      // 后端返回的数据结构中已经包含了所有需要的字段 (id, title, description, date, time, 等)
                      // 我们只需要确保 date 和 time 格式正确即可，这里甚至可以简化，因为后端格式已符合要求
                      return {
                        ...schedule,
                        // 直接使用后端返回的 time 字段，不再错误地读取 startTime
                        time: schedule.time 
                      };
                    })
        }
      } catch (error) {
        console.error('获取日程数据失败:', error);
        // 失败时使用本地模拟数据
        if (this.schedules.length === 0) {
          this.loadMockData();
        }
      } finally {
        this.loadingSchedules = false;
      }
    },
    
    // 加载模拟数据（后端连接失败时使用）
    loadMockData() {
      const mockSchedules = [
        {
          id: '1',
          title: '早上起床',
          description: '6:30起床，打开窗帘',
          time: '06:30',
          startTime: '06:30',
          endTime: '07:00',
          date: this.getTodayString(),
          location: '卧室',
          priority: 'high',
          completed: false
        },
        {
          id: '2',
          title: '下班回家',
          description: '打开空调和灯光',
          time: '18:00',
          startTime: '18:00',
          endTime: '18:30',
          date: this.getTodayString(),
          location: '客厅',
          priority: 'medium',
          completed: false
        },
        {
          id: '3',
          title: '热水器定时',
          description: '20:00自动开启热水器',
          time: '20:00',
          startTime: '20:00',
          endTime: '20:30',
          date: this.getTodayString(),
          location: '卫生间',
          priority: 'low',
          completed: false
        }
      ];
      
      this.schedules = mockSchedules;
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
            if (res.statusCode === 200) {
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
      if (!timeString) return '';
      if (typeof timeString === 'number') {
        const time = new Date(timeString);
        const hours = time.getHours().toString().padStart(2, '0');
        const minutes = time.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
      }
      return timeString;
    },
    
    // 获取今天的日期字符串
    getTodayString() {
      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth() + 1;
      const day = today.getDate();
      return `${year}-${month < 10 ? '0' + month : month}-${day < 10 ? '0' + day : day}`;
    },
    
    // 判断是否是今天
    isToday(dateStr) {
      return dateStr === this.getTodayString();
    },
    
    // 判断日期是否被选中
    isDateSelected(dateStr) {
      return this.selectedDate === dateStr;
    },
    
    // 判断指定日期是否有日程
    hasScheduleOnDate(dateStr) {
      return this.schedules.some(schedule => schedule.date === dateStr);
    },
    
    // 获取日期单元格的CSS类
    getDateClass(date) {
      const classes = ['calendar-date'];
      
      if (!date.isCurrentMonth) {
        classes.push('other-month');
      }
      
      if (date.isToday) {
        classes.push('today');
      }
      
      if (date.isSelected) {
        classes.push('selected');
      }
      
      if (date.hasSchedule && date.isCurrentMonth) {
        classes.push('has-schedule');
      }
      
      return classes;
    },
    
    // 切换月份
    changeMonth(direction) {
      if (direction > 0) {
        if (this.currentMonth === 12) {
          this.currentMonth = 1;
          this.currentYear++;
        } else {
          this.currentMonth++;
        }
      } else {
        if (this.currentMonth === 1) {
          this.currentMonth = 12;
          this.currentYear--;
        } else {
          this.currentMonth--;
        }
      }
    },
    
    // 选择日期
    selectDate(date) {
      this.selectedDate = date.dateStr;
    },
    
    // 添加日程
    addSchedule() {
      uni.navigateTo({
        url: `/pages/schedule/add?date=${this.selectedDate}`
      });
    },
    
    // 编辑日程
    editSchedule(schedule) {
      uni.navigateTo({
        url: `/pages/schedule/add?id=${schedule.id}`
      });
    },
    
    // 切换日程完成状态
    async toggleSchedule(schedule) {
      try {
        // 更新本地状态
        const updatedSchedule = { ...schedule, completed: !schedule.completed };
        const index = this.schedules.findIndex(s => s.id === schedule.id);
        if (index !== -1) {
          this.schedules.splice(index, 1, updatedSchedule);
        }
        
        // 同步到后端
        await this.makeRequest('PUT', `${API_CONFIG.ENDPOINTS.UPDATE_SCHEDULE}/${schedule.id}`, {
          completed: !schedule.completed
        });
        
      } catch (error) {
        console.error('更新日程状态失败:', error);
        // 失败时恢复本地状态
        const index = this.schedules.findIndex(s => s.id === schedule.id);
        if (index !== -1) {
          this.schedules.splice(index, 1, schedule);
        }
      }
    },
    
    // 判断日程是否过期
    isScheduleOverdue(schedule) {
      if (schedule.completed) return false;
      
      const now = new Date();
      const scheduleDate = new Date(`${schedule.date} ${schedule.time}`);
      return scheduleDate < now;
    },
    
    // 获取日程状态文本
    getScheduleStatus(schedule) {
      if (schedule.completed) return '已完成';
      if (this.isScheduleOverdue(schedule)) return '已过期';
      return '待完成';
    },
    
    // 显示日程菜单
    showScheduleMenu(schedule) {
      uni.showActionSheet({
        itemList: ['编辑', '删除'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 编辑日程
            this.editSchedule(schedule);
          } else if (res.tapIndex === 1) {
            // 删除日程
            this.deleteSchedule(schedule.id);
          }
        }
      });
    },
    
    // 删除日程
    async deleteSchedule(scheduleId) {
      uni.showModal({
        title: '确认删除',
        content: '确定要删除这个日程吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              // 先从本地移除
              const originalSchedules = [...this.schedules];
              this.schedules = this.schedules.filter(s => s.id !== scheduleId);
              
              // 同步到后端
              await this.makeRequest('DELETE', `${API_CONFIG.ENDPOINTS.DELETE_SCHEDULE}/${scheduleId}`);
              
              uni.showToast({
                title: '删除成功',
                icon: 'success'
              });
            } catch (error) {
              console.error('删除日程失败:', error);
              // 失败时恢复数据
              this.schedules = originalSchedules;
              uni.showToast({
                title: '删除失败',
                icon: 'none'
              });
            }
          }
        }
      });
    }
  }
};
</script>

<style scoped>
/* 基础容器样式 */
.page-container {
  position: relative;
  height: 100vh;
  overflow: hidden;
}

.page {
  padding: 20rpx;
  font-family: "Arial", "PingFang SC", sans-serif;
  height: 100vh;
  background-repeat: no-repeat;
  box-sizing: border-box;
  background-attachment: fixed;
  background-position: center;
  background-size: cover;
  overflow: hidden;
  position: relative;
}

/* 头部样式 */
.header {
  margin: 15rpx 0 20rpx;
  position: relative;
  z-index: 2;
}

.title {
  font-size: 32rpx;
  font-weight: bold;
  color: #007AFF;
  letter-spacing: 2rpx;
}

/* 月份切换器 */
.month-switcher {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20rpx;
  padding: 15rpx 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 2;
}

.month-btn {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 122, 255, 0.1);
  border-radius: 50%;
}

.month-btn:active {
  background: rgba(0, 122, 255, 0.2);
}

.arrow-icon {
  width: 24rpx;
  height: 24rpx;
}

.month-display {
  flex: 1;
  text-align: center;
}

.current-month {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

/* 日历容器 */
.calendar-container {
  margin-bottom: 20rpx;
  position: relative;
  z-index: 2;
}

.calendar-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

/* 星期标题 */
.weekdays {
  display: flex;
  justify-content: space-around;
  margin-bottom: 15rpx;
  border-bottom: 1rpx solid #f0f0f0;
  padding-bottom: 10rpx;
}

.weekday-item {
  width: 14.28%;
  text-align: center;
  font-size: 22rpx;
  color: #666;
  font-weight: 500;
}

/* 日历网格 */
.calendar-grid {
  display: flex;
  flex-wrap: wrap;
}

.calendar-date {
  width: 14.28%;
  height: 80rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  margin-bottom: 8rpx;
}

.date-number {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
}

/* 日期状态样式 */
.calendar-date.other-month .date-number {
  color: #ccc;
}

.calendar-date.today {
  background: #9bccff;
  border-radius: 12rpx;
}

.calendar-date.today .date-number {
  color: #fff;
  font-weight: bold;
}

.calendar-date.selected {
  background: rgba(0, 122, 255, 0.1);
  border-radius: 12rpx;
  border: 2rpx solid #007AFF;
  box-sizing: border-box;
}

.calendar-date.has-schedule .date-number {
  color: #007AFF;
  font-weight: bold;
}

/* 日程标记点 */
.schedule-dot {
  width: 8rpx;
  height: 8rpx;
  background: #007AFF;
  border-radius: 50%;
  position: absolute;
  bottom: 8rpx;
}

.schedule-dot.active-dot {
  background: #fff;
}

/* 当日行程模块 - 自适应占据剩余空间 */
.today-schedule {
  position: absolute;
  left: 20rpx;
  right: 20rpx;
  bottom: 120rpx; /* 固定下界，为导航栏预留空间 */
  top: 950rpx; /* 调整上界：确保在日历模块下方 */
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20rpx;
  padding: 20rpx;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
  z-index: 1;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
  padding-bottom: 15rpx;
  border-bottom: 1rpx solid #f0f0f0;
  flex-shrink: 0;
}

.schedule-date {
  font-size: 26rpx;
  font-weight: bold;
  color: #333;
}

.add-btn {
  display: flex;
  align-items: center;
  background: #007AFF;
  border-radius: 15rpx;
  padding: 8rpx 15rpx;
}

.add-btn:active {
  background: #0051D5;
}

.add-icon {
  width: 20rpx;
  height: 20rpx;
  margin-right: 5rpx;
}

.add-text {
  font-size: 22rpx;
  color: #fff;
  font-weight: 500;
}

/* 行程列表滚动容器 */
.schedule-scroll {
  flex: 1;
  overflow-y: auto;
  /* 确保滚动区域有明确的高度限制 */
  height: 0;
  /* 优化滚动性能 */
  -webkit-overflow-scrolling: touch;
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

/* 空行程提示 */
.empty-schedule {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200rpx;
}

.empty-icon {
  width: 80rpx;
  height: 80rpx;
  opacity: 0.3;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 24rpx;
  color: #999;
}

/* 行程项目 */
.schedule-item {
  background: #fff;
  border-radius: 15rpx;
  padding: 15rpx;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  box-shadow: 0 1rpx 3rpx rgba(0, 0, 0, 0.05);
  border-left: 6rpx solid #007AFF;
}

.schedule-item.completed {
  opacity: 0.7;
  border-left-color: #00B42A;
}

.schedule-item:active {
  background: #f8f9fa;
}

.schedule-left {
  flex: 1;
  display: flex;
  gap: 15rpx;
}

.time-tag {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
  padding: 6rpx 12rpx;
  border-radius: 8rpx;
  font-size: 20rpx;
  font-weight: 500;
  white-space: nowrap;
  min-width: 80rpx;
  text-align: center;
}

.time-tag.high {
  background: rgba(255, 61, 48, 0.1);
  color: #FF3D30;
}

.time-tag.medium {
  background: rgba(255, 125, 0, 0.1);
  color: #FF7D00;
}

.time-tag.low {
  background: rgba(0, 180, 42, 0.1);
  color: #00B42A;
}

.schedule-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.schedule-title {
  font-size: 24rpx;
  font-weight: bold;
  color: #333;
}

.schedule-desc {
  font-size: 20rpx;
  color: #666;
  line-height: 1.4;
}

.schedule-location {
  font-size: 18rpx;
  color: #999;
}

.schedule-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
}

.status-indicator {
  font-size: 18rpx;
  padding: 4rpx 8rpx;
  border-radius: 6rpx;
  font-weight: 500;
}

.status-indicator.completed {
  background: rgba(0, 180, 42, 0.1);
  color: #00B42A;
}

.status-indicator.pending {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.status-indicator.overdue {
  background: rgba(255, 61, 48, 0.1);
  color: #FF3D30;
}

.more-btn {
  font-size: 28rpx;
  color: #999;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
}

.more-btn:active {
  background: rgba(0, 0, 0, 0.05);
}

/* 底部留白 */
.bottom-space {
  height: 30rpx;
}

/* 安全区域适配 */
.safe-area-bottom {
  height: env(safe-area-inset-bottom);
  background: rgba(255, 255, 255, 0.9);
}
</style>