// utils/scheduleReminder.js - 日程提醒工具

class ScheduleReminder {
  constructor() {
    this.timers = new Map(); // 存储定时器
  }

  // 设置日程提醒
  setReminder(schedule) {
    if (!schedule.reminder || schedule.reminder === 'none' || schedule.completed) {
      return;
    }

    const reminderTime = this.calculateReminderTime(schedule);
    if (!reminderTime || reminderTime <= new Date()) {
      return; // 提醒时间已过
    }

    const delay = reminderTime.getTime() - new Date().getTime();
    
    // 清除已存在的定时器
    this.clearReminder(schedule.id);
    
    // 设置新的定时器
    const timer = setTimeout(() => {
      this.showReminder(schedule);
      this.timers.delete(schedule.id);
    }, delay);
    
    this.timers.set(schedule.id, timer);
    
    console.log(`设置提醒: ${schedule.title} 在 ${reminderTime.toLocaleString()} 提醒`);
  }

  // 计算提醒时间
  calculateReminderTime(schedule) {
    const scheduleDateTime = new Date(`${schedule.date} ${schedule.time}`);
    const reminderMinutes = parseInt(schedule.reminder);
    
    if (isNaN(reminderMinutes)) {
      return null;
    }
    
    return new Date(scheduleDateTime.getTime() - reminderMinutes * 60 * 1000);
  }

  // 显示提醒通知
  showReminder(schedule) {
    const reminderText = this.getReminderText(schedule.reminder);
    
    // 使用 uni.showModal 显示提醒
    uni.showModal({
      title: '日程提醒',
      content: `${schedule.title}\n${reminderText}开始\n地点：${schedule.location || '无'}`,
      confirmText: '知道了',
      showCancel: false,
      success: () => {
        // 可以添加振动提醒
        if (uni.vibrateShort) {
          uni.vibrateShort();
        }
      }
    });

    // 也可以使用本地通知 (需要权限)
    if (uni.createNotification) {
      uni.createNotification({
        title: '日程提醒',
        content: `${schedule.title} ${reminderText}开始`,
        payload: {
          scheduleId: schedule.id
        }
      });
    }
  }

  // 获取提醒文本
  getReminderText(reminderValue) {
    const reminderMap = {
      '0': '即将',
      '5': '5分钟后',
      '15': '15分钟后',
      '30': '30分钟后',
      '60': '1小时后'
    };
    return reminderMap[reminderValue] || '';
  }

  // 清除指定日程的提醒
  clearReminder(scheduleId) {
    const timer = this.timers.get(scheduleId);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(scheduleId);
    }
  }

  // 清除所有提醒
  clearAllReminders() {
    this.timers.forEach(timer => clearTimeout(timer));
    this.timers.clear();
  }

  // 批量设置提醒
  setMultipleReminders(schedules) {
    schedules.forEach(schedule => {
      this.setReminder(schedule);
    });
  }

  // 更新日程提醒
  updateReminder(schedule) {
    this.clearReminder(schedule.id);
    this.setReminder(schedule);
  }

  // 获取即将到来的提醒列表
  getUpcomingReminders(hours = 24) {
    const now = new Date();
    const futureTime = new Date(now.getTime() + hours * 60 * 60 * 1000);
    
    return Array.from(this.timers.keys()).map(scheduleId => {
      // 这里需要从store或其他地方获取完整的schedule数据
      return {
        scheduleId,
        hasReminder: true
      };
    });
  }
}

// 创建全局实例
const scheduleReminder = new ScheduleReminder();

export default scheduleReminder;