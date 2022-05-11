import abc
import numpy as np
# import spikeextractors
import tdt

import spikeinterface.extractors as se
from probeinterface import generate_multi_columns_probe


class SpikeSorter(metaclass=abc.ABCMeta):

	def __init__(self, params: dict, output_folder: str):
		"""

		"""

		self.recording = se.CustomTdtRecordingExtractor(params['file'], store=params['stores'])

		data_cmr = self.recording.get_traces() - np.median(self.recording.get_traces(), axis=0)[None, :].astype(params['dtype']) # Common median reference.
		self.recording._timeseries = data_cmr
		
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
		self.recording = self.recording.set_probe(probe)


		# self.recording = spikeextractors.BinDatRecordingExtractor(params['file'], params['sampling_rate'], params['n_channels'], params['dtype'])
		# data_cmr = self.recording.get_traces() - np.median(self.recording.get_traces(), axis=0)[None, :].astype(params['dtype']) # Common median reference.
		# self.recording._timeseries = data_cmr
		# self.recording = self.recording.load_probe_file(params['prb'])

		self.data_params = params
		self.output_folder = output_folder




	@abc.abstractmethod
	def launch(self, name: str, params: dict={}):
		"""

		"""
