# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

# MIDI controller.
from pycomposer.midi_controller import MidiController

# is-a `TrueSampler`
from pycomposer.truesampler.bar_true_sampler import BarTrueSampler
# is-a `NoiseSampler`.
from pycomposer.noisesampler.bar_noise_sampler import BarNoiseSampler

# is-a `NoiseSampler`.
from pygan.noisesampler.uniform_noise_sampler import UniformNoiseSampler
# is-a `GenerativeModel`.
from pygan.generativemodel.autoencodermodel.convolutional_auto_encoder import ConvolutionalAutoEncoder as Generator
# is-a `DiscriminativeModel`.
from pygan.discriminativemodel.cnnmodel.seq_cnn_model import SeqCNNModel as Discriminator
# is-a `GANsValueFunction`.
from pygan.gansvaluefunction.mini_max import MiniMax
# GANs framework.
from pygan.generativeadversarialnetworks.adversarial_auto_encoders import AdversarialAutoEncoders

# Activation function.
from pydbm.activation.tanh_function import TanhFunction
# Logistic Function as activation function.
from pydbm.activation.logistic_function import LogisticFunction
# Batch normalization.
from pydbm.optimization.batch_norm import BatchNorm
# Convolution layer.
from pydbm.cnn.layerablecnn.convolution_layer import ConvolutionLayer as ConvolutionLayerG1
from pydbm.cnn.layerablecnn.convolution_layer import ConvolutionLayer as ConvolutionLayerG2
from pydbm.cnn.layerablecnn.convolution_layer import ConvolutionLayer as ConvolutionLayerD1
# Computation graph in output layer.
from pydbm.synapse.cnn_output_graph import CNNOutputGraph
# Computation graph for convolution layer.
from pydbm.synapse.cnn_graph import CNNGraph as CNNGraphG1
from pydbm.synapse.cnn_graph import CNNGraph as CNNGraphG2
from pydbm.synapse.cnn_graph import CNNGraph as CNNGraphD1
from pydbm.synapse.cnn_graph import CNNGraph as DeCNNGraphD1
from pydbm.synapse.cnn_graph import CNNGraph as DeCNNGraphD2

# Sign function as activation function.
from pydbm.activation.signfunction.deterministic_binary_neurons import DeterministicBinaryNeurons
from pydbm.activation.signfunction.stochastic_binary_neurons import StochasticBinaryNeurons
# SGD optimizer.
from pydbm.optimization.optparams.sgd import SGD
# Adams optimizer.
from pydbm.optimization.optparams.adam import Adam
# Mean Squared Error(MSE).
from pydbm.loss.mean_squared_error import MeanSquaredError
from pydbm.loss.cross_entropy import CrossEntropy
# Verification.
from pydbm.verification.verificate_function_approximation import VerificateFunctionApproximation
# Convolutional Auto-Encoder.
from pydbm.cnn.convolutionalneuralnetwork.convolutional_auto_encoder import ConvolutionalAutoEncoder as CAE
# Deconvolution layer.
from pydbm.cnn.layerablecnn.convolutionlayer.deconvolution_layer import DeconvolutionLayer as DeconvolutionLayer1
from pydbm.cnn.layerablecnn.convolutionlayer.deconvolution_layer import DeconvolutionLayer as DeconvolutionLayer2


