#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"
#include "wifi_device.h"

#include "main.h"
#include "FIRE_module.h"
#include "GAS_module.h"
#include "LCD_module.h"
#include "LED_module.h"
#include "MQTT_module.h"
#include "PIR_module.h"
#include "TAH_module.h"

int toStop = 0;
uint32_t delay = 1000; // tick 上报延迟时间, 其余延迟均在此基础上改变
// module status for: FIRE GAS LCD LED MQTT PIR TAH
// WIFI模块自动启动
osThreadId_t module_status[MODULE_NUM] = {NULL};
int device_status[DEVICE_NUM] = {0};
int publish_state = 0;
unsigned int beep_freq = 160*1000*1000 / 2700; // 蜂鸣器声音频率, 2700HZ
unsigned int beep_duty = 10; // PWM占空比
unsigned int led_freq = 160*1000*1000 / 2700; // LED照明频率
unsigned int led_duty = 50; // PWM占空比

static void entry(void *arg)
{
    // init
    (void)arg;
    usleep(500 * 1000);
    printf("Smart Home Running\n");
    for (int i = 0; i < DEVICE_NUM; i++) device_status[i] = DEVICE_DISCONNECT; // 所有可控制设备初始为断连状态, 注意和模块区分

    // start
    module_status[MQTT_MODULE] = mqtt_task(); // mqtt进程
    module_status[LCD_MODULE] = lcd_task(); // lcd进程
    
    // end
}

void sh_task(void)
{
    osThreadAttr_t attr;

    attr.name = "smart_home";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityNormal;

    if (osThreadNew((osThreadFunc_t)entry, NULL, &attr) == NULL)
    {
        printf("[smart_home] Falied to create sh_task!\n");
    }
}

APP_FEATURE_INIT(sh_task);