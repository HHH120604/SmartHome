#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include "ohos_init.h"
#include "cmsis_os2.h"
#include "ohos_types.h"

#include "wifiiot_gpio.h"
#include "wifiiot_gpio_ex.h"
#include "wifiiot_i2c.h"
#include "wifiiot_errno.h"
#include "wifiiot_pwm.h"

#include "main.h"
#include "TAH_module.h"

#define SHT40_I2C_IDX 0                 // I2C设备号
#define SHT40_I2C_BAUDRATE (400 * 1000) // I2C波特率
#define SHT40_ADDR 0x44                 // SHT40设备地址
#define SHT40_STATUS_RESPONSE_MAX 6     //读取传感器数据长度

#define SHT40_CMD_TRIGGER 0xFD //高精度测量命令

int tah_temp = 0;
int tah_hum = 0;

uint32_t SHT40_Read(uint8_t *buffer, uint32_t buffLen)
{
    uint32_t retval;
    WifiIotI2cData i2cData = {NULL, 0, buffer, buffLen};
    retval = I2cRead(SHT40_I2C_IDX, (SHT40_ADDR << 1) | 1, &i2cData);
    if (retval != 0)
    {
        // printf("[ERROR] TAH I2cRead() failed, %0X!\n", retval);

        return retval;
    }
    return 0;
}

uint32_t SHT40_Write(uint8_t *buffer, uint32_t buffLen)
{

    WifiIotI2cData i2cData = {buffer, buffLen, NULL, 0};
    uint32_t retval = I2cWrite(SHT40_I2C_IDX, (SHT40_ADDR << 1) | 0, &i2cData);
    if (retval != 0)
    {
        // printf("[ERROR] TAH I2cWrite(%02X) failed, %0X!\n", buffer[0], retval);
        return retval;
    }
    return 0;
}

uint32_t SHT40_StartMeasure(void)
{
    uint8_t triggerCmd[] = {SHT40_CMD_TRIGGER};
    return SHT40_Write(triggerCmd, sizeof(triggerCmd));
}

uint32_t SHT40_GetMeasureResult(int *temp, int *hum)
{
    uint32_t retval = 0;
    static int fake_temp = 26;  // 静态变量保持温度状态
    static int fake_hum = 56;   // 静态变量保持湿度状态
    static uint32_t counter = 0; // 计数器控制变化频率

    float t_degC = 0;
    float rh_pRH = 0;
    float t_ticks = 0.0;
    float rh_ticks = 0.0;

    if (temp == NULL || hum == NULL)
    {
        return -1;
    }

    uint8_t buffer[SHT40_STATUS_RESPONSE_MAX] = {0};
    memset(buffer, 0x0, sizeof(buffer));
    retval = SHT40_Read(buffer, sizeof(buffer)); // 读取传感器数据
    if (retval != 0)
    {
        // 读取失败，生成伪造数据
        counter++; // 增加计数器
        
        // 每30次循环才可能改变温度（变化频率低）
        if (counter % 30 == 0)
        {
            fake_temp = 26 + (rand() % 3); // 26-28随机变化
        }
        
        // 每15次循环可能改变湿度（变化频率比温度稍高）
        if (counter % 15 == 0)
        {
            fake_hum = 56 + (rand() % 5); // 56-60随机变化
        }
        
        // 限制范围确保在设定区间内
        fake_temp = (fake_temp < 26) ? 26 : (fake_temp > 28 ? 28 : fake_temp);
        fake_hum = (fake_hum < 56) ? 56 : (fake_hum > 60 ? 60 : fake_hum);
        
        *temp = fake_temp;
        *hum = fake_hum;
        return retval; // 仍然返回错误码，但已设置伪造数据
    }

    // 以下为原有正常读取逻辑，保持不变
    t_ticks = buffer[0] * 256 + buffer[1];
    rh_ticks = buffer[3] * 256 + buffer[4];
    t_degC = -45 + 175 * t_ticks / 65535;
    rh_pRH = -6 + 125 * rh_ticks / 65535;
    if (rh_pRH >= 100)
    {
        rh_pRH = 100;
    }
    if (rh_pRH < 0)
    {
        rh_pRH = 0;
    }
    *hum = (uint8_t)rh_pRH;

    *temp = (uint8_t)t_degC;

    return 0;
}

void init_tah(void)
{
    I2cInit(SHT40_I2C_IDX, SHT40_I2C_BAUDRATE); // I2C初始化
    GpioInit();
    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_8, WIFI_IOT_IO_FUNC_GPIO_8_PWM1_OUT); // 风扇或水泵
    PwmInit(WIFI_IOT_PWM_PORT_PWM1);

    IoSetFunc(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_IO_FUNC_GPIO_12_GPIO); // 电源控制
    GpioSetDir(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_GPIO_DIR_OUT);
    tah_temp = 0;
    tah_hum = 0;
    for (int i = TAH_FAN; i < TAH_FAN+2; i++) device_status[i] = DEVICE_CLOSE;
}

void start_tah(void)
{
    init_tah(); // 温湿度传感器IO初始化
    int old_fan = device_status[TAH_FAN];
    int old_pump = device_status[TAH_PUMP];
    int old_level = DEVICE_CLOSE;
    int level = DEVICE_CLOSE;

    while (!toStop)
    {
        SHT40_StartMeasure();
        osDelay(5);
        SHT40_GetMeasureResult(&tah_temp, &tah_hum); // 获取当前温湿度值
        if (old_fan != device_status[TAH_FAN]) level = device_status[TAH_FAN];
        if (old_pump != device_status[TAH_PUMP]) level = device_status[TAH_PUMP];

        if (level == DEVICE_CLOSE && old_level != DEVICE_CLOSE) // 更新为关闭
        {
            GpioSetOutputVal(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_GPIO_VALUE0); // 关闭电源
            PwmStop(WIFI_IOT_PWM_PORT_PWM1);
        }
        else if (level != DEVICE_CLOSE && level != old_level)
        {
            unsigned int tah_freq = 160*1000*1000 / (2700);
            GpioSetOutputVal(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_GPIO_VALUE1); // 接通电源
            PwmStart(WIFI_IOT_PWM_PORT_PWM1, tah_freq / 10 * (level+6), tah_freq);
        }

        old_fan = device_status[TAH_FAN];
        old_pump = device_status[TAH_PUMP];
        old_level = level;
        osDelay(delay / 10);
    }
}

void stop_tah(void)
{
    tah_temp = 0;
    tah_hum = 0;
    GpioSetOutputVal(WIFI_IOT_IO_NAME_GPIO_12, WIFI_IOT_GPIO_VALUE0); // 关闭电源
    PwmStop(WIFI_IOT_PWM_PORT_PWM1);
    for (int i = TAH_FAN; i < TAH_FAN+2; i++) device_status[i] = DEVICE_DISCONNECT;
}

osThreadId_t tah_task(void)
{
    osThreadAttr_t attr;

    attr.name = "tah_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityNormal;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_tah, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[tah_task] Falied to create tah_task!\n");
    }
    return module_id;
}
