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
#include "PIR_module.h"

int pir_pir = 0; // PIR人体红外传感器
int pir_lux = 0; // PIR光敏电阻

void init_pir(void)
{
    GpioInit();
    // 三色灯
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_10, WIFI_IOT_IO_FUNC_GPIO_10_PWM1_OUT); // GREEN
    PwmInit(WIFI_IOT_PWM_PORT_PWM1);
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_11, WIFI_IOT_IO_FUNC_GPIO_11_PWM2_OUT); // RED
    PwmInit(WIFI_IOT_PWM_PORT_PWM2);
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_IO_FUNC_GPIO_12_PWM3_OUT); // BLUE
    PwmInit(WIFI_IOT_PWM_PORT_PWM3);

    pir_pir = 0;
    pir_lux = 0;
    // 可控制设备从断连状态解除
    for (int i = PIR_GREEN; i < PIR_GREEN+3; i++) device_status[i] = DEVICE_CLOSE;
}

void start_pir(void)
{
    init_pir();

    while (!toStop)
    {
        unsigned short data = 0;

        // 读取人体红外传感器输出
        if (AdcRead(WIFI_IOT_ADC_CHANNEL_3, &data, WIFI_IOT_ADC_EQU_MODEL_4, WIFI_IOT_ADC_CUR_BAIS_DEFAULT, 0) != WIFI_IOT_SUCCESS)
            printf("[ERROR] PIR ADC_3: pir_pir read failed\n");
        else pir_pir = data;

        if (AdcRead(WIFI_IOT_ADC_CHANNEL_4, &data, WIFI_IOT_ADC_EQU_MODEL_4, WIFI_IOT_ADC_CUR_BAIS_DEFAULT, 0) != WIFI_IOT_SUCCESS)
            printf("[ERROR] PIR ADC_4: pir_lux read failed\n");
        else pir_lux = data;
        // 三色灯
        for (int i = PIR_GREEN; i < PIR_GREEN+3; i++)
        {
            if (device_status[i] == DEVICE_ON1) PwmStart(i-PIR_GREEN+1, led_freq / (100/led_duty), led_freq);
            else PwmStop(i+1);
        }
        osDelay(delay / 10);
    }
}

void stop_pir(void)
{
    pir_pir = 0;
    pir_lux = 0;
    for (int i = PIR_GREEN; i < PIR_GREEN+3; i++)
    {
        PwmStop(i-PIR_GREEN+1);
        // 可控制设备断连
        device_status[i-PIR_GREEN+1] = DEVICE_DISCONNECT;
    }
}

osThreadId_t pir_task(void)
{
    osThreadAttr_t attr;

    attr.name = "pir_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityNormal;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_pir, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[pir_task] Falied to create pir_task!\n");
    }
    return module_id;
}