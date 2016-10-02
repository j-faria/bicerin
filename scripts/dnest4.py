import copy
import numpy as np
import matplotlib.pyplot as plt

pyqt = True
if pyqt:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui

def logsumexp(values):
    biggest = np.max(values)
    x = values - biggest
    result = np.log(np.sum(np.exp(x))) + biggest
    return result

def logdiffexp(x1, x2):
    biggest = x1
    xx1 = x1 - biggest
    xx2 = x2 - biggest
    result = np.log(np.exp(xx1) - np.exp(xx2)) + biggest
    return result

def postprocess(temperature=1., numResampleLogX=1, plot=True, loaded=[], \
            cut=0., save=True, zoom_in=True, compression_bias_min=1., compression_scatter=0., moreSamples=1., compression_assert=None):
    if len(loaded) == 0:
        levels_orig = np.atleast_2d(np.loadtxt("levels.txt"))
        sample_info = np.atleast_2d(np.loadtxt("sample_info.txt"))
        sample = np.atleast_2d(np.loadtxt("sample.txt"))

        # I believe this is the fastest way to get the 2nd line 
        # and doesn't load the whole file into memory
        fp = open('sample.txt')
        for i, line in enumerate(fp):
            if i==1: 
                sample_file_header = line
            elif i>2: 
                break
        fp.close()

        #if(sample.shape[0] == 1):
        #   sample = sample.T
    else:
        levels_orig, sample_info, sample = loaded[0], loaded[1], loaded[2]

    # Remove regularisation from levels_orig if we asked for it
    if compression_assert is not None:
        levels_orig[1:,0] = -np.cumsum(compression_assert*np.ones(levels_orig.shape[0] - 1))

    sample = sample[int(cut*sample.shape[0]):, :]
    sample_info = sample_info[int(cut*sample_info.shape[0]):, :]

    if sample.shape[0] != sample_info.shape[0]:
        print('# Size mismatch. Truncating...')
        lowest = np.min([sample.shape[0], sample_info.shape[0]])
        sample = sample[0:lowest, :]
        sample_info = sample_info[0:lowest, :]

    if plot:

        if pyqt:
            # win.setWindowTitle('Np posterior')
            win = pg.GraphicsWindow()
            plt1 = win.addPlot()
            plt1.plot(sample_info[:,0],
                            labels={'left': ('Level'), 'bottom': ('Iteration')})
            
            QtGui.QApplication.instance().exec_()
            
            win = pg.GraphicsWindow()
            plt1 = win.addPlot(row=1, col=1)
            plt1.plot(np.diff(levels_orig[:,0]))
            plt1.setLabel('left', "Compression")

            plt2 = win.addPlot(row=2, col=1)
            good = np.nonzero(levels_orig[:,4] > 0)[0]
            plt2.plot(levels_orig[good,3]/levels_orig[good,4])
            plt2.setYRange(0, 1)
            plt2.setLabel('left', "MH Acceptance")
            plt2.setLabel('bottom', "Level")

            QtGui.QApplication.instance().exec_()
        
        else:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.plot(sample_info[:,0])
            ax.set_xlabel("Iteration"); ax.set_ylabel("Level")

            fig = plt.figure()
            ax = fig.add_subplot(2,1,1)
            ax.plot(np.diff(levels_orig[:,0]))
            ax.set_xlabel("Level"); ax.set_ylabel("Compression"); 

            xlim = ax.get_xlim()
            ax.axhline(-1., color='r')
            ax.axhline(-np.log(10.), color='g')
            ax.set_ylim(ymax=0.05)

            ax = fig.add_subplot(2,1,2)
            good = np.nonzero(levels_orig[:,4] > 0)[0]
            ax.plot(levels_orig[good,3]/levels_orig[good,4])
            ax.set_xlim(xlim); ax.set_ylim([0., 1.])
            ax.set_xlabel("Level"); ax.set_ylabel("MH Acceptance")

    # Convert to lists of tuples
    logl_levels = [(levels_orig[i,1], levels_orig[i, 2]) for i in range(0, levels_orig.shape[0])] # logl, tiebreaker
    logl_samples = [(sample_info[i, 1], sample_info[i, 2], i) for i in range(0, sample.shape[0])] # logl, tiebreaker, id
    logx_samples = np.zeros((sample_info.shape[0], numResampleLogX))
    logp_samples = np.zeros((sample_info.shape[0], numResampleLogX))
    logP_samples = np.zeros((sample_info.shape[0], numResampleLogX))
    P_samples = np.zeros((sample_info.shape[0], numResampleLogX))
    logz_estimates = np.zeros((numResampleLogX, 1))
    H_estimates = np.zeros((numResampleLogX, 1))

    # Find sandwiching level for each sample
    sandwich = sample_info[:,0].copy().astype('int')
    for i in range(0, sample.shape[0]):
        while sandwich[i] < levels_orig.shape[0]-1 and logl_samples[i] > logl_levels[sandwich[i] + 1]:
            sandwich[i] += 1

    for z in range(0, numResampleLogX):
        # Make a monte carlo perturbation of the level compressions
        levels = levels_orig.copy()
        compressions = -np.diff(levels[:,0])
        compressions *= compression_bias_min + (1. - compression_bias_min)*np.random.rand()
        compressions *= np.exp(compression_scatter*np.random.randn(compressions.size))
        levels[1:, 0] = -compressions
        levels[:, 0] = np.cumsum(levels[:,0])

        # For each level
        for i in range(0, levels.shape[0]):
            # Find the samples sandwiched by this level
            which = np.nonzero(sandwich == i)[0]
            logl_samples_thisLevel = [] # (logl, tieBreaker, ID)
            for j in range(0, len(which)):
                logl_samples_thisLevel.append(copy.deepcopy(logl_samples[which[j]]))
            logl_samples_thisLevel = sorted(logl_samples_thisLevel)
            N = len(logl_samples_thisLevel)

            # Generate intermediate logx values
            logx_max = levels[i, 0]
            if i == levels.shape[0]-1:
                logx_min = -1E300
            else:
                logx_min = levels[i+1, 0]
            Umin = np.exp(logx_min - logx_max)

            if N == 0 or numResampleLogX > 1:
                U = Umin + (1. - Umin)*np.random.rand(len(which))
            else:
                U = Umin + (1. - Umin)*np.linspace(1./(N+1), 1. - 1./(N+1), N)
            logx_samples_thisLevel = np.sort(logx_max + np.log(U))[::-1]

            for j in range(0, which.size):
                logx_samples[logl_samples_thisLevel[j][2]][z] = logx_samples_thisLevel[j]

                if j != which.size - 1:
                    left = logx_samples_thisLevel[j+1]
                elif i == levels.shape[0]-1:
                    left = -1E300
                else:
                    left = levels[i+1][0]
                
                if j != 0:
                    right = logx_samples_thisLevel[j-1]
                else:
                    right = levels[i][0]

                logp_samples[logl_samples_thisLevel[j][2]][z] = np.log(0.5) + logdiffexp(right, left)

        logl = sample_info[:,1]/temperature

        logp_samples[:,z] = logp_samples[:,z] - logsumexp(logp_samples[:,z])
        logP_samples[:,z] = logp_samples[:,z] + logl
        logz_estimates[z] = logsumexp(logP_samples[:,z])
        logP_samples[:,z] -= logz_estimates[z]
        P_samples[:,z] = np.exp(logP_samples[:,z])
        H_estimates[z] = -logz_estimates[z] + np.sum(P_samples[:,z]*logl)

        if plot:
            if pyqt:
                win = pg.GraphicsWindow()
                plt1 = win.addPlot(row=1, col=1)
                plt1.plot(logx_samples[:,z], sample_info[:,1], name='Samples',
                          pen=None, symbolSize=4, symbolBrush=(0,0,255))
                plt1.plot(levels[1:,0], levels[1:,1], name='Levels',
                          pen=None, symbolSize=6, symbolBrush=(255,0,0))
                
                combined_logl = np.hstack([sample_info[:,1], levels[1:, 1]])
                combined_logl = np.sort(combined_logl)
                lower = combined_logl[int(0.1*combined_logl.size)]
                upper = combined_logl[-1]
                diff = upper - lower
                lower -= 0.05*diff
                upper += 0.05*diff
                if zoom_in:
                    plt1.setYRange(lower, upper)

                plt1.setLabel('left', "log L")

                plt2 = win.addPlot(row=2, col=1)
                good = np.nonzero(levels_orig[:,4] > 0)[0]
                plt2.plot(logx_samples[:,z], P_samples[:,z], 
                           pen=None, symbolPen=None, symbolSize=7, symbolBrush=(100, 100, 255))
                # plt2.setYRange(0, 1)
                plt2.setLabel('left', "Posterior Weights")
                plt2.setLabel('bottom', "log(X)")

                QtGui.QApplication.instance().exec_()
            else: 
                plt.figure()

                plt.subplot(2,1,1)
                plt.plot(logx_samples[:,z], sample_info[:,1], 'b.', label='Samples')
                plt.plot(levels[1:,0], levels[1:,1], 'r.', label='Levels')
                plt.legend(numpoints=1, loc='lower left')
                plt.ylabel('log(L)')
                plt.title(str(z+1) + "/" + str(numResampleLogX) + ", log(Z) = " + str(logz_estimates[z][0]))
                # Use all plotted logl values to set ylim
                combined_logl = np.hstack([sample_info[:,1], levels[1:, 1]])
                combined_logl = np.sort(combined_logl)
                lower = combined_logl[int(0.1*combined_logl.size)]
                upper = combined_logl[-1]
                diff = upper - lower
                lower -= 0.05*diff
                upper += 0.05*diff
                if zoom_in:
                    plt.ylim([lower, upper])

                xlim = plt.gca().get_xlim()

                plt.subplot(2,1,2)
                plt.plot(logx_samples[:,z], P_samples[:,z], 'b.')
                plt.ylabel('Posterior Weights')
                plt.xlabel('log(X)')
                plt.xlim(xlim)

    P_samples = np.mean(P_samples, 1)
    P_samples = P_samples/np.sum(P_samples)
    logz_estimate = np.mean(logz_estimates)
    logz_error = np.std(logz_estimates)
    H_estimate = np.mean(H_estimates)
    H_error = np.std(H_estimates)
    ESS = np.exp(-np.sum(P_samples*np.log(P_samples+1E-300)))

    print("log(Z) = " + str(logz_estimate) + " +- " + str(logz_error))
    print("Information = " + str(H_estimate) + " +- " + str(H_error) + " nats.")
    print("Effective sample size = " + str(ESS))

    # Resample to uniform weight
    N = int(moreSamples*ESS)
    posterior_sample = np.zeros((N, sample.shape[1]))
    w = P_samples
    w = w/np.max(w)
    if save:
        np.savetxt('weights.txt', w) # Save weights
    for i in range(0, N):
        while True:
            which = np.random.randint(sample.shape[0])
            if np.random.rand() <= w[which]:
                break
        posterior_sample[i,:] = sample[which,:]
    if save:
        np.savetxt("posterior_sample.txt", posterior_sample)

    if plot:
        plt.show()

    return [logz_estimate, H_estimate, logx_samples, posterior_sample]


def diffusion_plot():
    """
    Plot a nice per-particle diffusion plot.
    """

    sample_info = np.atleast_2d(np.loadtxt('sample_info.txt'))
    ID = sample_info[:,3].astype('int')
    j = sample_info[:,0].astype('int')

    ii = np.arange(1, sample_info.shape[0] + 1)

    for i in range(0, ID.max() + 1):
        which = np.nonzero(ID == i)[0]
        plt.plot(ii[which], j[which])

    plt.xlabel('Iteration')
    plt.ylabel('Level')
    plt.show()

def levels_plot():
    """
    Plot the differences between the logl values of the levels.
    """
    levels = np.loadtxt('levels.txt')

    plt.plot(np.log10(np.diff(levels[:,1])))
    plt.ylim([-1, 4])
    plt.axhline(0., color='r')
    plt.axhline(np.log10(np.log(10.)), color='g')
    plt.xlabel('Level')
    plt.ylabel('Delta log likelihood')
    plt.show()

