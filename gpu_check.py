import sys, platform

print('python:', sys.version)
print('platform:', platform.platform())

try:
    import torch
    print('torch:', torch.__version__)
    print('torch.cuda_available:', torch.cuda.is_available())
    print('torch.cuda_version:', getattr(torch.version, 'cuda', None))
    print('torch.device_count:', torch.cuda.device_count())
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        try:
            print('torch.device_name0:', torch.cuda.get_device_name(0))
        except Exception as e:
            print('torch.device_name0_err:', e)
except Exception as e:
    print('torch_err:', e)

try:
    import tensorflow as tf
    print('tf:', tf.__version__)
    gpus = tf.config.list_physical_devices('GPU')
    print('tf.gpus:', gpus)
except Exception as e:
    print('tf_err:', e)

