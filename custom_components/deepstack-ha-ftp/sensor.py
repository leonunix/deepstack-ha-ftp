# 利用海康威视自带的动静检测功能，当触发时候将图片上传到ftp，然后通过次插件去ftp获取图片。
# 然后交给devstack做对象识别，然后在homeassistant中显示。
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import os
from ftplib import FTP
from homeassistant.helpers.entity import Entity
import logging
from deepstack_sdk import ServerConfig, Detection,viz


_LOGGER = logging.getLogger(__name__)

NAME="name"
DEEPSTACK_URL= "deepstack_url"
FTP_SERVER_ADDR = "ftp_server_addr"
FTP_USER = "ftp_user"
FTP_PASSWD = "ftp_passwd"
FTP_PATH = "ftp_path"
CONF_SAVE_FILE_FOLDER = "save_file_folder"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(NAME): cv.string,
    vol.Required(DEEPSTACK_URL): cv.string,
    vol.Required(FTP_SERVER_ADDR): cv.string,
    vol.Required(FTP_USER): cv.string,
    vol.Required(FTP_PASSWD): cv.string,
    vol.Required(FTP_PATH): cv.string,
    vol.Required(CONF_SAVE_FILE_FOLDER): cv.string,
})

OBJECT_DETECTED = ["person","cat"]

def setup_platform(hass, config, add_devices,
                   discovery_info=None):
    tmp_path = hass.config.path('ftp/deepstack/')
    '''import os'''
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    name = config.get(NAME)
    deepstack_url = config.get(DEEPSTACK_URL)
    ftp_server_addr = config.get(FTP_SERVER_ADDR)
    ftp_user = config.get(FTP_USER)
    ftp_passwd = config.get(FTP_PASSWD)
    ftp_path = config.get(FTP_PATH)
    save_file_folder = config.get(CONF_SAVE_FILE_FOLDER)

    add_devices([DeepstackSensor(deepstack_url,ftp_server_addr,ftp_user,ftp_passwd,ftp_path,name,tmp_path,save_file_folder)])
    
    
class DeepstackSensor(Entity):
    def __init__(self,deepstack_url,ftp_server_addr,ftp_user,ftp_passwd,ftp_path,name,tmp_path,save_file_folder) -> None:
        super().__init__()
        self._deepstack_config = ServerConfig(deepstack_url)
        self._ftp_server_addr = ftp_server_addr
        self._ftp_user = ftp_user
        self._ftp_passwd = ftp_passwd
        self._ftp_path = ftp_path
        self._name = name
        self._state = False
        self._attr = None
        self._tmp_path = tmp_path
        self._save_file_folder = save_file_folder

        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._name

    @property
    def name(self):
        return self._name
    
    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attr

    def update(self):
        self.searching()

    def get_image_from_ftp(self) -> None:
        ftp = FTP() #初始化一个对象
        # ftp.set_debuglevel(2) #打开调试级别2，显示详细信息
        ftp.connect(self._ftp_server_addr,21) #链接ftp server 和端口
        ftp.login(self._ftp_user,self._ftp_passwd) # 登录用户名和密码
        
        ftp.cwd(self._ftp_path) #进入远程目录
        
        # Get image list
        file_list = ftp.nlst() #获取目录下的文件
        
        for file in file_list:
            if ".jpg" in file:
                # save image to tmp_path
                _LOGGER.info("Get image from ftp: %s",file)
                file_handler = open(self._tmp_path + file,'wb')
                ftp.retrbinary("RETR " + file ,file_handler.write)
                file_handler.close()
                _LOGGER.debug("Saved image to tmp_path: %s",self._tmp_path + file)
                
                # delete image from ftp
                ftp.delete(file)
                _LOGGER.info("Deleted image from ftp: %s",file)
                
    def send_image_to_deepstack(self):
        detection = Detection(self._deepstack_config)
        # get file list from tmp_path
        image_list = os.listdir(self._tmp_path)
        responses = []
        for file in image_list:
            if ".jpg" in file:
                image_byte = open(self._tmp_path + file, "rb").read()
                try:
                    response = detection.detectObject(image_byte)
                    _LOGGER.debug("Send image to deepstack: %s",file)
                    for obj in response:
                        needbreak = False
                        _LOGGER.debug("Name: {}, Confidence: {}, x_min: {}, y_min: {}, x_max: {}, y_max: {}".format(obj.label, obj.confidence, obj.x_min, obj.y_min, obj.x_max, obj.y_max))
                        for o in OBJECT_DETECTED:
                            if o in obj.label:
                                # save image
                                detection.detectObject(image_byte, output=self._save_file_folder + file)
                                responses.append(response)
                                needbeak=True
                                break
                        if needbreak:
                            break
                except Exception as e:
                    _LOGGER.debug("Error: %s",e)
                    
                # delete image from tmp_path
                os.remove(self._tmp_path + file)
                
        return responses
    
    
    def searching(self):
        self.get_image_from_ftp()
        responses = self.send_image_to_deepstack()
        self._attr = {}
        for o in OBJECT_DETECTED:
             self._attr[o] = 0
        if len(responses) > 0:
            self._state = True
            for response in responses:
                for obj in response:
                    for o in OBJECT_DETECTED:
                        if o in obj.label:
                            self._attr[o] += 1
        else :
            self._state = False
    

        
        

        
        
    
    
        
    
