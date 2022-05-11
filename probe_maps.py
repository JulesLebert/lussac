import numpy as np
from probeinterface import generate_multi_columns_probe

def generate_WARP_probe():
    probe = generate_multi_columns_probe(num_columns=8,
                                    num_contact_per_column=4,
                                    xpitch=350, ypitch=350,
                                    contact_shapes='circle')
    probe.create_auto_shape('rect')

    channel_indices = np.array([29, 31, 13, 15,
                                25, 27, 9, 11,
                                30, 32, 14, 16,
                                26, 28, 10, 12,
                                24, 22, 8, 6,
                                20, 18, 4, 2,
                                23, 21, 7, 5,
                                19, 17, 3, 1 ])

    probe.set_device_channel_indices(channel_indices - 1)
    return probe