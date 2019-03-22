# -*- coding: utf-8 -*-
"""
Created on Sun Nov 28 11:33:30 2018

@author: Diego Wanderley
@python: 3.6
@description: U-net modules and network
"""

from __future__ import print_function
import torch
import torch.nn as nn
import torch.nn.functional as F


class inconv(nn.Module):
    '''
    Input layer
    '''
    def __init__(self, in_ch, out_ch, batch_norm=True, dropout=0):
        ''' Constructor '''
        super(inconv, self).__init__()
        # Set conv layer
        self.conv = nn.Sequential()
        self.conv.add_module("conv_1", nn.Conv2d(in_ch, out_ch, 3, stride=1, padding=1))
        if batch_norm:
            self.conv.add_module("bnorm_1", nn.BatchNorm2d(out_ch))
        if dropout > 0:
            self.conv.add_module("dropout_1", nn.Dropout2d(dropout))
        self.conv.add_module("relu_1", nn.ReLU(inplace=True))

    def forward(self, x):
        ''' Foward method '''
        x = self.conv(x)
        return x

class fwdconv(nn.Module):
    '''
    Foward convolution layer
    '''
    def __init__(self, in_ch, out_ch, batch_norm=True, dropout=0):
        ''' Constructor '''
        super(fwdconv, self).__init__()
        # Set conv layer
        self.conv = nn.Sequential()
        self.conv.add_module("conv_1", nn.Conv2d(in_ch, out_ch, 3, stride=1, padding=1))
        if batch_norm:
            self.conv.add_module("bnorm_1", nn.BatchNorm2d(out_ch))
        if dropout > 0:
            self.conv.add_module("dropout_1", nn.Dropout2d(dropout))
        self.conv.add_module("relu_1", nn.ReLU(inplace=True))

    def forward(self, x):
        ''' Foward method '''
        x = self.conv(x)
        return x

class downconv(nn.Module):
    '''
    Downconvolution layer
    '''
    def __init__(self, in_ch, out_ch, batch_norm=True, dropout=0):
        ''' Constructor '''
        super(downconv, self).__init__()
        # Set conv layer
        self.conv = nn.Sequential()
        self.conv.add_module("conv_1", nn.Conv2d(in_ch, out_ch, 3, stride=2, padding=1))
        if batch_norm:
            self.conv.add_module("bnorm_1",nn.BatchNorm2d(out_ch))
        if dropout > 0:
            self.conv.add_module("dropout_1", nn.Dropout2d(dropout))
        self.conv.add_module("relu_1",nn.ReLU(inplace=True))

    def forward(self, x):
        ''' Foward method '''
        x = self.conv(x)
        return x

class upconv(nn.Module):
    '''
    Upconvolution layer
    '''
    def __init__(self, in_ch, out_ch, res_ch=0, bilinear=False, batch_norm=True, dropout=0):
        ''' Constructor '''
        super(upconv, self).__init__()
        # Check interpolation
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        else:
            self.up = nn.ConvTranspose2d(in_ch, in_ch, 2, stride=2)
        # Set conv layer
        self.conv = nn.Sequential()
        self.conv.add_module("fwdconv_1", fwdconv(in_ch+res_ch, out_ch, batch_norm=True, dropout=0))
        self.conv.add_module("fwdconv_2", fwdconv(out_ch, out_ch))

    def forward(self, x, x_res=None):
        ''' Foward method '''
        x_up = self.up(x)

        if x_res is None:
            x_cat = x_up
        else:
            x_cat = torch.cat((x_up, x_res), 1)

        x_conv = self.conv(x_cat)

        return x_conv

class outconv(nn.Module):
    '''
    Output convolution layer
    '''
    def __init__(self, in_ch, out_ch, batch_norm=True, dropout=0):
        ''' Constructor '''
        super(outconv, self).__init__()
        # Set conv layer
        self.conv = nn.Sequential()
        self.conv.add_module("conv_1", nn.Conv2d(in_ch, out_ch, 1, stride=1, padding=0))
        if batch_norm:
            self.conv.add_module("bnorm_1",nn.BatchNorm2d(out_ch))
        if dropout > 0:
            self.conv.add_module("dropout_1", nn.Dropout2d(dropout))
        self.conv.add_module("relu_1",nn.ReLU(inplace=True))
              

    def forward(self, x):
        ''' Foward method '''
        x = self.conv(x)
        return x


