#ifndef _MAIN_H_
#define _MAIN_H_

enum{
    // module status for: FIRE GAS LCD LED MQTT PIR T&H
    FIRE_MODULE,
    GAS_MODULE,
    LCD_MODULE,
    LED_MODULE,
    MQTT_MODULE,
    PIR_MODULE,
    TAH_MODULE,
    MODULE_NUM
};

enum {
    // device
    LED_RED,
    LED_GREEN,
    LED_YELLOW,
    LED_BEEP,
    PIR_GREEN,
    PIR_RED,
    PIR_BLUE,
    TAH_FAN,
    TAH_PUMP,
    DEVICE_NUM
};

enum {
    // device level
    DEVICE_CLOSE,
    DEVICE_ON1,
    DEVICE_ON2,
    DEVICE_ON3,
    DEVICE_ON4,
    DEVICE_ON5,
    DEVICE_ON6,
    DEVICE_ON7,
    DEVICE_ON8,
    DEVICE_DISCONNECT,
};

extern int toStop;
extern uint32_t delay;
extern osThreadId_t module_status[];
extern int device_status[];
extern int publish_state;
extern unsigned int beep_freq;
extern unsigned int beep_duty;
extern unsigned int led_freq;
extern unsigned int led_duty;

#endif