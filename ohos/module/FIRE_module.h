#ifndef _FIRE_MODULE_H_
#define _FIRE_MODULE_H_

osThreadId_t fire_task(void);
void init_fire(void);
void stop_fire(void);

extern int fire_fire; // FIRE红外火焰传感器
extern int fire_beep; // FIRE蜂鸣器

#endif