import pandas as pd
import sys
import matplotlib.pyplot as plt
from PIL import Image
import os
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as a3
import random
from matplotlib.pyplot import figure, draw, pause
import glob as glob
import cv2
import shutil
import json
import pickle

# imgs is a N x X x Y image stack

CELL_CNT = 0
cells_list = []
frames_list = []
master_shape = {}
MIN_CELL_AREA = 10
MOVEMENT_TOLERANCE = -3  #consider overlap isntead of moment;  This all depends on camera framerate + cell speed
#1) check for children (may need to be fancier for edge cases)

class Cell:
    def __init__(self, start_contour, start_frame, parent):
        global CELL_CNT
        self.id = CELL_CNT
        CELL_CNT += 1
        self.children = []
        self.parent_cell_id = parent
        self.frame_contours = {}
        self.frame_contours[str(start_frame)] = start_contour
        if os.path.exists('./cells/cell_'+str(self.id)):
            shutil.rmtree('./cells/cell_'+str(self.id))
        os.mkdir('./cells/cell_'+str(self.id))

    def set_frame_contour(self, f_num, con):
        self.frame_contours[str(f_num)] = con

    def get_frame_contour(self, f_num):
        return self.frame_contours[str(f_num)]

    def gen_vis_1(self, t0):
        if str(t0) in self.frame_contours:
            img = np.zeros(master_shape)
            img = cons_to_img([self.frame_contours[str(t0)]], master_shape[0], master_shape[1])
            cv2.imwrite('./cells/cell_'+str(self.id)+'/'+str(t0).zfill(3)+'.png', img)

    def gen_visualization(self):
        for i in range(0, len(frames_list)):
            img = np.zeros(master_shape)
            if str(i) in self.frame_contours:
                img = cons_to_img([self.frame_contours[str(i)]], master_shape[0], master_shape[1])
            cv2.imwrite('./cells/cell_'+str(self.id)+'/'+str(i).zfill(3)+'.png', img)
        os.chdir('./cells/cell_'+str(self.id))
        os.system('convert *.png mov.mov')
        os.chdir('../')
        os.chdir('../')

def simg(img):
    plt.ion()
    plt.imshow(img, cmap="gray")
    plt.show()
    a = input("Press Enter to continue...")
    #print (a)
    if(a == "x"):
        sys.exit()

def get_cells_in_f_num(f_num):
    ans = []
    for c in cells_list:
        if str(f_num) in c.frame_contours.keys():
            ans.append(c)
    return ans

def cons_to_img(cons, w, h):
    targ = np.zeros((w, h, 3), dtype=np.uint8)
    cv2.drawContours(targ, cons, -1, (255,255,255), thickness=-1)
    targ = cv2.cvtColor(targ, cv2.COLOR_BGR2GRAY)
    return targ

def process_start_frame():
    global cells_list, master_shape
    img = cv2.imread('imgs/start.tif')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    master_shape = gray.shape
    cs, hier = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cs:
        cells_list.append(Cell(c, -1, -1))

def load_images():
    global frames_list
    for g in glob.glob('imgs/t*.tif'):
        img = cv2.imread(g)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cs, hier = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        frames_list.append(cs)

def assign_watershed_contours(con, cell_list, t0, t1):
    #1) Get markers
    #2) generate mini_image
    #3) applywatershed to get markers
    #4) convert each watershed result to a contour

    #print(len(cell_list))
    #simg(cons_to_img([con], master_shape[0], master_shape[1]))

    marker_radius = 2
    targ_border = 10
    markers = []
    con_x,con_y,con_w,con_h = cv2.boundingRect(con)
    con_mini = con.copy()
    offset = (-con_x+targ_border, -con_y+targ_border)
    for j in range(0, len(con_mini)):
        con_mini[j][0][0] += offset[0]
        con_mini[j][0][1] += offset[1]

    for c in cell_list:
        print(cv2.contourArea(con))
        if(cv2.contourArea(con) < MIN_CELL_AREA):
            continue
        M = cv2.moments(c.get_frame_contour(t0))
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        markers.append({'x':cX-marker_radius+offset[0], 'y':cY-marker_radius+offset[1],'w':2*marker_radius, 'h':2*marker_radius})

    markers_img = np.zeros((con_h + targ_border * 2, con_w + targ_border * 2), np.uint8)
    sure_bg = np.zeros((con_h + targ_border * 2, con_w + targ_border * 2, 3), np.uint8)
    cv2.drawContours(sure_bg, [con_mini], -1, (255,255,255), thickness=-1)
    gray = cv2.cvtColor(sure_bg, cv2.COLOR_BGR2GRAY)
    markers_img = gray.copy()
    markers_img = np.where(markers_img > 100, -1, 0)

    cnt = 0
    for m in markers:
        cnt += 1
        print(m)
        markers_img[m['y']:(m['y']+m['h']),m['x']:(m['x']+m['w'])] = cnt
    markers_img = markers_img+1

    #simg(markers_img)