class Unet(nn.Module):
    '''
    U-net class
    '''
    def __init__(self, n_channels, n_classes):
        ''' Constructor '''
        super(Unet, self).__init__()
        # Number of classes definition
        self.n_classes = n_classes

        # Set input layer
        self.conv_init  = inconv(n_channels, 8)

        # Set downconvolution layer 1
        self.conv_down1 = downconv(8, 8, dropout=0.2)
        # Set downconvolution layer 2
        self.conv_down2 = downconv(8, 16, dropout=0.2)
        # Set downconvolution layer 3
        self.conv_down3 = downconv(16, 24, dropout=0.2)
        # Set downconvolution layer 4
        self.conv_down4 = downconv(24, 32, dropout=0.2)
        # Set downconvolution layer 5
        self.conv_down5 = downconv(32, 40, dropout=0.2)
        # Set downconvolution layer 6
        self.conv_down6 = downconv(40, 48, dropout=0.2)

        # Set upconvolution layer 1
        self.conv_up1 = upconv(48, 320, res_ch=40, dropout=0.2)
        # Set upconvolution layer 2
        self.conv_up2 = upconv(320, 256, res_ch=32, dropout=0.2)
        # Set upconvolution layer 3
        self.conv_up3 = upconv(256, 192, res_ch=24, dropout=0.2)
        # Set upconvolution layer 4
        self.conv_up4 = upconv(192, 128, res_ch=16, dropout=0.2)
        # Set upconvolution layer 5
        self.conv_up5 = upconv(128, 64, res_ch=8, dropout=0.2)
        # Set upconvolution layer 6
        self.conv_up6 = upconv(64, 8, res_ch=8, dropout=0.2)

        # Output
        self.conv_out = outconv(8, n_classes)

    def forward(self, x):
        ''' Foward method '''
         # input
        c_x0 = self.conv_init(x)
        # downstream
        dc_x1 = self.conv_down1(c_x0)
        dc_x2 = self.conv_down2(dc_x1)
        dc_x3 = self.conv_down3(dc_x2)
        dc_x4 = self.conv_down4(dc_x3)
        dc_x5 = self.conv_down5(dc_x4)
        dc_x6 = self.conv_down6(dc_x5)
        # upstream
        uc_x1 = self.conv_up1(dc_x6, dc_x5)
        uc_x2 = self.conv_up2(uc_x1, dc_x4)
        uc_x3 = self.conv_up3(uc_x2, dc_x3)
        uc_x4 = self.conv_up4(uc_x3, dc_x2)
        uc_x5 = self.conv_up5(uc_x4, dc_x1)
        uc_x6 = self.conv_up6(uc_x5, c_x0)
        # output
        x = self.conv_out(uc_x6)
        return x


class Unet2(nn.Module):
    '''
    U-net class from end-to-end ovarian structures segmentation
    '''
    def __init__(self, n_channels, n_classes):
        ''' Constructor '''
        super(Unet2, self).__init__()

        # Number of classes definition
        self.n_classes = n_classes

        # Set input layer
        self.conv_init  = inconv(n_channels, 8)

        # Set downconvolution layer 1
        self.conv_down1 = downconv(8, 8, dropout=0.2)
        # Set downconvolution layer 2
        self.conv_down2 = downconv(8, 16, dropout=0.2)
        # Set downconvolution layer 3
        self.conv_down3 = downconv(16, 24, dropout=0.2)
        # Set downconvolution layer 4
        self.conv_down4 = downconv(24, 32, dropout=0.2)
        # Set downconvolution layer 5
        self.conv_down5 = downconv(32, 40, dropout=0.2)
        # Set downconvolution layer 6
        self.conv_down6 = downconv(40, 48, dropout=0.2)

        # Set upconvolution layer 1
        self.conv_up1 = upconv(48, 320, res_ch=40, dropout=0.2)
        # Set upconvolution layer 2
        self.conv_up2 = upconv(320, 256, res_ch=32, dropout=0.2)
        # Set upconvolution layer 3
        self.conv_up3 = upconv(256, 192, res_ch=24, dropout=0.2)
        # Set upconvolution layer 4
        self.conv_up4 = upconv(192, 128, res_ch=16, dropout=0.2)
        # Set upconvolution layer 5
        self.conv_up5 = upconv(128, 64, res_ch=8, dropout=0.2)
        # Set upconvolution layer 6
        self.conv_up6 = upconv(64, 8, res_ch=8, dropout=0.2)

        # Set output layer
        if type(n_classes) is list:
            self.conv_out = nn.ModuleList() # necessary for GPU convertion
            for n in n_classes:
                c_out = outconv(8, n)
                self.conv_out.append(c_out)
        else:
            self.conv_out = outconv(8, n_classes)
        # Define Softmax
        self.softmax = nn.Softmax2d()

    def forward(self, x):
        ''' Foward method '''

        # input
        c_x0 = self.conv_init(x)
        # downstream
        dc_x1 = self.conv_down1(c_x0)
        dc_x2 = self.conv_down2(dc_x1)
        dc_x3 = self.conv_down3(dc_x2)
        dc_x4 = self.conv_down4(dc_x3)
        dc_x5 = self.conv_down5(dc_x4)
        dc_x6 = self.conv_down6(dc_x5)
        # upstream
        uc_x1 = self.conv_up1(dc_x6, dc_x5)
        uc_x2 = self.conv_up2(uc_x1, dc_x4)
        uc_x3 = self.conv_up3(uc_x2, dc_x3)
        uc_x4 = self.conv_up4(uc_x3, dc_x2)
        uc_x5 = self.conv_up5(uc_x4, dc_x1)
        uc_x6 = self.conv_up6(uc_x5, c_x0)
        # output
        if type(self.n_classes) is list:
            x_out = []
            for c_out in self.conv_out:
                x = c_out(uc_x6)
                x_out.append(self.softmax(x))
        else:
            x = self.conv_out(uc_x6)
            x_out = self.softmax(x)             

        return x_out


class InstSegNet(nn.Module):

    def __init__(self, n_channels, n_features):
        ''' Constructor '''
        super(InstSegNet, self).__init__()

        # Number of classes definition
        self.n_features = n_features
        # Unet
        self.body = Unet(n_channels, 8)
        # Output
        self.conv_out = outconv(8, n_features)

    def forward(self, x):
        ''' Foward method '''

        # Unet
        x_1 = self.body(x)
        # Output
        x_out = self.conv_out(x_1)

        return x_out