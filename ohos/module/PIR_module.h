#ifndef _PIR_MODULE_H_
#define _PIR_MODULE_H_

osThreadId_t pir_task(void);
void stop_pir(void);

extern int pir_pir; // PIR人体红外传感器
extern int pir_lux; // PIR光敏电阻

#endif