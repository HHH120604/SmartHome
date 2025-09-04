#ifndef _GAS_MODULE_H_
#define _GAS_MODULE_H_

osThreadId_t gas_task(void);
void init_gas(void);
void stop_gas(void);

extern int gas_gas; // GAS可燃气体检测
extern int gas_beep; // GAS蜂鸣器

#endif