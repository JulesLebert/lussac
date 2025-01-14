import os
import numpy as np
import spikeextractors
import spiketoolkit

import postprocessing.utils
from postprocessing.wvf_extractor import WaveformExtractor
import spikeinterface.extractors as se
import probe_maps

class PhyData:

	def __init__(self, params: dict):
		"""
		Creates a new PhyData instance.
		Loads all of the necessary data.

		@params params (dict):
			The params.json file containing eveything we need to know.
		"""

		self.sampling_f = params['recording']['sampling_rate']
		# self.recording = spikeextractors.BinDatRecordingExtractor(params['recording']['file'], params['recording']['sampling_rate'], params['recording']['n_channels'], params['recording']['dtype'])
		# self.recording = se.CustomTdtRecordingExtractor(params['recording']['file'], store=params['recording']['stores'])
		# probe = probe_maps.generate_WARP_probe()
		# self.recording = self.recording.set_probe(probe)
		self.recording = spikeextractors.BinDatRecordingExtractor('{}/recording.dat'.format(params['phy_folders'][0]), params['recording']['sampling_rate'], params['recording']['n_channels'], params['recording']['dtype'])


		self.uvolt_ratio = params['recording']['uvolt'] if 'uvolt' in params['recording'] else None

		self._sortings = []
		for path in params['phy_folders']:
			self._sortings.append(spiketoolkit.curation.CurationSortingExtractor(spikeextractors.PhySortingExtractor(path)))
			del self._sortings[-1]._parent_sorting # Redundant information that takes a lot of RAM.

		self.merged_sorting = spikeextractors.NumpySortingExtractor()
		self.merged_sorting.set_sampling_frequency(self.sampling_f)

		self.set_tmp_folder(params['post_processing']['tmp_folder'])
		self.logs_folder = params['post_processing']['logs_folder']

		self.wvf_extractor = WaveformExtractor(self)


	def set_tmp_folder(self, tmp_folder: str):
		"""
		Sets all sortings temporary folder (e.g. for waveforms extraction).

		@param tmp_folder (str):
			Location of temporary folder to set.
		"""

		os.makedirs(tmp_folder, exist_ok=True)

		for sorting in range(len(self._sortings)):
			os.makedirs("{0}/sorting_{1}".format(tmp_folder, sorting), exist_ok=True)
			self._sortings[sorting].set_tmp_folder("{0}/sorting_{1}".format(tmp_folder, sorting))

		os.makedirs("{0}/merged_sorting".format(tmp_folder), exist_ok=True)
		self.merged_sorting.set_tmp_folder("{0}/merged_sorting".format(tmp_folder))


	def set_sorting(self, idx: int):
		"""
		Sets the current working sorting (PhyData.sorting).

		@param idx (int):
			Index of the working sorting to set in PhyData._sortings.
		"""
		assert idx >= 0 and idx < len(self._sortings)

		self.sorting = self._sortings[idx]
		self.sorting_idx = idx


	def get_num_sortings(self):
		"""
		Returns the number of sortings.

		@return number_of_sortings (int):
			Length of list PhyData._sortings.
		"""

		return len(self._sortings)


	def get_unit_spike_train(self, unit_id: int):
		"""
		Returns the spike_train of a unit.

		@param unit_id (int):
			Id of unit to get the spike train of.

		@return spike_train (np.ndarray[uint64]) [n_spikes]:
			Time of each spikes (in sampling time).
		"""

		return self.sorting.get_unit_spike_train(unit_id)


	def set_unit_spike_train(self, unit_id: int, spike_train: list):
		"""
		Sets a unit spike train.

		@param unit_id (int):
			Id of unit to change the spike train of.
		@param spike_train (list or np.ndarray[int]):
			New spike train to set (change in sampling time).
		"""

		unit = None
		for root in self.sorting._roots:
			if root.unit_id == unit_id:
				unit = root
				break

		assert unit != None
		unit.set_spike_train(spike_train)


	def get_unit_firing_rate(self, unit_id: int):
		"""
		Returns the firing rate (Hz) of a unit.

		@param unit_id (int):
			Id of unit to get the firing rate's of.

		@return firing_rate (float):
			Firing rate of the unit (in Hz).
		"""

		return len(self.get_unit_spike_train(unit_id)) / self.recording.get_num_frames() * self.sampling_f


	def get_units_waveforms(self, unit_ids: list, **params):
		"""
		See WaveformExtractor.get_units_waveforms().
		"""

		return self.wvf_extractor.get_units_waveforms(unit_ids, self.sorting_idx, **params)

	def get_unit_waveforms(self, unit_id: int, **params):
		"""
		See WaveformExtractor.get_unit_waveforms().
		"""

		return self.wvf_extractor.get_unit_waveforms(unit_id, self.sorting_idx, **params)

	def get_units_mean_waveform(self, unit_ids: list, save_mean: bool=True, **params):
		"""
		See WaveformExtractor.get_units_mean_waveform().
		"""

		return self.wvf_extractor.get_units_mean_waveform(unit_ids, self.sorting_idx, save_mean, **params)

	def get_unit_mean_waveform(self, unit_id: int, save_mean: bool=True, **params):
		"""
		See WaveformExtractor.get_unit_mean_waveforms().
		"""

		return self.wvf_extractor.get_unit_mean_waveform(unit_id, self.sorting_idx, save_mean, **params)

	def get_waveforms_from_spiketrain(self, spike_train: np.ndarray, **params):
		"""
		See WaveformExtractor.get_waveforms_from_spiketrain().
		"""

		return self.wvf_extractor.get_waveforms_from_spiketrain(spike_train, **params)

	def clear_wvfs(self):
		"""
		Clears all saved waveforms from the WaveformExtractor.
		"""

		self.wvf_extractor.clear()


	def get_all_correlograms(self, unit_ids: list, bin_size: float=1.0/3.0, max_time: float=40.0):
		"""
		Returns all auto and cross-correlograms for the units passed in.

		@param unit_ids (list of int) [n_units]:
			ID of each unit for which the correlograms will be computed.
		@param bin_size (float):
			Size of a bin for the correlograms (in ms).
		@param max_time (float):
			Time limit for the correlograms (in ms).

		@return correlograms (np.ndarray[uint32]) [n_units, n_units, time]:
			Auto-correlogram (in the diagonal) and cross-correlogram between all units.
		@return bins (np.ndarray) [time+1]:
			Limits of each bin (in ms).
		"""

		template, bins = postprocessing.utils.get_autocorr(self, unit_ids[0], bin_size, max_time)
		correlograms = np.zeros([len(unit_ids), len(unit_ids), len(template)], dtype=np.uint64)

		for i in range(len(unit_ids)):
			for j in range(i, len(unit_ids)):
				if i == j:
					correlograms[i, j] = postprocessing.utils.get_autocorr(self, unit_ids[i], bin_size, max_time)[0]
				else:
					correlograms[i, j] = postprocessing.utils.get_crosscorr(self, unit_ids[i], unit_ids[j], bin_size, max_time)[0]
					correlograms[j, i] = (correlograms[i, j])[::-1] # Almost exact. Will differ for spikes at exact same timing.

		return (correlograms, bins)


	def change_spikes_time(self, unit_id: int, shift):
		"""
		Shifts a unit's spike train (positive means later in time).

		@param unit_id (int):
			ID of unit that will undergo the spikes timing change.
		@param shift (np.ndarray or int):
			If np.ndarray: each shift for each spike.
			If int: value to change each spike by.
		"""
		assert np.issubdtype(type(shift), np.integer) or len(shift) == len(self.sorting.get_unit_spike_train(unit_id))

		# Type check, otherwise it can mess stuff up.
		if isinstance(shift, np.ndarray):
			shift = shift.astype(np.int64)
		else:
			shift = np.int64(shift)

		spike_train = self.get_unit_spike_train(unit_id).astype(np.int64) + shift
		spike_train[spike_train <= 0] = 1
		
		self.set_unit_spike_train(unit_id, spike_train.astype(np.uint64))
