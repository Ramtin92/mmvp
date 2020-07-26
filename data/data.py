import os
import torch
from torchvision import transforms
from torch.utils.data import DataLoader, Dataset
import torch.nn.functional as F
import numpy as np

IMG_EXTENSIONS = ('.npy',)
AUDIO_LENGTH = 16
AUDIO_HEIGHT = 128
HAPTIC_MAX = [-10.478915, 1.017272, 6.426756, 5.950242, 0.75426, -0.013009, 0.034224]
HAPTIC_MIN = [-39.090578, -21.720063, -10.159031, -4.562487, -1.456323, -1.893409, -0.080752]
# we do not normalize the cpos (gripper pose, end effector)
HAPTIC_MEAN = [-25.03760727, -8.2802204, -5.49065186, 2.53891808, -0.6424120, -1.22525292, -0.04463354, 0.0, 0.0, 0.0]
HAPTIC_STD = [4.01142790e+01, 2.29780167e+01, 2.63156072e+01, 7.54091499e+00, 3.40810983e-01, 3.23891355e-01, 1.65208189e-03, 1.0, 1.0, 1.0]

VIBRO_MEAN = [55.32553454, -141.92273532, -26.08607739]
VIBRO_STD = [109.59627816, 133.72501765, 163.39785803]


def make_dataset(path):
    if not os.path.exists(path):
        raise FileExistsError('some subfolders from data set do not exists!')

    samples = []
    for sample in os.listdir(path):
        image = os.path.join(path, sample)
        samples.append(image)
    return samples


def npy_loader(path):
    samples = np.load(path, allow_pickle=True).item()
    samples['vision'] = torch.from_numpy(samples['vision'])
    samples['haptic'] = torch.from_numpy(samples['haptic']).float()
    samples['audio'] = torch.from_numpy(samples['audio'])
    samples['behavior'] = torch.from_numpy(samples['behavior']).float()
    samples['vibro'] = torch.from_numpy(samples['vibro'])
    return samples


class PushDataset(Dataset):
    def __init__(self, root, image_transform=None, action_transform=None, state_transform=None, loader=npy_loader, device='cpu'):
        if not os.path.exists(root):
            raise FileExistsError('{0} does not exists!'.format(root))
        # self.subfolders = [f[0] for f in os.walk(root)][1:]
        self.image_transform = image_transform
        self.action_transform = action_transform
        self.state_transform = state_transform
        self.samples = make_dataset(root)
        if len(self.samples) == 0:
            raise (RuntimeError("Found 0 images in subfolders of: " + root + "\n"
                                                                             "Supported image extensions are: " + ",".join(
                IMG_EXTENSIONS)))
        self.loader = loader
        self.device = device

    def __getitem__(self, index):
        image, action, state, behaivor = self.samples[index]
        image, action, state, behaivor = self.loader(image), self.loader(action), self.loader(state), self.loader(behaivor)

        if self.image_transform is not None:
            image = torch.cat([self.image_transform(single_image).unsqueeze(0) for single_image in image.unbind(0)], dim=0)
        if self.action_transform is not None:
            action = torch.cat([self.action_transform(single_action).unsqueeze(0) for single_action in action.unbind(0)], dim=0)
        if self.state_transform is not None:
            state = torch.cat([self.state_transform(single_state).unsqueeze(0) for single_state in state.unbind(0)], dim=0)

        return image.to(self.device), action.to(self.device), state.to(self.device)

    def __len__(self):
        return len(self.samples)


