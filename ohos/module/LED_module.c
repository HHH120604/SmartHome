#include <stdio.h>
#include <unistd.h>

#include "ohos_init.h"
#include "cmsis_os2.h"
#include "wifiiot_gpio.h"
#include "wifiiot_gpio_ex.h"
#include "wifiiot_adc.h"
#include "wifiiot_pwm.h"
#include "wifiiot_errno.h"

#include "main.h"
#include "LED_module.h"

void init_led(void)
{
    GpioInit();
    // 蜂鸣器
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_9, WIFI_IOT_IO_FUNC_GPIO_9_PWM0_OUT);
    PwmInit(WIFI_IOT_PWM_PORT_PWM0);

    // LED: RED GREEN YELLOW
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_10, WIFI_IOT_IO_FUNC_GPIO_10_PWM1_OUT);
    PwmInit(WIFI_IOT_PWM_PORT_PWM1);
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_11, WIFI_IOT_IO_FUNC_GPIO_11_PWM2_OUT);
    PwmInit(WIFI_IOT_PWM_PORT_PWM2);
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_IO_FUNC_GPIO_12_PWM3_OUT);
    PwmInit(WIFI_IOT_PWM_PORT_PWM3);

    // 可控制设备从断连状态解除
    for (int i = LED_RED; i < LED_RED+4; i++) device_status[i] = DEVICE_CLOSE;
}

void start_led(void)
{
    init_led();

    while (!toStop)
    {
        // LED
        for (int i = LED_RED; i < LED_RED+3; i++)
        {
            if (device_status[i] == DEVICE_ON1) PwmStart(i+1, led_freq / (100/led_duty), led_freq);
            else PwmStop(i+1);
        }
        // 蜂鸣器
        if (device_status[LED_BEEP] == DEVICE_ON1) PwmStart(WIFI_IOT_PWM_PORT_PWM0, beep_freq / (100/beep_duty), beep_freq);
        else PwmStop(WIFI_IOT_PWM_PORT_PWM0);

        osDelay(delay / 10);
    }
}

void stop_led(void)
{
    for (int i = LED_RED; i < LED_RED+4; i++)
    {
        PwmStop(i-LED_RED+1);
        // 可控制设备断连
        device_status[i-LED_RED+1] = DEVICE_DISCONNECT;
    }
}

osThreadId_t led_task(void)
{
    osThreadAttr_t attr;

    attr.name = "led_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityNormal;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_led, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[led_task] Falied to create led_task!\n");
    }
    return module_id;
}