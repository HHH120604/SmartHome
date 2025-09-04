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
#include "GAS_module.h"

int gas_gas = 0; // GAS可燃气体检测
int gas_beep = 0; // GAS蜂鸣器
int gas_threshold = 300; // GAS气体报警阈值

void init_gas(void)
{
    GpioInit();
    // 蜂鸣器
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_9, WIFI_IOT_IO_FUNC_GPIO_9_PWM0_OUT);
    PwmInit(WIFI_IOT_PWM_PORT_PWM0);

    gas_gas = 0;
    gas_beep = 0;
}

void start_gas(void)
{
    init_gas();

    while (!toStop)
    {
        unsigned short data = 0;

        // 读取可燃气体输出
        if (AdcRead(WIFI_IOT_ADC_CHANNEL_5, &data, WIFI_IOT_ADC_EQU_MODEL_4, WIFI_IOT_ADC_CUR_BAIS_DEFAULT, 0) != WIFI_IOT_SUCCESS)
        {
            printf("GAS ADC_5 read failed!\n");
        }
        else
        {
            gas_gas = data;
        }
        // 蜂鸣器
        if (gas_gas > gas_threshold)
        {
            PwmStart(WIFI_IOT_PWM_PORT_PWM0, beep_freq / (100/beep_duty), beep_freq);
            gas_beep = 1;
            publish_state = 1;
        }
        else
        {
            PwmStop(WIFI_IOT_PWM_PORT_PWM0);
            gas_beep = 0;
        }
        osDelay(delay / 10);
    }
}

void stop_gas(void)
{
    PwmStop(WIFI_IOT_PWM_PORT_PWM0);
    gas_gas = 0;
    gas_beep = 0;
}

osThreadId_t gas_task(void)
{
    osThreadAttr_t attr;

    attr.name = "gas_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityNormal;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_gas, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[gas_task] Falied to create gas_task!\n");
    }
    return module_id;
}