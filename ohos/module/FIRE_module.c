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
#include "FIRE_module.h"

int fire_fire = 0; // FIRE红外火焰传感器
int fire_beep = 0; // FIRE蜂鸣器
int fire_amp = 0; // FIRE运放放大输出

void init_fire(void)
{
    GpioInit();
    // 蜂鸣器
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_9, WIFI_IOT_IO_FUNC_GPIO_9_PWM0_OUT);
    PwmInit(WIFI_IOT_PWM_PORT_PWM0);
    // 红外火焰传感器
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_10, WIFI_IOT_IO_FUNC_GPIO_10_GPIO);
    GpioSetDir(WIFI_IOT_IO_NAME_GPIO_10, WIFI_IOT_GPIO_DIR_IN);

    fire_fire = 0;
    fire_beep = 0;
    fire_amp = 0;
}

void start_fire(void)
{
    init_fire();

    while (!toStop)
    {
        WifiIotGpioValue rel = 0;
        unsigned short data = 0;

        // 红外火焰传感器
        GpioGetInputVal(WIFI_IOT_IO_NAME_GPIO_10, &rel);
        fire_fire = rel ? 0 : 1; // 低电平有效

        // 读取运放放大输出
        if (AdcRead(WIFI_IOT_ADC_CHANNEL_4, &data, WIFI_IOT_ADC_EQU_MODEL_4, WIFI_IOT_ADC_CUR_BAIS_DEFAULT, 0) != WIFI_IOT_SUCCESS)
        {
            printf("FIRE ADC_4 read failed!\n");
        }
        else
        {
            fire_amp = data;
        }
        // 蜂鸣器
        if (fire_fire)
        {
            PwmStart(WIFI_IOT_PWM_PORT_PWM0, beep_freq / (100/beep_duty), beep_freq);
            fire_beep = 1;
            publish_state = 1;
        }
        else
        {
            PwmStop(WIFI_IOT_PWM_PORT_PWM0);
            fire_beep = 0;
        }
        osDelay(delay / 10);
    }
}

void stop_fire(void)
{
    PwmStop(WIFI_IOT_PWM_PORT_PWM0);
    fire_fire = 0;
    fire_beep = 0;
    fire_amp = 0;
}

osThreadId_t fire_task(void)
{
    osThreadAttr_t attr;

    attr.name = "fire_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityNormal;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_fire, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[fire_task] Falied to create fire_task!\n");
    }
    return module_id;
}