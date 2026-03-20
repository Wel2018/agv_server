import json
import time
import requests
import functools
from toolbox.core.log import printc
from typing import Optional, Callable, Any


def ret_res(res: requests.Response) -> dict:
    """返回结果"""
    return json.loads(res.text)

def request_handler(
    timeout: Optional[float] = None,
    max_retry: int = 1,
    retry_delay: float = 1.0,
    retry_exceptions: tuple = (
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError
    )
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[requests.Response]:
            # --- 1. 适配逻辑：动态获取超时时间 ---
            actual_timeout = timeout
            
            # 如果装饰器没传 timeout，尝试从类或实例中获取
            if actual_timeout is None and args:
                # args[0] 在实例方法中是 self，在类方法中是 cls
                target = args[0]
                # 使用 getattr 安全获取，避免 args[0] 是普通参数时报错
                actual_timeout = getattr(target, "timeout", None)
            
            retry_count = 0
            last_exception = None
            
            while retry_count < max_retry:
                try:
                    # --- 2. 注入逻辑：仅在需要时注入 timeout ---
                    # 检查原函数是否接受 timeout 参数，避免触发 TypeError
                    # import inspect
                    # sig = inspect.signature(func)
                    # if "timeout" in sig.parameters:
                    kwargs["timeout"] = actual_timeout
                
                    # 执行原函数
                    # 注意：如果 ret_res 是你定义的外部函数，请确保它已导入
                    res = func(*args, **kwargs)
                    # return res # 这里建议直接返回，或确保 ret_res 逻辑正确
                    return ret_res(res)  # ty:ignore[invalid-return-type]
                
                except retry_exceptions as e:
                    retry_count += 1
                    last_exception = e
                    if retry_count < max_retry:
                        # 假设 printc 是你定义的彩色打印函数
                        printc(f"[{func.__name__}] 请求失败（第{retry_count}次重试），"
                              f"异常：{str(e)}，将在{retry_delay}秒后重试...", 'error')
                        time.sleep(retry_delay)
            
            printc(f"[{func.__name__}] 达到最大重试次数（{max_retry}次），请求失败，"
                  f"最终异常：{str(last_exception)}", 'error')
            return None
        return wrapper
    return decorator
