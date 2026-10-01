"""
Arquitetura do modelo Mix Vision Transformer para segmentação de BAC
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class OverlapPatchEmbed(nn.Module):
    """Overlapping patch merging"""
    def __init__(self, patch_size=7, stride=4, in_chans=1, embed_dim=64):
        super().__init__()
        self.proj = nn.Conv2d(
            in_chans, embed_dim,
            kernel_size=patch_size,
            stride=stride,
            padding=patch_size // 2
        )
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x):
        x = self.proj(x)
        _, _, H, W = x.shape
        x = x.flatten(2).transpose(1, 2)
        x = self.norm(x)
        return x, H, W


class Attention(nn.Module):
    """Efficient self-attention com spatial reduction"""
    def __init__(self, dim, num_heads=8, sr_ratio=1):
        super().__init__()
        self.num_heads = num_heads
        self.scale = (dim // num_heads) ** -0.5
        
        self.q = nn.Linear(dim, dim)
        self.kv = nn.Linear(dim, dim * 2)
        self.proj = nn.Linear(dim, dim)
        
        self.sr_ratio = sr_ratio
        if sr_ratio > 1:
            self.sr = nn.Conv2d(dim, dim, kernel_size=sr_ratio, stride=sr_ratio)
            self.norm = nn.LayerNorm(dim)

    def forward(self, x, H, W):
        B, N, C = x.shape
        q = self.q(x).reshape(B, N, self.num_heads, C // self.num_heads).permute(0, 2, 1, 3)
        
        if self.sr_ratio > 1:
            x_ = x.permute(0, 2, 1).reshape(B, C, H, W)
            x_ = self.sr(x_).reshape(B, C, -1).permute(0, 2, 1)
            x_ = self.norm(x_)
            kv = self.kv(x_).reshape(B, -1, 2, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        else:
            kv = self.kv(x).reshape(B, -1, 2, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        
        k, v = kv[0], kv[1]
        
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        return x


class MixFFN(nn.Module):
    """Feed-forward com depth-wise convolution"""
    def __init__(self, dim, mlp_ratio=4):
        super().__init__()
        hidden_dim = int(dim * mlp_ratio)
        self.fc1 = nn.Linear(dim, hidden_dim)
        self.dwconv = nn.Conv2d(hidden_dim, hidden_dim, 3, 1, 1, groups=hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, dim)

    def forward(self, x, H, W):
        x = self.fc1(x)
        B, N, C = x.shape
        x = x.permute(0, 2, 1).reshape(B, C, H, W)
        x = self.dwconv(x)
        x = x.flatten(2).transpose(1, 2)
        x = F.gelu(x)
        x = self.fc2(x)
        return x


class Block(nn.Module):
    """Bloco Transformer"""
    def __init__(self, dim, num_heads, mlp_ratio=4, sr_ratio=1):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = Attention(dim, num_heads, sr_ratio)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = MixFFN(dim, mlp_ratio)

    def forward(self, x, H, W):
        x = x + self.attn(self.norm1(x), H, W)
        x = x + self.mlp(self.norm2(x), H, W)
        return x


class MixVisionTransformer(nn.Module):
    """Encoder hierárquico"""
    def __init__(self, config):
        super().__init__()
        embed_dims = config['embed_dims']
        num_heads = config['num_heads']
        mlp_ratios = config['mlp_ratios']
        depths = config['depths']
        sr_ratios = config['sr_ratios']
        
        # Patch embeddings
        self.patch_embed1 = OverlapPatchEmbed(7, 4, 1, embed_dims[0])
        self.patch_embed2 = OverlapPatchEmbed(3, 2, embed_dims[0], embed_dims[1])
        self.patch_embed3 = OverlapPatchEmbed(3, 2, embed_dims[1], embed_dims[2])
        self.patch_embed4 = OverlapPatchEmbed(3, 2, embed_dims[2], embed_dims[3])
        
        # Transformer blocks
        self.block1 = nn.ModuleList([Block(embed_dims[0], num_heads[0], mlp_ratios[0], sr_ratios[0]) 
                                      for _ in range(depths[0])])
        self.block2 = nn.ModuleList([Block(embed_dims[1], num_heads[1], mlp_ratios[1], sr_ratios[1]) 
                                      for _ in range(depths[1])])
        self.block3 = nn.ModuleList([Block(embed_dims[2], num_heads[2], mlp_ratios[2], sr_ratios[2]) 
                                      for _ in range(depths[2])])
        self.block4 = nn.ModuleList([Block(embed_dims[3], num_heads[3], mlp_ratios[3], sr_ratios[3]) 
                                      for _ in range(depths[3])])
        
        self.norm1 = nn.LayerNorm(embed_dims[0])
        self.norm2 = nn.LayerNorm(embed_dims[1])
        self.norm3 = nn.LayerNorm(embed_dims[2])
        self.norm4 = nn.LayerNorm(embed_dims[3])

    def forward(self, x):
        B = x.shape[0]
        outs = []
        
        # Stage 1
        x, H, W = self.patch_embed1(x)
        for blk in self.block1:
            x = blk(x, H, W)
        x = self.norm1(x).reshape(B, H, W, -1).permute(0, 3, 1, 2)
        outs.append(x)
        
        # Stage 2
        x, H, W = self.patch_embed2(x)
        for blk in self.block2:
            x = blk(x, H, W)
        x = self.norm2(x).reshape(B, H, W, -1).permute(0, 3, 1, 2)
        outs.append(x)
        
        # Stage 3
        x, H, W = self.patch_embed3(x)
        for blk in self.block3:
            x = blk(x, H, W)
        x = self.norm3(x).reshape(B, H, W, -1).permute(0, 3, 1, 2)
        outs.append(x)
        
        # Stage 4
        x, H, W = self.patch_embed4(x)
        for blk in self.block4:
            x = blk(x, H, W)
        x = self.norm4(x).reshape(B, H, W, -1).permute(0, 3, 1, 2)
        outs.append(x)
        
        return outs


class MLPDecoder(nn.Module):
    """Decoder MLP"""
    def __init__(self, in_channels=[64, 128, 320, 512], num_classes=1):
        super().__init__()
        self.linear_c4 = nn.Linear(in_channels[3], 256)
        self.linear_c3 = nn.Linear(in_channels[2], 256)
        self.linear_c2 = nn.Linear(in_channels[1], 256)
        self.linear_c1 = nn.Linear(in_channels[0], 256)
        self.linear_fuse = nn.Conv2d(256 * 4, 256, 1)
        self.classifier = nn.Conv2d(256, num_classes, 1)

    def forward(self, inputs):
        c1, c2, c3, c4 = inputs
        n, _, h, w = c4.shape
        
        _c4 = self.linear_c4(c4.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        _c4 = F.interpolate(_c4, size=(h*8, w*8), mode='bilinear', align_corners=False)
        
        _c3 = self.linear_c3(c3.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        _c3 = F.interpolate(_c3, size=(h*8, w*8), mode='bilinear', align_corners=False)
        
        _c2 = self.linear_c2(c2.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        _c2 = F.interpolate(_c2, size=(h*8, w*8), mode='bilinear', align_corners=False)
        
        _c1 = self.linear_c1(c1.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)
        _c1 = F.interpolate(_c1, size=(h*8, w*8), mode='bilinear', align_corners=False)
        
        _c = torch.cat([_c4, _c3, _c2, _c1], dim=1)
        _c = self.linear_fuse(_c)
        x = self.classifier(_c)
        x = F.interpolate(x, size=(1024, 1024), mode='bilinear', align_corners=False)
        
        return x


class BACSegmentationModel(nn.Module):
    """Modelo completo"""
    def __init__(self, config):
        super().__init__()
        self.encoder = MixVisionTransformer(config)
        self.decoder = MLPDecoder(in_channels=config['embed_dims'])
    
    def forward(self, x):
        features = self.encoder(x)
        mask = self.decoder(features)
        return torch.sigmoid(mask)