import numpy as np
import matplotlib.pyplot as plt

def find_inverse_sample(sample, arr, low):
    abs_diffs = np.abs(arr-sample)
    sorted_ids = np.argsort(abs_diffs)
    inv_sample = sorted_ids[1]*abs_diffs[sorted_ids[0]]+sorted_ids[0]*abs_diffs[sorted_ids[1]]
    inv_sample = inv_sample/(abs_diffs[sorted_ids[0]]+abs_diffs[sorted_ids[1]])
    return inv_sample+low

if __name__=="__main__":
    phase_curve = np.load("phase_vals.npy")
    
    # # Plot phase curve to get range
    # plt.plot(phase_curve)
    # plt.show()

    # Range is 2 to 244

    # Find flip point
    print(np.argmax(phase_curve))

    # # Wrap phase
    phase_curve[np.argmax(phase_curve):] = 2*np.pi - phase_curve[np.argmax(phase_curve):]
    plt.plot(phase_curve)
    plt.show()

    # Find range
    low = np.argmin(phase_curve)
    high = np.argmax(phase_curve)

    # Truncate
    truncated_phase_curve = phase_curve[low:high+1]
    plt.plot(truncated_phase_curve)
    plt.show()

    # Sample range uniformly 256 times
    sampled_range = np.linspace(phase_curve[low], phase_curve[high], 256)
    
    # Get inverse vals
    inv_samples = [find_inverse_sample(sample, truncated_phase_curve, low) for sample in sampled_range]
    inv_samples = np.array(inv_samples)

    # Map to required range
    inv_samples = np.round(inv_samples*319/256)

    # Save csv file
    with open('clut_pluto.csv', 'a') as the_file:
        for i in range(256):
            the_file.write(f'{int(inv_samples[i])}\n')