import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math

class Point(object):
    def __init__(self,xParam = 0.0,yParam = 0.0):
        self.x = xParam
        self.y = yParam
 
    def __str__(self):
        return "(%.2f, %.2f)"% (self.x ,self.y)
 
    def distance(self, pt):
        xDiff = self.x - pt.x
        yDiff = self.y - pt.y
        return math.sqrt(xDiff ** 2 + yDiff ** 2)

    def slopee(self, pt):
        xDiff = self.x - pt.x
        yDiff = self.y - pt.y
        if abs(xDiff) >= 0.9:
            return yDiff / xDiff
        else:
            print("该线段垂直于y轴")
            
class Regulation:
    def __init__(self, edge_points: list[Point]):
        if len(edge_points) < 10 and len(edge_points) > 2:
            self.edge_points = edge_points
            self.angle = 0
        if len(edge_points) == 2:
            print("提供的点数太少,将该两点视为矩形角点。")
            rect = []
            rect.append(edge_points[0])
            rect.append(Point(edge_points[0].x, edge_points[1].y))
            rect.append(edge_points[1])
            rect.append(Point(edge_points[1].x, edge_points[0].y))
            self.edge_points = edge_points
            
        if len(edge_points) > 10:
            print("测区形状过于复杂,将使用DP法进行轮廓简化,请您最好重新规划路线。")
            #self.edge_points = cv.approxPolyDP(edge_points, 50, True)
    
    def get_angle(self):
        max_distance = 0
        start_point_index = 0
        for i in range(len(self.edge_points) - 1):
            if self.edge_points[i].distance(self.edge_points[i + 1]) > max_distance:
                max_distance = self.edge_points[i].distance(self.edge_points[i + 1])
                start_point_index = i
        if  self.edge_points[0].distance(self.edge_points[-1]) > max_distance:
            max_distance = self.edge_points[0].distance(self.edge_points[-1])
            start_point_index = len(self.edge_points) - 1
        self.edge_points = self.edge_points[start_point_index : ] + self.edge_points[ : start_point_index]
        self.angle = self.edge_points[0].slopee(self.edge_points[1])
       
    def turn_Polygen(self):
        new_edge_points = []
        h = math.atan(self.angle)#斜率转角度
        origin_x = self.edge_points[0].x
        origin_y = self.edge_points[0].y
        for point in self.edge_points:
            point.x = point.x - origin_x
            point.y = point.y - origin_y
            new_x = round(point.x * math.cos(h) + point.y * math.sin(h))
            new_y = round(-point.x * math.sin(h) + point.y * math.cos(h))
            point.x = new_x
            point.y = abs(new_y)
            new_edge_points.append(point)  
        self.edge_points = new_edge_points
        
