"""
EDA in Simulators mainly handles the visualisation for
"""

from Config import Config
from usr_func.checkfolder import checkfolder
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
from matplotlib.gridspec import GridSpec
from joblib import Parallel, delayed

filepath = "./npy/analytical/"
figpath = os.getcwd() + "/../../../../OneDrive - NTNU/MASCOT_PhD/Projects/GOOGLE/Docs/fig/Sim_2DNidelva/Simulator/"

c = Config()
plg_b = c.get_polygon_border()
plg_o = c.get_polygon_obstacle()
num_steps = c.get_num_steps()
num_replicates = c.get_num_replicates()

smyopic = "SimulatorMyopic2D"
srrt = "SimulatorRRTStar"

sigmas_nuggets = np.array([[1., .25],
                           [1., .1],
                           [1.5, .25],
                           [1.5, .1],
                           [.5, .25],
                           [.5, .1],
                           [.1, .1],
                           [.1, .01]])

replicates = os.listdir(filepath)
Nrep = 0
for rep in replicates:
    if rep.startswith("R_"):
        Nrep += 1
print("Number of replicates: ", Nrep)

traj = None
ibv = None
rmse = None
vr = None

def load_data4simulator(string):
    traj = np.empty([0, 3, num_steps, 2])
    ibv = np.empty([0, 3, num_steps])
    rmse = np.empty([0, 3, num_steps])
    vr = np.empty([0, 3, num_steps])

    for i in range(Nrep):
        rep = "R_{:03d}".format(i)

        datapath = filepath + rep + string
        r_traj = np.load(datapath + "traj.npy").reshape(1, 3, num_steps, 2)
        r_ibv = np.load(datapath + "ibv.npy").reshape(1, 3, num_steps)
        r_vr = np.load(datapath + "vr.npy").reshape(1, 3, num_steps)
        r_rmse = np.load(datapath + "rmse.npy").reshape(1, 3, num_steps)

        traj = np.append(traj, r_traj, axis=0)
        ibv = np.append(ibv, r_ibv, axis=0)
        vr = np.append(vr, r_vr, axis=0)
        rmse = np.append(rmse, r_rmse, axis=0)

    return traj, ibv, vr, rmse