class AAEComposer(object):
    '''
    Algorithmic Composer based on Adversarial Auto-Encoders(AAEs) (Makhzani, A., et al., 2015).

    This composer learns observed data points drawn from a conditional true distribution 
    of input MIDI files, trained using back propagation in an unsupervised manner, by 
    minimizing the reconsturction errors of the decoding results from the original inputs,
    and generates feature points drawn from a fake distribution that means such as Uniform 
    distribution or Normal distribution, imitating the true MIDI files data.

    The components included in this class are functionally differentiated into three models.

    1. `TrueSampler`.
    2. `Generator`.
    3. `Discriminator`.

    The function of `TrueSampler` is to draw samples from a true distribution of input MIDI files. 
    `Generator`, which is-a `AutoEncoders`, has `NoiseSampler`s and draws fake samples from a Uniform 
    distribution or Normal distribution by use it. And `Discriminator` observes those input samples, 
    trying discriminating true and fake data. 

    While `Discriminator` observes `Generator`'s observation to discrimine the output from true samples, 
    `Generator` observes `Discriminator`'s observations to confuse `Discriminator`s judgments. 
    In GANs framework, the mini-max game can be configured by the observations of observations.

    While doing this game, the `Generator` also learns by the reconsturction errors with a special
    loss function `DissonanceLoss` which computes losses as scores of dissonance.

    After this game, the `Generator` will grow into a functional equivalent that enables to imitate 
    the `TrueSampler` and makes it possible to compose similar but slightly different music by the 
    imitation.

    Following MidiNet and MuseGAN(Dong, H. W., et al., 2018), this class consider bars
    as the basic compositional unit for the fact that harmonic changes usually occur at 
    the boundaries of bars and that human beings often use bars as the building blocks 
    when composing songs. The feature engineering in this class also is inspired by 
    the Multi-track piano-roll representations in MuseGAN. 

    References:
        - Dong, H. W., Hsiao, W. Y., Yang, L. C., & Yang, Y. H. (2018, April). MuseGAN: Multi-track sequential generative adversarial networks for symbolic music generation and accompaniment. In Thirty-Second AAAI Conference on Artificial Intelligence.
        - Fang, W., Zhang, F., Sheng, V. S., & Ding, Y. (2018). A method for improving CNN-based image recognition using DCGAN. Comput. Mater. Contin, 57, 167-178.
        - Gauthier, J. (2014). Conditional generative adversarial nets for convolutional face generation. Class Project for Stanford CS231N: Convolutional Neural Networks for Visual Recognition, Winter semester, 2014(5), 2.
        - Goodfellow, I., Pouget-Abadie, J., Mirza, M., Xu, B., Warde-Farley, D., Ozair, S., ... & Bengio, Y. (2014). Generative adversarial nets. In Advances in neural information processing systems (pp. 2672-2680).
        - Long, J., Shelhamer, E., & Darrell, T. (2015). Fully convolutional networks for semantic segmentation. In Proceedings of the IEEE conference on computer vision and pattern recognition (pp. 3431-3440).
        - Makhzani, A., Shlens, J., Jaitly, N., Goodfellow, I., & Frey, B. (2015). Adversarial autoencoders. arXiv preprint arXiv:1511.05644.
        - Yang, L. C., Chou, S. Y., & Yang, Y. H. (2017). MidiNet: A convolutional generative adversarial network for symbolic-domain music generation. arXiv preprint arXiv:1703.10847.

    '''

    def __init__(
        self, 
        midi_path_list, 
        batch_size=10,
        seq_len=4,
        time_fraction=1.0,
        min_pitch=24,
        max_pitch=108,
        learning_rate=1e-05,
        hidden_dim=None,
        true_sampler=None,
        noise_sampler=None,
        generative_model=None,
        discriminative_model=None,
        gans_value_function=None
    ):
        '''
        Init.

        Args:
            midi_path_list:         `list` of paths to MIDI files.
            batch_size:             Batch size.
            seq_len:                The length of sequence that LSTM networks will observe.
            time_fraction:          Time fraction or time resolution (seconds).

            min_pitch:              The minimum of note number.
            max_pitch:              The maximum of note number.

            learning_rate:          Learning rate in `Generator` and `Discriminator`.

            hidden_dim:             The number of units in hidden layer of `DiscriminativeModel`.

            true_sampler:           is-a `TrueSampler`.
            noise_sampler:          is-a `NoiseSampler`.
            generative_model:       is-a `GenerativeModel`.
            discriminative_model:   is-a `DiscriminativeModel`.
            gans_value_function:    is-a `GANsValueFunction`.
        '''
        self.__midi_controller = MidiController()
        self.__midi_df_list = [self.__midi_controller.extract(midi_path) for midi_path in midi_path_list]

        # The dimension of observed or feature points.
        dim = max_pitch - min_pitch
        scale = 0.01

        if true_sampler is None:
            true_sampler = BarTrueSampler(
                midi_df_list=self.__midi_df_list,
                batch_size=batch_size,
                seq_len=seq_len,
                time_fraction=time_fraction,
                min_pitch=min_pitch,
                max_pitch=max_pitch,
                conditional_flag=False
            )

        if noise_sampler is None:
            noise_sampler = BarNoiseSampler(
                midi_df_list=self.__midi_df_list,
                batch_size=batch_size,
                seq_len=seq_len,
                time_fraction=time_fraction,
                min_pitch=min_pitch,
                max_pitch=max_pitch
            )
            channel = noise_sampler.channel
        else:
            program_list = [self.__midi_df_list[i].program for i in range(len(self.__midi_df_list))]
            program_list = list(set(program_list))
            channel = len(program_list)

        if generative_model is None:
            conv1 = ConvolutionLayerG1(
                CNNGraphG1(
                    activation_function=TanhFunction(),
                    # The number of filters.
                    filter_num=batch_size,
                    channel=channel,
                    # Kernel size.
                    kernel_size=3,
                    scale=scale,
                    # The number of strides.
                    stride=1,
                    # The number of zero-padding.
                    pad=1
                )
            )

            conv2 = ConvolutionLayerG2(
                CNNGraphG2(
                    activation_function=TanhFunction(),
                    filter_num=batch_size,
                    channel=batch_size,
                    kernel_size=3,
                    scale=scale,
                    stride=1,
                    pad=1
                )
            )

            deconvolution_layer_list = [
                DeconvolutionLayer1(
                    DeCNNGraphD1(
                        activation_function=TanhFunction(),
                        filter_num=batch_size,
                        channel=channel,
                        kernel_size=3,
                        scale=scale,
                        stride=1,
                        pad=1
                    )
                )
            ]

            opt_params = Adam()
            # The probability of dropout.
            opt_params.dropout_rate = 0.0

            convolutional_auto_encoder = CAE(
                layerable_cnn_list=[
                    conv1, 
                    conv2
                ],
                epochs=100,
                batch_size=batch_size,
                learning_rate=learning_rate,
                # # Attenuate the `learning_rate` by a factor of this value every `attenuate_epoch`.
                learning_attenuate_rate=0.1,
                # # Attenuate the `learning_rate` by a factor of `learning_attenuate_rate` every `attenuate_epoch`.
                attenuate_epoch=25,
                computable_loss=MeanSquaredError(),
                opt_params=opt_params,
                verificatable_result=VerificateFunctionApproximation(),
                # # Size of Test data set. If this value is `0`, the validation will not be executed.
                test_size_rate=0.3,
                # Tolerance for the optimization.
                # When the loss or score is not improving by at least tol 
                # for two consecutive iterations, convergence is considered 
                # to be reached and training stops.
                tol=1e-15
            )

            generative_model = Generator(
                batch_size=batch_size,
                learning_rate=learning_rate,
                convolutional_auto_encoder=convolutional_auto_encoder,
                channel=channel,
                verbose_mode=False
            )
        generative_model.noise_sampler = noise_sampler

        if discriminative_model is None:
            activation_function = TanhFunction()
            activation_function.batch_norm = BatchNorm()

            # Convolution layer.
            conv = ConvolutionLayerD1(
                # Computation graph for first convolution layer.
                CNNGraphD1(
                    # Logistic function as activation function.
                    activation_function=activation_function,
                    # The number of `filter`.
                    filter_num=batch_size,
                    # The number of channel.
                    channel=channel,
                    # The size of kernel.
                    kernel_size=3,
                    # The filter scale.
                    scale=0.001,
                    # The nubmer of stride.
                    stride=1,
                    # The number of zero-padding.
                    pad=1
                )
            )

            # Stack.
            layerable_cnn_list=[
                conv
            ]

            opt_params = Adam()
            opt_params.dropout_rate = 0.0

            if hidden_dim is None:
                hidden_dim = channel * seq_len * dim

            cnn_output_activating_function = LogisticFunction()

            cnn_output_graph = CNNOutputGraph(
                hidden_dim=hidden_dim, 
                output_dim=1, 
                activating_function=cnn_output_activating_function, 
                scale=0.01
            )

            discriminative_model = Discriminator(
                batch_size=batch_size,
                layerable_cnn_list=layerable_cnn_list,
                cnn_output_graph=cnn_output_graph,
                opt_params=opt_params,
                computable_loss=CrossEntropy(),
                learning_rate=learning_rate,
                verbose_mode=False
            )

        if gans_value_function is None:
            gans_value_function = MiniMax()

        GAN = AdversarialAutoEncoders(gans_value_function=gans_value_function)

        self.__noise_sampler = noise_sampler
        self.__true_sampler = true_sampler
        self.__generative_model = generative_model
        self.__discriminative_model = discriminative_model
        self.__GAN = GAN
        self.__time_fraction = time_fraction
        self.__min_pitch = min_pitch
        self.__max_pitch = max_pitch

    def learn(self, iter_n=500, k_step=10):
        '''
        Learning.

        Args:
            iter_n:     The number of training iterations.
            k_step:     The number of learning of the `discriminator`.

        '''
        generative_model, discriminative_model = self.__GAN.train(
            self.__true_sampler,
            self.__generative_model,
            self.__discriminative_model,
            iter_n=iter_n,
            k_step=k_step
        )
        self.__generative_model = generative_model
        self.__discriminative_model = discriminative_model

    def extract_logs(self):
        '''
        Extract update logs data.

        Returns:
            The shape is:
            - `list` of the reconstruction errors.
            - `list` of probabilities inferenced by the `discriminator` (mean) in the `discriminator`'s update turn.
            - `list` of probabilities inferenced by the `discriminator` (mean) in the `generator`'s update turn.

        '''
        return self.__GAN.extract_logs_tuple()

    def compose(self, file_path, velocity_mean=None, velocity_std=None):
        '''
        Compose by learned model.

        Args:
            file_path:      Path to generated MIDI file.

            velocity_mean:  Mean of velocity.
                            This class samples the velocity from a Gaussian distribution of 
                            `velocity_mean` and `velocity_std`.
                            If `None`, the average velocity in MIDI files set to this parameter.

            velocity_std:   Standard deviation(SD) of velocity.
                            This class samples the velocity from a Gaussian distribution of 
                            `velocity_mean` and `velocity_std`.
                            If `None`, the SD of velocity in MIDI files set to this parameter.
        '''
        generated_arr = self.__generative_model.draw()

        # @TODO(chimera0(RUM)): Fix the redundant processings.
        if velocity_mean is None:
            velocity_mean = np.array(
                [self.__midi_df_list[i].velocity.mean() for i in range(len(self.__midi_df_list))]
            ).mean()
        if velocity_std is None:
            velocity_std = np.array(
                [self.__midi_df_list[i].velocity.std() for i in range(len(self.__midi_df_list))]
            ).std()

        generated_list = []
        start = 0
        end = self.__time_fraction
        for batch in range(generated_arr.shape[0]):
            for program_key in range(generated_arr.shape[1]):
                seq_arr, pitch_arr = np.where(generated_arr[batch, program_key] == 1)
                key_df = pd.DataFrame(
                    np.c_[
                        seq_arr, 
                        pitch_arr, 
                        generated_arr[batch, program_key, seq_arr, pitch_arr]
                    ], 
                    columns=["seq", "pitch", "p"]
                )
                key_df = key_df.sort_values(by=["p"], ascending=False)
                program = self.__noise_sampler.program_list[program_key]
                for seq in range(generated_arr.shape[2]):
                    df = key_df[key_df.seq == seq]
                    for i in range(df.shape[0]):
                        pitch = int(df.pitch.values[i] + self.__min_pitch)
                        velocity = np.random.normal(loc=velocity_mean, scale=velocity_std)
                        velocity = int(velocity)
                        generated_list.append((program, start, end, pitch, velocity))

                start += self.__time_fraction
                end += self.__time_fraction

        generated_midi_df = pd.DataFrame(
            generated_list, 
            columns=[
                "program",
                "start", 
                "end", 
                "pitch", 
                "velocity"
            ]
        )

        pitch_arr = generated_midi_df.pitch.drop_duplicates()
        df_list = []
        for pitch in pitch_arr:
            df = generated_midi_df[generated_midi_df.pitch == pitch]
            df = df.sort_values(by=["start", "end"])
            df["next_start"] = df.start.shift(-1)
            df["next_end"] = df.end.shift(-1)
            df.loc[df.end == df.next_start, "end"] = df.loc[df.end == df.next_start, "next_end"]
            df = df.drop_duplicates(["end"])
            df_list.append(df)

        generated_midi_df = pd.concat(df_list)
        generated_midi_df = generated_midi_df.sort_values(by=["start", "end"])

        self.__midi_controller.save(
            file_path=file_path, 
            note_df=generated_midi_df
        )

    def get_generative_model(self):
        ''' getter '''
        return self.__generative_model
    
    def set_readonly(self, value):
        ''' setter '''
        raise TypeError("This property must be read-only.")
    
    generative_model = property(get_generative_model, set_readonly)

    def get_true_sampler(self):
        ''' getter '''
        return self.__true_sampler
    
    true_sampler = property(get_true_sampler, set_readonly)