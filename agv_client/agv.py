from toolbox.comm.http_op import HttpRequest


class AgvHttpClient:

    def __init__(self) -> None:
        self.req = HttpRequest(ip="127.0.0.1")

    def get_robot_res(self):
        return self.req.get("ctl/get_robot_res")
    
    def cancel_move(self):
        return self.req.get("ctl/cancel_move")
    
    def velocity_control_stop(self):
        return self.req.get("ctl/velocity_control_stop")
        
    def list_map_marker(self):
        return self.req.get("ctl/list_map_marker")
        
    def list_map(self):
        return self.req.get("ctl/list_map")

    def force_stop(self, flag=1):
        return self.req.post("ctl/force_stop", json={
            "flag": flag
        })

    def nav_to_target(self, name="1234"):
        return self.req.post("ctl/nav_to_target", json={
            "name": name
        })
    
    def velocity_control(self, linear_v=0, angular_v=0):
        return self.req.post("ctl/velocity_control", json={
            "linear_v": linear_v,
            "angular_v": angular_v,
        })
    
    
