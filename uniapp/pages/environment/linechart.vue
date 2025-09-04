<template>
  <view class="page-container">
    <!-- 带背景的页面，与主页风格统一 -->
    <view class="page" :style="{ backgroundImage: 'url(/static/img/home_bg.png)', backgroundSize: 'cover' }">
      <!-- 时间范围选择 -->
      <view class="time-range">
        <view class="time-item" 
          v-for="item in timeRanges" 
          :key="item.value"
          :class="{ 'active': selectedTimeRange === item.value }"
          @click="selectTimeRange(item.value)" :disabled="isLoading">
          {{ item.label }}
        </view>
      </view>
      
      <!-- 加载状态指示器 -->
      <view class="loading-indicator" v-if="isLoading">
        <view class="loading-spinner"></view>
        <text class="loading-text">加载中...</text>
      </view>
      
      <!-- 错误信息提示 -->
      <view class="error-message" v-if="errorMessage && !isLoading">
        <image src="/static/icon/clear.png" class="error-icon" />
        <text>{{ errorMessage }}</text>
        <button class="retry-btn" @click="fetchEnvironmentHistory">重试</button>
      </view>
      
      <!-- 图表容器 -->
      <view class="chart-container" v-if="!isLoading">
        <view class="chart-wrapper">
          <canvas canvas-id="lineCanvas" class="line-chart"></canvas>
        </view>
        
        <!-- 数据统计摘要 -->
        <view class="stats-summary">
          <view class="stat-item">
            <text class="stat-label">平均值</text>
            <text class="stat-value">{{ Math.round(stats.average) }}{{ unit }}</text>
          </view>
          <view class="stat-item">
            <text class="stat-label">最大值</text>
            <text class="stat-value">{{ Math.round(stats.max) }}{{ unit }}</text>
          </view>
          <view class="stat-item">
            <text class="stat-label">最小值</text>
            <text class="stat-value">{{ Math.round(stats.min) }}{{ unit }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import API_CONFIG from '../../utils/api-config.js';

export default {
  data() {
    return {
      chartType: 'temperature', // 默认显示温度统计
      selectedTimeRange: 'day', // 默认显示24小时数据
      timeRanges: [
        { label: '3小时', value: '3hours' },
        { label: '24小时', value: 'day' },
        { label: '15天', value: '15days' }
      ],
      chartData: [],
      stats: {
        average: 0,
        max: 0,
        min: 0
      },
      chart: null,
      isLoading: false, // 加载状态标记
      errorMessage: '' // 错误信息
    };
  },
  
  computed: {
    // 图表标题
    chartTitle() {
      return this.chartType === 'temperature' ? '温度' : '湿度';
    },
    
    // 数据单位
    unit() {
      return this.chartType === 'temperature' ? '°C' : '%';
    },
    
    // 从Vuex获取当前环境数据
    currentEnvData() {
      return this.$store.getters.getFullEnvironment;
    }
  },
  
  onLoad(options) {
    // 接收从monitor页面传递的参数
    if (options && options.type) {
      this.chartType = options.type;
    }
    
    // 初始化图表数据 - 向后端请求
    this.fetchEnvironmentHistory();
  },
  
  onShow() {
    // 每次页面显示时，重新生成数据，确保与index页面数据保持同步
    this.fetchEnvironmentHistory();
    this.drawChart();
  },
  
  onReady() {
    // 页面渲染完成后绘制图表
    this.drawChart();
  },
  
  watch: {
    // 监听环境数据变化，实时更新图表
    currentEnvData: {
      handler() {
        // 环境数据变化时，如果当前没有在加载中，则更新图表
        if (!this.isLoading) {
          this.drawChart();
        }
      },
      deep: true // 深度监听对象内部变化
    },
    
    // 监听图表类型变化
    chartType() {
      this.fetchEnvironmentHistory();
    }
  },
  
  methods: {
    // 返回上一页
      navigateBack() {
        uni.navigateBack();
      },
    
      // 选择时间范围
    selectTimeRange(range) {
      this.selectedTimeRange = range;
      this.fetchEnvironmentHistory();
    },
    // 向后端请求环境历史数据
    fetchEnvironmentHistory() {
      this.isLoading = true;
      this.errorMessage = '';
      
      // 发送请求
      uni.request({
        url: `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GET_ENVIRONMENT_HISTORY}${this.chartType}/${this.selectedTimeRange}`,
        method: 'GET',
        timeout: API_CONFIG.TIMEOUT,
        success: (res) => {
          if (res.statusCode === 200 && res.data) {
            // console.log(res.data);
            // 处理返回的数据 - 包含3个时间跨度的列表
            this.processSingleRangeData(res.data);
          } else {
            // 处理错误响应
            this.errorMessage = res.data ? res.data.message : '获取数据失败';
            console.error('获取环境历史数据失败:', res);
            // 在API失败时，使用当前值创建简单的回退数据
            this.generateFallbackData();
          }
        },
        fail: (err) => {
          this.errorMessage = '网络请求失败，请检查网络连接';
          console.error('请求环境历史数据网络失败:', err);
          // 在网络失败时，使用当前值创建简单的回退数据
          this.generateFallbackData();
        },
        complete: () => {
          this.isLoading = false;
          setTimeout(() => {
            this.drawChart();
          }, 100);
        }
      });
    },
    
    // 处理单一时间跨度的数据列表
    processSingleRangeData(dataList) {
      if (!dataList || !Array.isArray(dataList)) {
        this.generateFallbackData();
        return;
      }
      
      const data = [];
      const now = new Date();
      let timeFormat = 'HH:mm'; // 默认时间格式
      
      // 根据不同的时间范围设置不同的时间格式和时间间隔
      if (this.selectedTimeRange === '3hours') {
        timeFormat = 'HH:mm';
        
        // 3小时时间跨度的数据处理 - 固定10分钟间隔
        const FIXED_INTERVAL_MINUTES = 10; // 固定10分钟间隔
        const TOTAL_MINUTES = 3 * 60; // 3小时总分钟数
        const EXPECTED_POINTS = TOTAL_MINUTES / FIXED_INTERVAL_MINUTES; // 期望的数据点数量
        
        // 从最早的时间点（当前时间 - 3小时）开始处理
        for (let i = 0; i < EXPECTED_POINTS; i++) {
          // 计算当前点的时间
          const timePoint = new Date(now);
          // 从当前时间向前推算，i越大，离现在越近
          timePoint.setMinutes(now.getMinutes() - (EXPECTED_POINTS - 1 - i) * FIXED_INTERVAL_MINUTES);
          
          // 获取或计算当前点的值
          let value = 0;
          
          // 如果有后端数据，优先使用后端数据
          if (dataList && dataList.length > 0) {
            // 计算应该使用的后端数据索引
            // 线性映射：将期望的点位置映射到实际数据数组的位置
            const dataIndex = Math.floor((i / (EXPECTED_POINTS - 1)) * (dataList.length - 1));
            const item = dataList[dataIndex];
            value = typeof item === 'number' ? item : (item.value !== undefined ? item.value : 0);
          }
          
          data.push({
            time: this.formatTime(timePoint, timeFormat),
            value: Math.round(value) // 确保值为整数
          });
        }
      } else if (this.selectedTimeRange === 'day') {
        timeFormat = 'HH:mm';
        
        // 24小时时间跨度的数据处理
        const totalPoints = dataList.length;
        const timeIntervalHours = 24 / totalPoints; // 平均分配24小时的时间跨度
        
        dataList.forEach((item, index) => {
          if (item !== undefined) {
            const timePoint = new Date(now);
            timePoint.setHours(now.getHours() - (totalPoints - 1 - index) * timeIntervalHours);
            
            const value = typeof item === 'number' ? item : (item.value !== undefined ? item.value : 0);
            
            data.push({
              time: this.formatTime(timePoint, timeFormat),
              value: Math.round(value)
            });
          }
        });
      } else if (this.selectedTimeRange === '15days') {
        timeFormat = 'MM-DD';
        
        // 15天时间跨度的数据处理
        const totalPoints = dataList.length;
        const timeIntervalDays = 15 / totalPoints; // 平均分配15天的时间跨度
        
        dataList.forEach((item, index) => {
          if (item !== undefined) {
            const timePoint = new Date(now);
            timePoint.setDate(now.getDate() - (totalPoints - 1 - index) * timeIntervalDays);
            timePoint.setHours(12, 0, 0, 0); // 统一设置为中午12点
            
            const value = typeof item === 'number' ? item : (item.value !== undefined ? item.value : 0);
            
            data.push({
              time: this.formatTime(timePoint, timeFormat),
              value: Math.round(value)
            });
          }
        });
      }
      
      this.chartData = data;
      this.calculateStats();
    },
    
    // 生成回退数据（当API请求失败时使用）
    generateFallbackData() {
      const data = [];
      const now = new Date();
      const currentValue = this.chartType === 'temperature' ? this.currentEnvData.temp : this.currentEnvData.humidity;
      let dataPoints = 12;
      let timeFormat = 'HH:mm';
      
      if (this.selectedTimeRange === '3hours') {
        dataPoints = 18; // 3小时，每10分钟一个点，共18个点
      } else if (this.selectedTimeRange === 'day') {
        dataPoints = 24;
      } else if (this.selectedTimeRange === '15days') {
        dataPoints = 15;
        timeFormat = 'MM-DD';
      }
      
      // 生成基于当前值的简单回退数据
      for (let i = dataPoints - 1; i >= 0; i--) {
        const time = new Date(now);
        
        if (this.selectedTimeRange === '3hours') {
          time.setMinutes(now.getMinutes() - i * 10);
        } else if (this.selectedTimeRange === 'day') {
          time.setHours(now.getHours() - i);
        } else if (this.selectedTimeRange === '15days') {
          time.setDate(now.getDate() - i);
          time.setHours(12, 0, 0, 0);
        }
        
        // 生成一个接近当前值的数值，波动较小
        const variation = this.chartType === 'temperature' ? (Math.random() - 0.5) * 2 : (Math.random() - 0.5) * 8;
        const newValue = Math.max(0, Math.min(
          this.chartType === 'temperature' ? 40 : 100,
          currentValue + variation
        ));
        
        data.push({
          time: this.formatTime(time, timeFormat),
          value: Math.round(newValue)
        });
      }
      
      this.chartData = data;
      this.calculateStats();
    },
    
    // 格式化时间
    formatTime(date, format) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      
      if (format === 'HH:mm') {
        return `${hours}:${minutes}`;
      } else if (format === 'MM-DD') {
        return `${month}-${day}`;
      }
      
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    },
    
    // 计算统计数据
    calculateStats() {
      if (this.chartData.length === 0) {
        this.stats = { average: 0, max: 0, min: 0 };
        return;
      }
      
      const values = this.chartData.map(item => item.value);
      const sum = values.reduce((acc, val) => acc + val, 0);
      
      this.stats = {
        average: sum / values.length,
        max: Math.max(...values),
        min: Math.min(...values)
      };
    },
    
    // 绘制折线图
    drawChart() {
      try {
        // 使用uni.createCanvasContext代替wx.createCanvasContext，确保更好的跨平台兼容性
        const ctx = uni.createCanvasContext('lineCanvas');
        const chartWidth = wx.getSystemInfoSync().windowWidth - 60;
        const chartHeight = 300;
        
        // 清空画布
        ctx.clearRect(0, 0, chartWidth, chartHeight);
      
      if (this.chartData.length === 0) {
          // 确保即使没有数据也执行draw()
          ctx.draw();
          return;
        }
      
      // 15日数据需要按照时间从旧到新排列
      let displayData = this.chartData;
      if (this.selectedTimeRange === '15days') {
        // 复制原始数据并按时间排序
        displayData = [...this.chartData].sort((a, b) => {
          // 解析日期字符串并比较
          const dateA = new Date(a.time);
          const dateB = new Date(b.time);
          return dateA - dateB;
        });
      }
      
      // 计算数据范围
      const values = displayData.map(item => item.value);
      let minValue = Math.min(...values);
      let maxValue = Math.max(...values);
      let valueRange = maxValue - minValue || 1; // 防止除以0

      // 当所有值相同时（直线情况），添加一定的余量使直线居中
      // if (valueRange === 0) {
      const margin = this.chartType === 'temperature' ? 2 : 5; // 温度数据增加5度余量，湿度数据增加10%余量
      minValue -= margin;
      maxValue += margin - 1;
      valueRange = maxValue - minValue;
      // }
      
      // 图表边距
      const padding = 40;
      const plotWidth = chartWidth - 2 * padding;
      const plotHeight = chartHeight - 2 * padding;
      
      // 绘制坐标轴
      ctx.setStrokeStyle('#e0e0e0');
      ctx.setLineWidth(1);
      
      // X轴
      ctx.beginPath();
      ctx.moveTo(padding, chartHeight - padding);
      ctx.lineTo(chartWidth - padding, chartHeight - padding);
      ctx.stroke();
      
      // Y轴
      ctx.beginPath();
      ctx.moveTo(padding, padding);
      ctx.lineTo(padding, chartHeight - padding);
      ctx.stroke();
      
      // 绘制网格线
      ctx.setStrokeStyle('#f0f0f0');
      ctx.setLineWidth(1);
      
      // 水平网格线
      for (let i = 0; i <= 4; i++) {
        const y = padding + (plotHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(chartWidth - padding, y);
        ctx.stroke();
        
        // Y轴刻度标签
        const value = maxValue - (valueRange / 4) * i;
        ctx.setFillStyle('#999');
        ctx.setFontSize(12);
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(value), padding - 10, y + 5);
      }
      
      // X轴刻度标签
      const labelStep = Math.max(1, Math.floor(displayData.length / 6));
      ctx.setFillStyle('#999');
      ctx.setFontSize(12);
      ctx.textAlign = 'center';
      
      for (let i = 0; i < displayData.length; i += labelStep) {
        const x = padding + (plotWidth / (displayData.length - 1)) * i;
        const y = chartHeight - padding + 20;
        ctx.fillText(displayData[i].time, x, y);
      }
      
      // 绘制折线
      const lineColor = this.chartType === 'temperature' ? '#007AFF' : '#00B42A';
      ctx.setStrokeStyle(lineColor);
      ctx.setLineWidth(3);
      ctx.setLineCap('round');
      ctx.setLineJoin('round');
      
      ctx.beginPath();
      displayData.forEach((item, index) => {
        const x = padding + (plotWidth / (displayData.length - 1)) * index;
        const y = padding + plotHeight - ((item.value - minValue) / valueRange) * plotHeight;
        
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();
      
      // 绘制数据点
      ctx.setFillStyle(lineColor);
      displayData.forEach((item, index) => {
        const x = padding + (plotWidth / (displayData.length - 1)) * index;
        const y = padding + plotHeight - ((item.value - minValue) / valueRange) * plotHeight;
        
        // 绘制外圈
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.setFillStyle('#fff');
        ctx.fill();
        ctx.setStrokeStyle(lineColor);
        ctx.setLineWidth(2);
        ctx.stroke();
      });
      
      // 绘制填充区域
      ctx.beginPath();
      ctx.moveTo(padding, chartHeight - padding);
      displayData.forEach((item, index) => {
        const x = padding + (plotWidth / (displayData.length - 1)) * index;
        const y = padding + plotHeight - ((item.value - minValue) / valueRange) * plotHeight;
        
        if (index === 0) {
          ctx.lineTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.lineTo(chartWidth - padding, chartHeight - padding);
      ctx.closePath();
      
      // 创建渐变填充
      const gradient = ctx.createLinearGradient(padding, padding, padding, chartHeight - padding);
      const gradientStartColor = this.chartType === 'temperature' ? 'rgba(0, 122, 255, 0.2)' : 'rgba(0, 180, 42, 0.2)';
      const gradientEndColor = this.chartType === 'temperature' ? 'rgba(0, 122, 255, 0.05)' : 'rgba(0, 180, 42, 0.05)';
      gradient.addColorStop(0, gradientStartColor);
      gradient.addColorStop(1, gradientEndColor);
      
      ctx.setFillStyle(gradient);
      ctx.fill();
      
      // 绘制图表
        ctx.draw();
      } catch (error) {
        console.error('绘制图表出错:', error);
      }
    }
  }
};
</script>

<style scoped>
/* 基础容器样式，与主页保持一致 */
.page-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.page {
  padding: 20rpx;
  font-family: "Arial", "PingFang SC", sans-serif;
  min-height: 100vh;
  background-repeat: no-repeat;
  box-sizing: border-box;
}

/* 头部样式，与主页风格统一 */
.header {
  display: flex;
  align-items: center;
  margin: 30rpx 0;
}

.back {
  font-size: 36rpx;
  color: #333;
  margin-right: 20rpx;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back:active {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 50%;
}

.title {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  flex: 1;
  text-align: center;
}

/* 加载状态指示器 */
.loading-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx 0;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20rpx;
  margin: 20rpx 0;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 6rpx solid #f3f3f3;
  border-top: 6rpx solid #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-top: 20rpx;
  font-size: 28rpx;
  color: #666;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误信息样式 */
.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20rpx;
  margin: 20rpx 0;
  text-align: center;
}

.error-icon {
  width: 80rpx;
  height: 80rpx;
  margin-bottom: 20rpx;
  opacity: 0.5;
}

.error-message text {
  font-size: 28rpx;
  color: #ff4d4f;
  margin-bottom: 20rpx;
  line-height: 1.5;
}

.retry-btn {
  padding: 10rpx 40rpx;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 20rpx;
  font-size: 28rpx;
}

.retry-btn:active {
  background: #0056b3;
}

/* 禁用状态的时间选择项 */
.time-item[disabled] {
  opacity: 0.5;
  pointer-events: none;
}

/* 时间范围选择器 */
.time-range {
  display: flex;
  justify-content: center;
  margin: 20rpx 0;
  padding: 0 20rpx;
}

.time-item {
  padding: 10rpx 30rpx;
  margin: 0 10rpx;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 20rpx;
  font-size: 24rpx;
  color: #666;
  box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.05);
}

.time-item.active {
  background: #007AFF;
  color: #fff;
}

/* 图表容器 */
.chart-container {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20rpx;
  padding: 30rpx 20rpx;
  margin: 20rpx 0;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

/* 图表包装器 */
.chart-wrapper {
  width: 100%;
  height: 300px;
  margin-bottom: 30rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 折线图 */
.line-chart {
  width: 100%;
  height: 100%;
}

/* 统计摘要 */
.stats-summary {
  display: flex;
  justify-content: space-around;
  padding: 10rpx 0;
}

.stat-item {
  text-align: center;
  flex: 1;
}

.stat-label {
  font-size: 20rpx;
  color: #999;
  display: block;
  margin-bottom: 8rpx;
}

.stat-value {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}
</style>