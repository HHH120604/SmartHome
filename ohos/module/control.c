#include <stdio.h>
#include <stdlib.h>
#include <cmsis_os2.h>

#include "main.h"
#include "control.h"
#include "FIRE_module.h"
#include "GAS_module.h"
#include "LCD_module.h"
#include "LED_module.h"
#include "MQTT_module.h"
#include "PIR_module.h"
#include "TAH_module.h"
#include "WIFI_module.h"

enum {
    MODULE_CODE,
    PUBLISH_CODE,
    DEVICE_CODE,
};

#define FAILED 0
#define SUCCESS 1

int parse(unsigned char *payload, int len)
{
    int rc = SUCCESS;
    int size = 10;
    // 解析指令类型
    int code = payload[0] - '0';
    // 控制指令
    int *command = (int *)calloc(size, sizeof(int));
    for (int i = 0; i < size; i++) command[i] = 0;
    for (int i = 1; i < len; i++) command[i-1] = payload[i] - '0';
    switch (code)
    {
    case MODULE_CODE:
        rc = module_control(command);
        break;
    case PUBLISH_CODE:
        // rc = publish_control(command);
        publish_state = 1;
        rc = SUCCESS;
        break;
    case DEVICE_CODE:
        rc = device_control(command);
        break;
    default:
        printf("[ERROR] error code %d\n", code);
        rc = FAILED;
    }
    free(command);
    return rc;
}

int module_control(int *command)
{
    int rc = SUCCESS; // 返回状态码
    for (int i = 0; i < MODULE_NUM; i++)
    {
        // 检测当前模块工作状态与指令状态是否相同
        if (command[i] != (module_status[i] != NULL)) // 不相同时进行启动或暂停
        {
            printf("module %d: %d, statu: %d\n", i, command[i], module_status[i] != NULL);
            if (command[i]) rc = module_start(i); // 需要启动的模块
            else rc = module_stop(i); // 需要终止的模块
        }
    }
    return rc;
}

// int publish_control(int *command)
// {
//     char *message = "None";
//     int rc = SUCCESS; // 返回状态码
//     for (int i = 0; i < MODULE_NUM; i++)
//     {
//         // 检测当前模块是否处于工作状态
//         if (command[i] && (module_status[i] != NULL)) // 工作中的模块才可获取信息
//         {
            
//         }
//     }
//     return rc;
// }

int device_control(int *command)
{
    int rc = SUCCESS; // 返回状态码
    for (int i = 0; i < DEVICE_NUM; i++)
    {
        // 检测当前模块是否处于工作状态
        if ((device_status[i] != DEVICE_DISCONNECT)) // 工作中的模块才可获取信息
        {
            device_status[i] = command[i];
        }
    }
    return rc;
}

int module_start(int module_id)
{
    if (module_id >= MODULE_NUM) printf("[ERROR: module id: %d out of range 0~%d\n]", module_id, MODULE_NUM);
    if (module_status[module_id] != NULL)
    {
        printf("[WARN]: module %d has been started before!\n");
        return SUCCESS;
    }
    switch (module_id)
    {
    case FIRE_MODULE:
        module_status[FIRE_MODULE] = fire_task();
        break;
    case GAS_MODULE:
        module_status[GAS_MODULE] = gas_task();
        break;
    case LCD_MODULE:
        module_status[LCD_MODULE] = lcd_task();
        break;
    case LED_MODULE:
        module_status[LED_MODULE] = led_task();
        break;
    case MQTT_MODULE:
        // module_status[MQTT_MODULE] = mqtt_task(); // mqtt线程暂不提供更改
        break;
    case PIR_MODULE:
        module_status[PIR_MODULE] = pir_task();
        break;
    case TAH_MODULE:
        module_status[TAH_MODULE] = tah_task();
        break;
    default:
        printf("[ERROR]: No matched module id: %d\n", module_id);
        return FAILED;
        break;
    }
    if (module_status[module_id] == NULL) return FAILED;
    printf("module %d start success\n", module_id);
    return SUCCESS;
}

int module_stop(int module_id)
{
    osStatus_t rc = osOK;
    if (module_id == MQTT_MODULE) return rc; // mqtt线程暂不提供更改
    if (module_id >= MODULE_NUM) printf("[ERROR: module id: %d out of range 0~%d\n]", module_id, MODULE_NUM);
    if (module_status[module_id] == NULL)
    {
        printf("[WARN]: module %d has been stopped before!\n", module_id);
        return SUCCESS;
    }
    if (module_id != MQTT_MODULE) rc = osThreadTerminate(module_status[module_id]);
    if (rc != osOK)
    {
        printf("[ERROR]: module id: %d stop faied with osStatus_t %d\n", module_id, rc);
        return FAILED;
    }
    else
    {
        // 线程终止后处理
        module_status[module_id] = NULL;
        switch (module_id)
        {
        case FIRE_MODULE:
            stop_fire();
            break;
        case GAS_MODULE:
            stop_gas();
            break;
        case LCD_MODULE:
            stop_lcd();
            break;
        case LED_MODULE:
            stop_led();
            break;
        case MQTT_MODULE:
            break;
        case PIR_MODULE:
            stop_pir();
            break;
        case TAH_MODULE:
            stop_tah();
            break;
        default:
            printf("[ERROR]: No matched module id: %d\n", module_id);
            return FAILED;
            break;
        }
    }
    printf("module %d stop success\n", module_id);
    return SUCCESS;
}