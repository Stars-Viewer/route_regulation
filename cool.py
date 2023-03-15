import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import matplotlib.animation as animation

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
        
    def calculate_num_pics(self):
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
    


    
    
        
    
    