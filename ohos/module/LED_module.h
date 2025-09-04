#ifndef _LED_MODULE_H_
#define _LED_MODULE_H_

osThreadId_t led_task(void);
void init_led(void);
void stop_led(void);

#endif