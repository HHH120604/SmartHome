#ifndef _CONTROL_H_
#define _CONTROL_H_

int parse(unsigned char *payload, int len); // mqtt指令解析
int module_control(int *command);
int device_control(int *command);
int module_start(int module_id);
int module_stop(int module_id);

#endif