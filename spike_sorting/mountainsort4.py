import os
import shutil
import spikesorters
import spiketoolkit
import spikeinterface as si
import spikeinterface.sorters as ss
from spikeinterface.exporters import export_to_phy

from .spike_sorter import SpikeSorter


class MountainSort4(SpikeSorter):

	def launch(self, name: str, params: dict={}):
		"""

		"""

		sorting = ss.run_mountainsort4(recording=self.recording, output_folder=self.output_folder + "/output", **params)
		# tmp_folder = "{0}/output/tmp".format(self.output_folder)
		recording = self.recording
		# annotate as filtered even if not to save in phy
		# filter will be performed in 
		recording.annotate(is_filtered=True)
		# os.makedirs(tmp_folder, exist_ok=True)
		# sorting.set_tmp_folder(tmp_folder)
		we = si.WaveformExtractor.create(self.recording, sorting, 'waveforms', remove_if_exists=True)
		we.set_params(ms_before=1.0, ms_after=3.0, max_spikes_per_unit=1000)
		we.run_extract_waveforms(n_jobs=3, chunk_size=30000)
		export_to_phy(we, self.output_folder + "/{0}".format(name),
              compute_pc_features=False, compute_amplitudes=False, copy_binary=True,
			   dtype=self.data_params['dtype'])
		# spiketoolkit.postprocessing.export_to_phy(self.recording, sorting, self.output_folder + "/{0}".format(name), compute_pc_features=False, compute_amplitudes=False, max_channels_per_template=self.data_params['n_channels'],
		# 														max_spikes_per_unit=1000, copy_binary=False, ms_before=1.0, ms_after=3.0, dtype=self.data_params['dtype'], recompute_info=True, n_jobs=3, filter_flag=False)

		del sorting
		shutil.rmtree("{0}/output".format(self.output_folder))
