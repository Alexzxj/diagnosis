class Session():
    def init(self):
        """定义一个全局变量"""
        global _global_dict
        _global_dict = {}

    def set(self, key, value):
        """保存session"""
        _global_dict[key] = value

    def get(self, key, defValue=None):
        """获取session"""
        try:
            return _global_dict[key]
        except KeyError:
            return defValue
