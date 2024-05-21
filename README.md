1. Set up conda environment via
```
conda env create --file env.yaml
```
2. Download the raindrop image from Onedrive and place it under the directory './icdar2015_rain'. It consists of at least two folders: 'ch4_test_images' and 'ch4_test_images_gt'
3. Download pre-trained checkpoint for ICDAR 2015 dataset: [LINK](https://drive.google.com/file/d/1i2R7UIUqmkUtF0jv_3MXTqmQ_9wuAnLf/view)
4. Running command for inference is as below. If the argument --de-rain is prepended, the image is processed by the de-rain module before the text detection module is running.  
```
python eval.py --trained_model=./craft_ic15_20k.pth --test_folder=./icdar2015_rain [--derain]
```
ToDo
- [ ] Training code: we need to clarify which ablation studies will be conducted.
