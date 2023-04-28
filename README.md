# face identity for [Home Assistant](https://home-assistant.io)  
## 插件说明
本插件利用海康威视的自带动静识别功能，因为自带的性能太差，误报太多。所以加了一道利用deepstack来进行物体识别。
海康威视摄像机里面设置，自动上报，方式选ftp，然后在设置里面添加好ftp服务器地址还有用户名密码，出去晃一晃，看看ftp里面是否上传了图片
deepstack安装方式
```shell
docker run -e VISION-DETECTION=True -v localstorage:/datastore -p 80:5000 deepquestai/deepstack
```

## 使用
下载插件, 并将 deepstack-ha-ftp 放置于 custom_components 文件夹下。

## 重要提示
对于许多用户出现`明明插件正确放置，但是 HomeAssistant 报插件找不到的错误` 只需要重启下 HomeAssistant 就好了。

## 配置示例 :
```YAML
sensor:
  - platform : deep_stack_ha_ftp
    name: deepstack_for_homeassistant
    deepstack_url: "*****************"
    ftp_server_addr: "*****************"
    ftp_user: "*****************"
    ftp_passwd: "*****************"
    ftp_path: /
    save_file_folder: images/
```