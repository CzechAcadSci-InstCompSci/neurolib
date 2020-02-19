import copy as cp
import numpy as np

from neurolib.models.hopf.timeIntegration import timeIntegration
import neurolib.models.hopf.loadDefaultParams as dp
from neurolib.models import bold


def chunkwiseTimeIntegration(params, chunkSize=10000, simulateBOLD=True, saveAllActivity=False):
    # time stuff
    totalDuration = params["duration"]

    # compute maximum delay of model
    dt = params["dt"]
    Dmat = dp.computeDelayMatrix(params["lengthMat"], params["signalV"])
    Dmat_ndt = np.around(Dmat / dt)  # delay matrix in multiples of dt
    max_global_delay = np.amax(Dmat_ndt)
    delay_Ndt = int(max_global_delay + 1)

    paramsChunk = cp.deepcopy(params)

    N = params["Cmat"].shape[0]

    if simulateBOLD:
        boldModel = bold.BOLDModel(N, dt)

    # initialize data arrays
    t_BOLD_return = np.array([], dtype="f", ndmin=1)
    BOLD_return = np.array([], dtype="f", ndmin=2)
    all_t = np.array([], dtype="f", ndmin=1)
    t_return = np.array([], dtype="f", ndmin=1)
    all_xs = np.array([], dtype="f", ndmin=2).reshape(N, 0)
    xs_return = np.array([], dtype="f", ndmin=2)
    all_ys = np.array([], dtype="f", ndmin=2).reshape(N, 0)
    ys_return = np.array([], dtype="f", ndmin=2)

    lastT = 0
    while lastT < totalDuration:

        # Determine the size of the next chunk
        currentChunkSize = min(chunkSize, (totalDuration - lastT) / dt)
        currentChunkSize += delay_Ndt
        paramsChunk["duration"] = currentChunkSize * dt

        # Time Integration
        t_chunk, xs_chunk, ys_chunk, x_ou_chunk, y_ou_chunk = timeIntegration(paramsChunk)

        # Prepare integration parameters for the next chunk
        paramsChunk["xs_init"] = xs_chunk[:, -delay_Ndt:]
        paramsChunk["ys_init"] = ys_chunk[:, -delay_Ndt:]

        xs_return = xs_chunk[:, delay_Ndt:]
        ys_return = ys_chunk[:, delay_Ndt:]
        t_return = t_chunk[:-delay_Ndt]

        del xs_chunk, ys_chunk, t_chunk

        if saveAllActivity:
            all_xs = np.hstack((all_xs, xs_return))
            all_ys = np.hstack((all_ys, ys_return))
            all_t = np.hstack((all_t, np.add(t_return, lastT)))

        if simulateBOLD:
            boldModel.run(xs_return, normalize=True)
            BOLD_return = boldModel.BOLD
            t_BOLD_return = boldModel.t_BOLD

        # in crement time counter
        lastT = lastT + t_return[-1] + dt

    if saveAllActivity:
        xs_return = all_xs
        ys_return = all_ys
        t_return = all_t

    return t_return, xs_return, ys_return, x_ou_chunk, y_ou_chunk, t_BOLD_return, BOLD_return