def make_plots_total(sigma, nugget):

    string = "/sigma_{:02d}/".format(int(10 * sigma)) + "nugget_{:03d}/".format(int(100 * nugget))
    savefig = figpath[:-1] + string
    checkfolder(savefig)

    def plot_comparsion_between_myopic_and_rrt(traj_myopic=None, traj_rrt=None, ibv_myopic=None, ibv_rrt=None,
                                               vr_myopic=None, vr_rrt=None, rmse_myopic=None, rmse_rrt=None,
                                               lim_ibv=None, lim_vr=None, lim_rmse=None,
                                               i=0, title="None", filename=None):

        fig = plt.figure(figsize=(70, 40))
        gs = GridSpec(nrows=3, ncols=5)
        plt.rcParams["font.family"] = "Times New Roman"
        plt.rcParams["font.size"] = 35
        def plot_trajectory_subplot(data, title):
            """ Plot each tracjectory component. """
            ax = plt.gca()
            for j in range(data.shape[0]):
                plt.plot(data[j, :i, 1], data[j, :i, 0], 'k.-', alpha=.4)
                ax.plot(plg_b[:, 1], plg_b[:, 0], 'r-.')
                ax.plot(plg_o[:, 1], plg_o[:, 0], 'r-.')
                ax.set_xlabel("East", fontsize=40)
                ax.set_ylabel("North", fontsize=40)
                ax.set_title(title, fontsize=40)
                ax.set_aspect("equal")

        def plot_simulation_result_comparison_subplot(data, steps, ylabel="IBV", lim=None, std_err: bool = False):
            """
            data: contains result for each case, should be N_replicates x 3 x N_steps.
            0: refers to EIBV dominant case
            1: refers to IVR dominant case
            2: refers to Equal weight case
            """
            N = data.shape[0]
            if std_err:
                divider = 1.645 / np.sqrt(N)
            else:
                divider = 1
            ax = plt.gca()
            hx = np.arange(steps)
            ax.errorbar(hx, y=np.mean(data[:, 0, :steps], axis=0),
                        yerr=np.std(data[:, 0, :steps], axis=0) * divider, fmt="-o", capsize=5,
                        label="EIBV dominant")
            ax.errorbar(hx, y=np.mean(data[:, 1, :steps], axis=0),
                        yerr=np.std(data[:, 1, :steps], axis=0) * divider, fmt="-o", capsize=5,
                        label="IVR dominant")
            ax.errorbar(hx, y=np.mean(data[:, 2, :steps], axis=0),
                        yerr=np.std(data[:, 2, :steps], axis=0) * divider, fmt="-o", capsize=5,
                        label="Equal weights")
            plt.legend(loc="lower left")
            plt.ylim(lim)
            plt.xlim([-.5, num_steps+.5])
            plt.grid()
            plt.xlabel('Time steps', fontsize=40)
            plt.ylabel(ylabel)
        
        def plot_best_myopic_rrt(data_rrt, data_myopic, steps, ylabel="IBV", lim=None, std_err: bool=False) -> None: 
            """
            data: contains result for each case, should be N_replicates x 3 x N_steps.
            0: refers to EIBV dominant case
            1: refers to IVR dominant case
            2: refers to Equal weight case

            Format of data_rrt: N_replicates x 3 x N_steps
                Example: data_rrt[0, 0, 0] refers to the first replicate, EIBV dominant, first step

            Format of data_myopic: N_replicates x 3 x N_steps
                Example: data_myopic[0, 0, 0] refers to the first replicate, EIBV dominant, first step

            """
            N = data_rrt.shape[0]  # number of replicates
            if std_err:
                divider = 1.645 / np.sqrt(N)
            else:
                divider = 1
            ax = plt.gca()
            hx = np.arange(steps)
            
            # ind_rrt_best = np.argmin(np.mean(data_rrt[:, :, steps], axis=0))
            # ind_myopic_best = np.argmin(np.mean(data_myopic[:, :, steps], axis=0))

            ind_rrt_best = 2
            ind_myopic_best = 2

            if ylabel == "IBV":
                ind_rrt_best = 0
                ind_myopic_best = 0
            elif ylabel == "VR":
                ind_rrt_best = 1
                ind_myopic_best = 1
            elif ylabel == "RMSE":
                ind_rrt_best = 2
                ind_myopic_best = 2

            ax.errorbar(hx, y=np.mean(data_rrt[:, ind_rrt_best, :steps], axis=0),
                        yerr=np.std(data_rrt[:, ind_rrt_best, :steps], axis=0) * divider, fmt="-o", capsize=5,
                        label="RRT " + ["EIBV dominant" if ind_rrt_best == 0 else "IVR dominant" if ind_rrt_best == 1 else "Equal weights"][0])

            ax.errorbar(hx, y=np.mean(data_myopic[:, ind_myopic_best, :steps], axis=0),
                        yerr=np.std(data_myopic[:, ind_myopic_best, :steps], axis=0) * divider, fmt="-o", capsize=5,
                        label="Myopic " + ["EIBV dominant" if ind_myopic_best == 0 else "IVR dominant" if ind_myopic_best == 1 else "Equal weights"][0])
            if np.mean(data_rrt[:, ind_rrt_best, steps]) < np.mean(data_myopic[:, ind_myopic_best, steps]):
                ax.set_title("Winner: RRT")
            else:
                ax.set_title("Winner: Myopic")
            plt.legend(loc="lower left")
            plt.ylim(lim)
            plt.xlim([-.5, num_steps+.5])
            plt.grid()
            plt.xlabel('Time steps')
            plt.ylabel(ylabel)

        def plot_simulator(traj, ibv, vr, rmse, col: int = 0, name: str = "Myopic2D"):
            ax = fig.add_subplot(gs[0, col])
            plot_trajectory_subplot(traj[:, 0, :, :], "EIBV dominant")

            ax = fig.add_subplot(gs[1, col])
            plot_trajectory_subplot(traj[:, 1, :, :], "IVR dominant")

            ax = fig.add_subplot(gs[2, col])
            plot_trajectory_subplot(traj[:, 2, :, :], "Equal weights")

            ax = fig.add_subplot(gs[0, col+2])
            plot_simulation_result_comparison_subplot(ibv, i, "IBV", lim_ibv)
            ax.set_title("Simulator: " + name)

            ax = fig.add_subplot(gs[1, col+2])
            plot_simulation_result_comparison_subplot(vr, i, "VR", lim_vr)
            ax.set_title("VR")

            ax = fig.add_subplot(gs[2, col+2])
            plot_simulation_result_comparison_subplot(rmse, i, "RMSE", lim_rmse, std_err=True)
            ax.set_title("RMSE")

        plot_simulator(traj=traj_myopic, ibv=ibv_myopic, vr=vr_myopic, rmse=rmse_myopic, col=0, name="Myopic2D")
        plot_simulator(traj=traj_rrt, ibv=ibv_rrt, vr=vr_rrt, rmse=rmse_rrt, col=1, name="RRTStar")

        ax = fig.add_subplot(gs[0, 4])
        plot_best_myopic_rrt(data_rrt=ibv_rrt, data_myopic=ibv_myopic, steps=i, ylabel="IBV", lim=lim_ibv)

        ax = fig.add_subplot(gs[1, 4])
        plot_best_myopic_rrt(data_rrt=vr_rrt, data_myopic=vr_myopic, steps=i, ylabel="VR", lim=lim_vr)

        ax = fig.add_subplot(gs[2, 4])
        plot_best_myopic_rrt(data_rrt=rmse_rrt, data_myopic=rmse_myopic, steps=i, ylabel="RMSE", lim=lim_rmse, std_err=True)

        plt.suptitle(title)
        plt.savefig(filename)
        plt.close("all")

    string_myopic = string + smyopic + "/"
    traj_myopic, ibv_myopic, vr_myopic, rmse_myopic = load_data4simulator(string_myopic)
    string_rrt = string + srrt + "/"
    traj_rrt, ibv_rrt, vr_rrt, rmse_rrt = load_data4simulator(string_rrt)

    def get_limits(value_rrt, value_myopic, std_err: bool = False) -> list:
        vmean_rrt = np.mean(value_rrt, axis=0)
        if std_err:
            vstd_rrt = np.std(value_rrt, axis=0) / np.sqrt(value_rrt.shape[0]) * 1.645
        else:
            vstd_rrt = np.std(value_rrt, axis=0)
        vmin_rrt = np.amin(vmean_rrt - vstd_rrt)
        vmax_rrt = np.amax(vmean_rrt + vstd_rrt)

        vmean_myopic = np.mean(value_myopic, axis=0)
        if std_err:
            vstd_myopic = np.std(value_myopic, axis=0) / np.sqrt(value_myopic.shape[0]) * 1.645
        else:
            vstd_myopic = np.std(value_myopic, axis=0)
        vmin_myopic = np.amin(vmean_myopic - vstd_myopic)
        vmax_myopic = np.amax(vmean_myopic + vstd_myopic)
        return [min(vmin_rrt, vmin_myopic), max(vmax_rrt, vmax_myopic)]

    lim_ibv = get_limits(ibv_rrt, ibv_myopic)
    lim_vr = get_limits(vr_rrt, vr_myopic)
    lim_rmse = get_limits(rmse_rrt, rmse_myopic, std_err=True)

    for i in tqdm(range(num_steps)):
        # if i >= 5:
        #     break
        plot_comparsion_between_myopic_and_rrt(traj_myopic=traj_myopic, traj_rrt=traj_rrt, ibv_myopic=ibv_myopic,
                                               ibv_rrt=ibv_rrt, vr_myopic=vr_myopic, vr_rrt=vr_rrt,
                                               rmse_myopic=rmse_myopic, rmse_rrt=rmse_rrt,
                                               lim_ibv=lim_ibv, lim_vr=lim_vr, lim_rmse=lim_rmse, i=i,
                                               title="sigma: {:.1f}, nugget: {:.2f}".format(sigma, nugget),
                                               filename=savefig + "P_{:03d}.png".format(i))

# make_plots_total(sigma=.1, nugget=.4)

Parallel(n_jobs=8)(
    delayed(make_plots_total)(sigma=sigma, nugget=nugget) for sigma, nugget in sigmas_nuggets)