class CY101Dataset(Dataset):
    def __init__(self, root, image_transform=None, haptic_transform=None, audio_transform=None, vibro_transform=None, loader=npy_loader, device='cpu'):
        if not os.path.exists(root):
            raise FileExistsError('{0} does not exists!'.format(root))

        self.image_transform = lambda vision: torch.cat([image_transform(single_image).unsqueeze(0) for single_image in vision.unbind(0)], dim=0)
        self.haptic_transform = lambda haptic: torch.cat([haptic_transform(single_haptic).unsqueeze(0) for single_haptic in haptic.unbind(0)], dim=0)
        self.audio_transform = lambda audio: torch.cat([audio_transform(single_audio).unsqueeze(0) for single_audio in audio.unbind(0)], dim=0)
        self.vibro_transform = lambda vibro: torch.cat([vibro_transform(single_vibro).unsqueeze(0) for single_vibro in vibro.unbind(0)], dim=0)

        self.samples = make_dataset(root)
        if len(self.samples) == 0:
            raise (RuntimeError("Found 0 images in subfolders of: " + root + "\n"
                                "Supported image extensions are: " + ",".join(IMG_EXTENSIONS)))
        self.loader = loader
        self.device = device

    def __getitem__(self, index):
        modalities = self.loader(self.samples[index])
        vision = modalities['vision']
        haptic = modalities['haptic']
        audio = modalities['audio']
        behavior = modalities['behavior']
        vibro = modalities['vibro']
        if self.image_transform is not None:
            vision = self.image_transform(vision)
            # vision = torch.cat([self.image_transform(single_image).unsqueeze(0) for single_image in vision.unbind(0)], dim=0)
        if self.haptic_transform is not None:
            haptic = self.haptic_transform(haptic)
            # haptic = torch.cat([self.haptic_transform(single_haptic).unsqueeze(0) for single_haptic in haptic.unbind(0)], dim=0)
        if self.audio_transform is not None:
            audio = self.audio_transform(audio)
            # audio = torch.cat([self.audio_transform(single_audio).unsqueeze(0) for single_audio in audio.unbind(0)], dim=0)
        if self.vibro_transform is not None:
            vibro = self.vibro_transform(vibro)
            # vibro = torch.cat([self.vibro_transform(single_vibro).unsqueeze(0) for single_vibro in vibro.unbind(0)], dim=0)
        return vision.to(self.device), haptic.to(self.device), audio.to(self.device), behavior.to(self.device), vibro.to(self.device)

    def __len__(self):
        return len(self.samples)


def build_dataloader_CY101(opt):
    def crop(im):
        height, width = im.shape[1:]
        width = max(height, width)
        im = im[:, :width, :width]
        return im

    def padding(au):
        length = au.shape[1]
        if length < AUDIO_LENGTH:
            au = F.pad(au, (0, 0, 0, AUDIO_LENGTH-length), mode='constant', value=0)
        au = au[:, :AUDIO_LENGTH,:]
        return au

    class Standardizer:
        def __init__(self, mean, std):
            if not isinstance(mean, torch.Tensor) and not isinstance(std, torch.Tensor):
                raise TypeError("Expecte mean and std to be  torch.Tensor")
            self.mean = mean
            self.std = std
            self.std.to(opt.device)
            self.mean.to(opt.device)

        def __call__(self, hp):
            return (hp-self.mean)/self.std

    def addnoise_au(au):
        au = au + torch.rand_like(au, device=au.device)*10
        au[au>255]=255
        au[au<0]=0
        return au

    def addnoise_hp(hp):
        hp = hp + torch.rand_like(hp, device=hp.device)
        return hp

    image_transform = transforms.Compose([
        transforms.Lambda(crop),
        transforms.ToPILImage(),
        transforms.Resize((opt.height, opt.width)),
        transforms.ToTensor()
    ])

    audio_transform = transforms.Compose([
        transforms.Lambda(lambda x:x.byte()),
        transforms.ToPILImage(),
        transforms.Resize((AUDIO_LENGTH, AUDIO_HEIGHT)),
        transforms.ToTensor()
    ])

    haptic_transform = transforms.Compose([
        transforms.Lambda(Standardizer(mean=torch.Tensor(HAPTIC_MEAN),
                                       std=torch.Tensor(HAPTIC_STD))),
        transforms.Lambda(addnoise_hp)
    ])

    vibro_transform = transforms.Compose([
        transforms.Lambda(Standardizer(mean=torch.Tensor(VIBRO_MEAN),
                                        std=torch.Tensor(VIBRO_STD))),
    ])

    train_ds = CY101Dataset(
        root=os.path.join(opt.data_dir+'/train'),
        image_transform=image_transform,
        audio_transform=audio_transform,
        haptic_transform=haptic_transform,
        vibro_transform=vibro_transform,
        loader=npy_loader,
        device=opt.device
    )

    valid_ds = CY101Dataset(
        root=os.path.join(opt.data_dir+'/test'),
        image_transform=image_transform,
        audio_transform=audio_transform,
        haptic_transform=haptic_transform,
        vibro_transform=vibro_transform,
        loader=npy_loader,
        device=opt.device
    )

    train_dl = DataLoader(dataset=train_ds, batch_size=opt.batch_size, shuffle=True, drop_last=False)
    valid_dl = DataLoader(dataset=valid_ds, batch_size=opt.batch_size, shuffle=False, drop_last=False)
    return train_dl, valid_dl

if __name__ == '__main__':
    from options import Options
    opt = Options().parse()
    opt.data_dir = '../'+opt.data_dir
    tr, va = build_dataloader_CY101(opt)
    import cv2
    for a, b, c, d, e in tr:
        imgs = c[0].unbind(0)
        imgs = list(map(lambda x:(x.permute([1, 2, 0]).cpu().numpy()*255).squeeze().astype(np.uint8), imgs))
        for img in imgs:
            cv2.imwrite('l.png', img[20])


