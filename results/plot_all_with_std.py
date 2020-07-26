import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

paths = {
    'PSNR':'Experiement_object_based_all_behaviors/psnr_all_with_std.csv',
    'SSIM': 'Experiement_object_based_all_behaviors/ssim_all_with_std.csv'
}
sns.set(style="whitegrid")

plt.rcParams.update({'font.size': 16})
plt.rc('ytick', labelsize=14)
plt.rc('xtick', labelsize=14)
f, axes = plt.subplots(1, 2, figsize=(13.5,4.5))
for i, metric in enumerate(paths):
    df = pd.read_csv(paths[metric])
    if i == len(paths)-1:
        axes[1].errorbar(x=range(4, 20), y=df.use_haptic_audio_vibro_mean, yerr=df.use_haptic_audio_vibro_std,
                         marker="x", fillstyle='none',label="vision+haptic+audio+vibro", color='red')
        axes[1].errorbar(x=range(4, 20), y=df.use_haptic_audio_mean, yerr=df.use_haptic_audio_std, marker='v',
                         fillstyle='none',label="vision+haptic+audio", color='green')
        axes[1].errorbar(x=range(4, 20), y=df.use_haptic_mean, yerr=df.use_haptic_std, marker="o",
                         fillstyle='none',label="vision+haptic", color='orange')
        axes[1].errorbar(x=range(4, 20), y=df.baseline_mean, yerr=df.baseline_std, marker=8,
                         fillstyle='none',label="Finn et al.", color='blue')
        axes[i].set_ylim(0.65, 0.95)
    else:
        axes[0].errorbar(x=range(4, 20), y=df.use_haptic_audio_vibro_mean, yerr=df.use_haptic_audio_vibro_std,
                         fillstyle='none',marker="x", color='red')
        axes[0].errorbar(x=range(4, 20), y=df.use_haptic_audio_mean, yerr=df.use_haptic_audio_std,
                         marker='v', fillstyle='none',color='green')
        axes[0].errorbar(x=range(4, 20), y=df.use_haptic_mean, yerr=df.use_haptic_std,
                         marker="o",fillstyle='none', color='orange')
        axes[0].errorbar(x=range(4, 20), y=df.baseline_mean, yerr=df.baseline_std,
                         marker=8, fillstyle='none',color='blue')
        axes[i].set_ylim(22, 32)

    axes[i].set_ylabel(metric, fontsize = 16)
    axes[i].set_xlabel("Time step", fontsize = 16)
    axes[i].set_title("Heldout set reconstruction evaluation", fontsize = 18)

    # plt.xlabel("# frames")
    axes[i].xaxis.set_major_locator(ticker.MultipleLocator(2))
    if metric == 'SSIM':
        axes[i].yaxis.set_major_locator(ticker.MultipleLocator(0.05))
    else:
        axes[i].yaxis.set_major_locator(ticker.MultipleLocator(2))

# plt.subplots_adjust(wspace=0.45)
plt.legend(fontsize=12)

plt.tight_layout()
plt.savefig('all_with_std.png', dpi=300)
plt.show()