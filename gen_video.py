import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from PIL import Image
import os
import collections
from scipy.io import loadmat
import matplotlib.animation as animation
from mpl_toolkits import mplot3d
from scipy import misc
import datetime
from scipy.spatial import ConvexHull
from scipy.stats import multivariate_normal
from matplotlib.patches import Polygon
from scipy.spatial import HalfspaceIntersection
from scipy.spatial import ConvexHull
import scipy as sp
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as a3
import matplotlib.colors as colors
import random
from matplotlib.pyplot import figure, draw, pause
import glob as glob
import cv2
import shutil
# imgs is a N x X x Y image stack

CELL_CNT = 0

def simg(img):

    plt.ion()
    plt.imshow(img, cmap="gray")
    plt.show()
    a = input("Press Enter to continue...")
    #print (a)
    if(a == "x"):
        sys.exit()

def gen_filtered_video():
    if os.path.exists('./02_filtered'):
        shutil.rmtree('./02_filtered')
    os.mkdir('./02_filtered')
    '''
        sys.exit()
    '''
    ans = []
    for g in glob.glob('./02/*'):
        img = g
        img = cv2.imread(img)
        #h = ax.imshow(img, cmap='gray')
        #draw()
        #pause(.001)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        (T, thresh) = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)
        cv2.imwrite('./02_filtered/'+os.path.basename(g), thresh)

    os.chdir('./02_filtered/')
    os.system('convert *.tif filtered.mov')

gen_filtered_video()