class Trajectory:
    def __init__(self, scale = 1/2000, length_EW = 5e4, length_NS = 3e4, 
                 height_min = 20, height_max = 200, GSD = 0.2, f = 5.02e-2, 
                 size_pix = 6.8e-6, rows_num = 1.4e4, cols_num = 1e4, 
                 pic_h = 9.52e-2, pic_w = 6.8e-2, direction = "EW",
                 overlap_along = 0.65, overlap_beside = 0.3, shift_bias = 1, speed_plane = 50):
        self.scale = scale 
        self.length_EW = length_EW
        self.length_NS = length_NS
        self.height_min = height_min
        self.height_max = height_max
        self.GSD = GSD
        self.f = f
        self.size_pix = size_pix
        self.rows_num = rows_num
        self.cols_num = cols_num
        self.pic_h = pic_h
        self.pic_w = pic_w
        self.direction = direction
        self.overlap_along = overlap_along
        self.overlap_beside = overlap_beside
        self.shift_bias = shift_bias
        self.speed_plane = speed_plane
        self.M = 0 #摄影比例尺分母
        self.H = 0 #摄影航高
        self.Bx = 0 #摄影基线长度
        self.By = 0 #航线间距
        self.num_along = 0 #航向相片数
        self.num_beside = 0 #航线数
        self.num_total = 0 #相片总数
        self.exposure = 0 #最大曝光时间
        print("Warning! 进行参数计算时必需遵循顺序，否则可能出现计算错误！")
        print("/********************开始计算**************************/")
        
    def calculate_M(self):
        M = round(self.GSD / self.size_pix)
        print("航摄比例尺: 1 / " + str(M))
        self.M = M
       
    def calculate_H(self):
        H = int(self.f * self.M)
        print("摄影航高为:"  + str(H))
        self.H = H
    
    def refresh_overlap(self):
        height_mean = (self.height_min + self.height_max) / 2
        delta_height = self.height_max - height_mean
        new_alone = self.overlap_along + (1 - self.overlap_along) * delta_height / self.H
        new_beside = self.overlap_beside + (1 - self.overlap_beside) * delta_height / self.H
        self.overlap_along = new_alone
        self.overlap_beside = new_beside
        print("航向重叠度为:{:.2f}".format(self.overlap_along))
        print("旁向重叠度为:{:.2f}".format(self.overlap_beside))
    
    def calculate_B(self):
        self.By = int (self.pic_h * self.M *(1 - self.overlap_beside))
        self.Bx = int (self.pic_w * self.M *(1 - self.overlap_along))
        print("航线间距为:" + str(self.By))
        print("摄影基线长度为:"  + str(self.Bx))
        
    def calculate_num_pics_rect(self):
        if self.direction == "EW":
            self.num_along = round(self.length_EW / self.Bx) + 1 + 2
            self.num_beside = round(self.length_NS / self.By) + 1
        elif self.direction == "NS":
            self.num_along = round(self.length_NS / self.Bx) + 1 + 2
            self.num_beside = round(self.length_EW / self.By) + 1
        else:
            print("必须指定东西向EW或者南北向NS")
        self.num_total = self.num_along * self.num_beside #相片总数
        
        print("每条航向相片数为:" + str(self.num_along))
        print("航线数:" + str(self.num_beside))
        print("相片总数为:" + str(self.num_total))
    
    def calculate_num_pics_polygen(self, edge_points : list[Point]):
        num_points = len(edge_points)
        x = []
        y = []
        for point in edge_points:
            x.append(point.x)
            y.append(point.y)
        max_x = max(x)
        min_x = min(x)
        max_y = max(y)
        min_y = min(y)
        index = y.index(max_y)
        true_x = []
        true_y = []
        width = max_x - min_x
        height = max_y - min_y   
        self.num_along = round(width / self.Bx) + 1 + 2
        self.num_beside = round(height / self.By) + 1
        
        true_x.append(-self.Bx)
        true_y.append(0)
        for i in range(self.num_along):
                tem_x = int(min_x + i * self.Bx)
                if tem_x >= 0 and tem_x <= edge_points[1].x:
                    true_x.append(tem_x)
                    true_y.append(0)
                    if tem_x + self.Bx > edge_points[1].x:
                        true_x.append(tem_x + self.Bx)
                        true_y.append(0)
                        
        for j in range(1, self.num_beside):
            tem_y = int(min_y + j * self.By)
            intersect_x = 0
            intersect_x_2 = []
            for k in range(1, num_points):
                up = max([edge_points[k].y, edge_points[(k + 1) % num_points].y])
                down = min([edge_points[k].y, edge_points[(k + 1) % num_points].y])
                if tem_y >= down and tem_y <= up:
                    if edge_points[k].x != edge_points[(k + 1) % num_points].x:
                        a = (edge_points[(k+1)%num_points].y - edge_points[k].y) / (edge_points[(k+1)%num_points].x - edge_points[k].x)
                        b = edge_points[k].y - a * edge_points[k].x
                        intersect_x = int((tem_y - b) / a)
                    else:
                        intersect_x = edge_points[k].x
                    intersect_x_2.append(intersect_x)
            intersect_x_2.sort()
            
            line_x = []
            line_y = []  
            for i in range(self.num_along):
                tem_x = int(min_x + i * self.Bx)
                
                if tem_x >= intersect_x_2[0] and tem_x <= intersect_x_2[1]:
                    if tem_x - self.Bx < intersect_x_2[0]:
                        line_x.append(tem_x - self.Bx)
                        line_y.append(tem_y)
                    line_x.append(tem_x)
                    line_y.append(tem_y)
                    if tem_x + self.Bx > intersect_x_2[1]:
                        line_x.append(tem_x + self.Bx)
                        line_y.append(tem_y)
            if j%2 == 1:
                line_x = sorted(line_x, reverse=True)
            true_x = true_x + line_x
            true_y = true_y + line_y
        true_x.append(edge_points[index].x)
        true_y.append(true_y[-1] + self.By)
        print("Warning!这里计算的是多边形航迹规划,每条航向数不同")
        print("航线数:" + str(self.num_beside))
        print("相片总数为:" + str(len(true_x)))
        return true_x, true_y
        
    def calculate_exposure(self):
        height_mean = (self.height_min + self.height_max) / 2
        self.exposure = self.shift_bias * self.size_pix * (self.H - height_mean) / (self.speed_plane * self.f)
        print("最大曝光时间为:" + str(self.exposure))
        print("/********************结束计算**************************/")
        
