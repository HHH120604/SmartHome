#include <stdio.h>
#include <unistd.h>
#include "ohos_init.h"
#include "cmsis_os2.h"
#include "wifiiot_gpio.h"
#include "wifiiot_gpio_ex.h"
#include "oled_ssd1306.h"

#include "main.h"
#include "FIRE_module.h"
#include "GAS_module.h"
#include "LCD_module.h"
#include "LED_module.h"
#include "PIR_module.h"
#include "TAH_module.h"
#include "WIFI_module.h"

void init_lcd(void)
{
    GpioInit();
    OledInit();
    OledFillScreen(0x00); //清屏
}

void start_lcd(void)
{
    init_lcd();

    OledShowString(0, 0, "-- Smart Home --", 1);

    char line[32] = {0};
    while (!toStop)
    {
        int x = 0, y = 1;

        snprintf(line, sizeof(line), "fire:%-3d gas:%-3d", fire_fire, gas_gas);
        OledShowString(x, y++, line, 1);

        snprintf(line, sizeof(line), "led:%d%d%d%d pir:%d%d%d", device_status[LED_RED], device_status[LED_GREEN], device_status[LED_YELLOW],
            device_status[LED_BEEP], device_status[PIR_GREEN], device_status[PIR_RED], device_status[PIR_BLUE]);
        OledShowString(x, y++, line, 1);

        snprintf(line, sizeof(line), "pir:%-4dlux:%-4d", pir_pir, pir_lux);
        OledShowString(x, y++, line, 1);

        snprintf(line, sizeof(line), "temp:%-3d hum:%-3d", tah_temp, tah_hum);
        OledShowString(x, y++, line, 1);

        snprintf(line, sizeof(line), "fan:%-4dpump:%-3d", device_status[TAH_FAN], device_status[TAH_PUMP]);
        OledShowString(x, y++, line, 1);
        
        osDelay(delay/100);
    }
    
}

void stop_lcd(void)
{
    OledFillScreen(0x00); //清屏
}

osThreadId_t lcd_task(void)
{
    osThreadAttr_t attr;

    attr.name = "lcd_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityAboveNormal;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_lcd, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[ERROR][lcd_task]: Falied to create lcd_task!\n");
    }
    return module_id;
}