#include <stdio.h>

#include <unistd.h>
#include <stdlib.h>
#include "ohos_init.h"
#include "cmsis_os2.h"

#include "hi_wifi_api.h"
//#include "wifi_sta.h"
#include "lwip/ip_addr.h"
#include "lwip/netifapi.h"

#include "lwip/sockets.h"
#include "MQTTPacket.h"
#include "transport.h"

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

void start_mqtt(void)
{
    // start wifi first
    start_wifi();

    MQTTPacket_connectData data = MQTTPacket_connectData_initializer;
    int rc = 0;
    int mysock = 0;
    unsigned char buf[200];
    int buflen = sizeof(buf);
    int msgid = 1;
    MQTTString topicString = MQTTString_initializer;
    int req_qos = 0;
    char payload[200];
    int payloadlen = strlen(payload);
    int len = 0;

    char *host = "192.168.17.107";
    int port = 1883;

    mysock = transport_open(host, port);
    if (mysock < 0)
        return;

    printf("Sending to hostname %s port %d\n", host, port);

    data.clientID.cstring = "hi3861_device";
    data.keepAliveInterval = 20;
    data.cleansession = 1;
    data.username.cstring = "hi3861_device";
    data.password.cstring = "a123456789";

    len = MQTTSerialize_connect(buf, buflen, &data);
    rc = transport_sendPacketBuffer(mysock, buf, len);

    /* wait for connack */
    if (MQTTPacket_read(buf, buflen, transport_getdata) == CONNACK)
    {
        unsigned char sessionPresent, connack_rc;

        if (MQTTDeserialize_connack(&sessionPresent, &connack_rc, buf, buflen) != 1 || connack_rc != 0)
        {
            printf("Unable to connect, return code %d\n", connack_rc);
            goto exit;
        }
    }
    else
        goto exit;

    /* subscribe */
    topicString.cstring = "hi3861/subscribe"; // 订阅主题
    len = MQTTSerialize_subscribe(buf, buflen, 0, msgid, 1, &topicString, &req_qos);
    rc = transport_sendPacketBuffer(mysock, buf, len);
    if (MQTTPacket_read(buf, buflen, transport_getdata) == SUBACK) /* wait for suback */
    {
        unsigned short submsgid;
        int subcount;
        int granted_qos;

        rc = MQTTDeserialize_suback(&submsgid, 1, &subcount, &granted_qos, buf, buflen);
        if (granted_qos != 0)
        {
            printf("granted qos != 0, %d\n", granted_qos);
            goto exit;
        }
    }
    else
        goto exit;

    topicString.cstring = "hi3861/publish"; // 发布主题
    uint32_t last_pub_time = osKernelGetTickCount() - delay; // 上次定时上报时间
    while (!toStop)
    {
        uint32_t now = osKernelGetTickCount();
        if ((now - last_pub_time) >= delay || publish_state)
        {
            // 构造发布内容
            snprintf(payload, sizeof(payload), "%d,%d,%d,%d,%d,%d", fire_fire, gas_gas, pir_pir, pir_lux, tah_temp, tah_hum);
            printf("published: %s\n", payload);
            payloadlen = strlen(payload);
            len = MQTTSerialize_publish(buf, buflen, 0, 0, 0, 0, topicString, (unsigned char *)payload, payloadlen);
            rc = transport_sendPacketBuffer(mysock, buf, len);
            publish_state = 0;
            last_pub_time = now;
        }

        // 解析订阅结果
        if (MQTTPacket_read(buf, buflen, transport_getdata) == PUBLISH)
        {
            unsigned char dup;
            int qos;
            unsigned char retained;
            unsigned short msgid;
            int payloadlen_in;
            unsigned char *payload_in;
            int rc;
            MQTTString receivedTopic;
            rc = MQTTDeserialize_publish(&dup, &qos, &retained, &msgid, &receivedTopic,
                &payload_in, &payloadlen_in, buf, buflen);
            if (rc == 1)
            {
                printf("subscribe: %d, %s\n", payloadlen_in, payload_in);
                rc = parse(payload_in, payloadlen_in);
            }
            else printf("[ERROR]: mqtt subscribe error code: %d\n", rc);

            rc = rc;
        }
        osDelay(delay / 100);
    }

    printf("mqtt disconnecting\n");
    len = MQTTSerialize_disconnect(buf, buflen);
    rc = transport_sendPacketBuffer(mysock, buf, len);

    exit:
        transport_close(mysock);

    rc = rc;
    return;
}

osThreadId_t mqtt_task(void)
{
    osThreadAttr_t attr;

    attr.name = "mqtt_task";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 4096; // 4096;
    attr.priority = osPriorityAboveNormal1;
    osThreadId_t module_id = osThreadNew((osThreadFunc_t)start_mqtt, NULL, &attr);
    if (module_id == NULL)
    {
        printf("[ERROR][mqtt_task]: Falied to create mqtt_task!\n");
    }
    return module_id;
}