#    print(sure_bg.shape)
#    print(markers_img.shape)
    res = cv2.watershed(sure_bg, markers_img)
    #simg(res)

    x = np.unravel_index(np.argmax(res), res.shape)
    max_r = res[x[0], x[1]]
    final_cons = []
    for i in range(2, max_r+1):
        tmp = np.zeros(markers_img.shape, np.uint8)
        tmp[res==i] = 255
        cs, hier = cv2.findContours(tmp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cs = cs[0]
        for j in range(0, len(cs)):
            cs[j][0][0] -= offset[0]
            cs[j][0][1] -= offset[1]
        cell_list[i-2].set_frame_contour(t1, cs)
        tmmp = np.zeros((master_shape[0], master_shape[1], 3), np.uint8)
        cv2.drawContours(tmmp, [cs], -1, (255,0,255), thickness=-1)


def handle_frame_pair(t0, t1):
    prev_cells = get_cells_in_f_num(t0)
    curr_cons = frames_list[t1]
    #THE PLAN!
    #1) check for children
    #2) check for neighbors
    #3) else, add contour for frame

    cons_to_pars = {}
    constr_to_cons = {}

    for cell in prev_cells:
        hits = []
        tmmp = np.zeros((master_shape[0], master_shape[1], 3), np.uint8)
        print(cv2.contourArea(cell.get_frame_contour(t0)))
        if(cv2.contourArea(cell.get_frame_contour(t0)) < MIN_CELL_AREA):
            continue
        cv2.drawContours(tmmp, [cell.get_frame_contour(t0)], -1, (255,0,0), thickness=-1)
        M = cv2.moments(cell.get_frame_contour(t0))
        cell_cX = int(M["m10"] / M["m00"])
        cell_cY = int(M["m01"] / M["m00"])

        print(len(curr_cons))
        min_winner = {'val':-1000000, 'winner':-1}
        for con in curr_cons:
            print(cv2.contourArea(con))
            if(cv2.contourArea(con) < MIN_CELL_AREA):
                continue
            M = cv2.moments(con)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            #DEBUD
            tmmp = np.zeros((master_shape[0], master_shape[1], 3), np.uint8)
            cv2.drawContours(tmmp, [con], -1, (255,255,255), thickness=-1)
            print("time ["+str(t0)+"]: " + str(cv2.pointPolygonTest(cell.get_frame_contour(t0), (cX, cY), True)))

            #end EDUGB

            crit1 = cv2.pointPolygonTest(cell.get_frame_contour(t0), (cX, cY), True)
            crit2 = cv2.pointPolygonTest(con, (cell_cX, cell_cY), True)
            for cc in [crit1, crit2]:
                if cc > min_winner['val']:
                    min_winner['val'] = cc
                    min_winner['winner'] = con

            if(crit1 > MOVEMENT_TOLERANCE or crit2 > MOVEMENT_TOLERANCE):
                hits.append(con)

        if(len(hits) > 1):
            print('CHILD!!! -> ' + str(t0))
            cells_list.append(Cell(hits[0], t1, cell.id))
            cells_list.append(Cell(hits[1], t1, cell.id))
            break;
        elif(len(hits) == 1): #3 (tentatively associate)
            if not str(hits[0]) in cons_to_pars.keys():
                cons_to_pars[str(hits[0])] = []
                constr_to_cons[str(hits[0])] = hits[0]
            cons_to_pars[str(hits[0])].append(cell)
        else:
            print('error, cell missing continuity: ' + str(len(hits)) + ' at time: ' + str(t1) + ' for cell ' + str(cell.id))
            if not str(min_winner['winner']) in cons_to_pars.keys():
                cons_to_pars[str(min_winner['winner'])] = []
                constr_to_cons[str(min_winner['winner'])] = min_winner['winner']
            cons_to_pars[str(min_winner['winner'])].append(cell)
        #sys.exit()

            #now go back and check cons_to_pars to see if 2 or 3 situation
        for con_str in cons_to_pars.keys():
            if len(cons_to_pars[con_str]) == 1:
                cons_to_pars[con_str][0].set_frame_contour(t1, constr_to_cons[con_str])
        else:
            #begin the watershedding madness!
            assign_watershed_contours(constr_to_cons[con_str], cons_to_pars[con_str], t0, t1)



    #3) else, add contour for frame
    # OPTIMIZE - reuse previous find above for #1 if exists
    #for cell in prev_cells:
        for con in curr_cons:
            if(cv2.contourArea(con) < MIN_CELL_AREA):
                continue
            M = cv2.moments(con)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            if(cv2.pointPolygonTest(cell.get_frame_contour(t0), (cX, cY), True) > MOVEMENT_TOLERANCE):
                cell.set_frame_contour(t1, con);
                break;

    for cell in prev_cells:
        cell.gen_vis_1(t1)


#BEGIN#
if os.path.exists('./cells'):
    shutil.rmtree('./cells')
os.mkdir('./cells')
process_start_frame()
load_images()
for t in range(-1, len(frames_list) - 1):
    handle_frame_pair(t, t+1)

with open('cells.pickle', 'wb') as handle:
    pickle.dump(cells_list, handle, protocol=pickle.HIGHEST_PROTOCOL)
#for c in cells_list:
#    c.gen_visualization()
