import numpy as np
import torch
from torch.autograd import Variable
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from glob import glob
import imageio
import torch.backends.cudnn as cudnn
from modules.vgg import vgg16, vgg16_bn,VGG_spread, vgg19, vgg19_bn
from modules.resnet import resnet50, resnet101, resnet18
import matplotlib.cm
from matplotlib.cm import ScalarMappable
import matplotlib.pyplot as plt
import cv2
from torchsummary import summary
from imagenet_index import index2class
from LRP_util import *
import os



# define data loader

###########################################################################################################################
model_arch = 'resnet'

if model_arch == 'vgg':
    model = vgg16_bn(pretrained=True).cuda().eval()  #####
    target_layer = model.features[43]
elif model_arch == 'resnet':
    model = resnet50(pretrained=True).cuda().eval() #####
    target_layer = model.layer2

layer_path = 'layer2'
###########################################################################################################################

CAM_CLASS = GradCAM_multi(model, target_layer)
Score_CAM_class = ScoreCAM(model,target_layer)

img_path_long = './picture/cat3.jpg'
img = cv2.imread(img_path_long,1)
img_show = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_show = cv2.resize(img_show,(224,224))
img = np.float32(cv2.resize(img, (224, 224)))/255

in_tensor = preprocess_image(img).cuda()
output = model(in_tensor)

maxindex = np.argmax(output.data.cpu().numpy())

print(index2class[maxindex])
save_path = './results/{}_{}'.format(index2class[maxindex][:10], img_path_long.split('/')[-1])

Tt, Tn = CLRP(output, maxindex)
posi_R = model.relprop(Tt,1,flag=layer_path).data.cpu().numpy()
nega_R = model.relprop(Tn,1,flag=layer_path).data.cpu().numpy()

R = posi_R - nega_R
R = np.transpose(R[0],(1,2,0))
r_weight = np.sum(R,axis=(0,1),keepdims=True)
activation, grad_cam, grad_campp = CAM_CLASS(in_tensor)

score_map, _ = Score_CAM_class(in_tensor, class_idx=maxindex)
score_map = score_map.squeeze()
score_map = score_map.detach().cpu().numpy()
R_CAM = cv2.resize(np.sum(activation * r_weight, axis=-1),(224,224))


a = cv2.resize(np.sum(activation,axis=-1),(224,224))


fig = plt.figure(figsize=(10, 10))
plt.subplots_adjust(bottom=0.01)

plt.subplot(2, 5, 1)
plt.imshow(img_show)
plt.title('Original')
plt.axis('off')

plt.subplot(2, 5, 1 + 5)
plt.imshow(img_show)
plt.axis('off')

plt.subplot(2, 5, 2)
plt.imshow((grad_cam),cmap='seismic')
plt.imshow(img_show, alpha=.5)
plt.title('Grad CAM')
plt.axis('off')

plt.subplot(2, 5, 2 + 5)
plt.imshow((grad_cam),cmap='seismic')
plt.axis('off')

plt.subplot(2, 5, 3)
plt.imshow((grad_campp),cmap='seismic')
plt.imshow(img_show, alpha=.5)
plt.title('Grad CAM++', fontsize=15)
plt.axis('off')

plt.subplot(2, 5, 3 + 5)
plt.imshow((grad_campp),cmap='seismic')
plt.axis('off')

plt.subplot(2, 5, 4)
plt.imshow((score_map),cmap='seismic')
plt.imshow(img_show, alpha=.5)
plt.title('Score_CAM', fontsize=15)
plt.axis('off')

plt.subplot(2, 5, 4 + 5)
plt.imshow((score_map),cmap='seismic')
plt.axis('off')

plt.subplot(2, 5, 5)
plt.imshow((R_CAM),cmap='seismic')
plt.imshow(img_show, alpha=.5)
plt.title('Relevance_CAM', fontsize=15)
plt.axis('off')

plt.subplot(2, 5, 5 + 5)
plt.imshow((R_CAM),cmap='seismic')
plt.axis('off')

plt.tight_layout()
plt.draw()
plt.waitforbuttonpress()
plt.savefig(save_path)
plt.clf()
plt.close()

print('Done')