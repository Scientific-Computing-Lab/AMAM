## Metallography-Oriented Deep Models (15)

| Rank | Model | Category | mIoU | Dice | Pixel Acc | Params (M) | Train min |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Metal-U-Net++ CLAHE (EfficientNet-B0) | micrograph-contrast | 0.5796 | 0.6962 | 0.8126 | 6.07 | 0.1 |
| 2 | Metal-MAnet RGB+Sobel (EfficientNet-B0) | edge-aware | 0.5782 | 0.6937 | 0.8079 | 8.67 | 0.1 |
| 3 | Metal-U-Net Gabor Stack (ResNet34) | texture-aware | 0.5410 | 0.6601 | 0.7543 | 24.44 | 0.2 |
| 4 | Metal-DeepLabV3+ CLAHE (ResNet34) | micrograph-contrast | 0.5320 | 0.6524 | 0.7795 | 22.44 | 0.1 |
| 5 | Metal-SegFormer Gray (MiT-B2) | micrograph-contrast | 0.5185 | 0.6303 | 0.7555 | 24.72 | 0.1 |
| 6 | Metal-U-Net CLAHE (ResNet34) | micrograph-contrast | 0.5165 | 0.6376 | 0.7716 | 24.44 | 0.1 |
| 7 | Metal-U-Net Gray (ResNet34) | micrograph-contrast | 0.5102 | 0.6378 | 0.7099 | 24.43 | 0.1 |
| 8 | Metal-SegFormer CLAHE (MiT-B0) | micrograph-contrast | 0.5008 | 0.6192 | 0.7473 | 3.72 | 0.1 |
| 9 | Metal-UPerNet CLAHE (MiT-B2) | micrograph-contrast | 0.4939 | 0.6082 | 0.7533 | 32.53 | 0.1 |
| 10 | Metal-U-Net RGB+Sobel (ResNet34) | edge-aware | 0.4918 | 0.6147 | 0.7020 | 24.44 | 0.1 |
| 11 | Metal-LinkNet RGB+Sobel (ResNet34) | edge-aware | 0.4891 | 0.5964 | 0.7467 | 21.78 | 0.1 |
| 12 | Metal-U-Net++ Gray (ResNet34) | micrograph-contrast | 0.4727 | 0.5826 | 0.7298 | 26.07 | 0.2 |
| 13 | Metal-U-Net LBP Stack (ResNet34) | texture-aware | 0.4674 | 0.5775 | 0.6990 | 24.44 | 0.1 |
| 14 | Metal-FPN Gabor Stack (ResNet34) | texture-aware | 0.4577 | 0.5811 | 0.6880 | 23.16 | 0.1 |
| 15 | MLography U-Net (2022-style) | metallography-original | 0.4322 | 0.5548 | 0.6800 | 23.75 | 0.2 |