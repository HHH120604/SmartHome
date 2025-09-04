#ifndef _TAH_MODULE_H_
#define _TAH_MODULE_H_

osThreadId_t tah_task(void);
void stop_tah(void);

extern int tah_temp;
extern int tah_hum;

#endif