class Drawpicture(Trajectory):
    def __init__(self, point_start = "左上", zoom = 0.5, 
                 scale = 1/2000, length_EW = 5e4, length_NS = 3e4, 
                 height_min = 20, height_max = 200, GSD = 0.2, f = 5.02e-2, 
                 size_pix = 6.8e-6, rows_num = 1.4e4, cols_num = 1e4, 
                 pic_h = 9.52e-2, pic_w = 6.8e-2, direction = "EW",
                 overlap_along = 0.65, overlap_beside = 0.3, shift_bias = 1, speed_plane = 50):
        
        super(Drawpicture, self).__init__(scale = scale, length_EW = length_EW, length_NS = length_NS, 
                 height_min = height_min, height_max = height_max, GSD = GSD, f = f, 
                 size_pix = size_pix, rows_num = rows_num, cols_num = cols_num, 
                 pic_h = pic_h, pic_w = pic_w, direction = direction,
                 overlap_along = overlap_along, overlap_beside = overlap_beside, shift_bias = shift_bias, speed_plane = speed_plane)
        
        self.zoom = zoom
        self.point_start = point_start
        self.point_list_x = []
        self.point_list_y = []
        self.point_list_sort = []
        self.img = None
        
    def create_blank_image(self):
        L = int(self.length_NS * 1.2 * self.zoom)
        W = int(self.length_EW * 1.2 * self.zoom)
        img = np.zeros((L ,W , 3), np.uint8)
        img.fill(255)
        img[int(L*0.1) : int(L*0.1)+int(self.length_NS*self.zoom), int(W*0.1) : int(W*0.1)+int(self.length_EW*self.zoom), :] = (0, 230, 0)
        self.img = img
    
    def draw_picture(self):
        if self.direction == "EW":
            if self.point_start ==  "左上":
                for j in range(self.num_beside):
                    for i in range(self.num_along):
                        x = int(((self.length_EW * 0.1) + i * self.Bx) * self.zoom)
                        y = int(((self.length_NS * 0.1) + j * self.By) * self.zoom)
                        
                        self.point_list_y.append(y)
                        if j%2 == 0:
                            self.point_list_x.append(x)
                        else:
                            self.point_list_x.append(int(((self.length_EW * 0.1) + (self.num_along - 1 - i) * self.Bx) * self.zoom))
                        
                        rectangle_w = self.M * self.pic_w * self.zoom
                        rectangle_h = self.M * self.pic_h * self.zoom
                        
                        point_left_up = (x - int(rectangle_w / 2), y + int(rectangle_h / 2))
                        point_right_down = (x + int(rectangle_w / 2), y - int(rectangle_h / 2))
                        cv.circle(self.img, (x, y), 20, (0, 0, 255), 20)
                        cv.rectangle(self.img, point_left_up, point_right_down, ((i+1)*(j+1)%255 , i%255, j%255), 20)
            cv.imwrite("range.jpg", self.img)
            print("\n/***************航片覆盖范围绘图完成*******************/\n")
    
    def get_xy(self):
        return self.point_list_x, self.point_list_y
    


    
    
        
    
    