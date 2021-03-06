# -*- coding: utf-8 -*-
import numpy as np
cimport numpy as np
from pydbm.activation.sign_function import SignFunction
ctypedef np.float64_t DOUBLE_t
from pydbm.activation.logistic_function import LogisticFunction


class StochasticBinaryNeurons(SignFunction):
    '''
    Stochastic Binary Neurons as a Sign function.

    The binary neurons are neurons that output binary valued predictions as a sign-like function. 
    The stochastic binary neurons, in contrast, binarize an input according to a probability.

    This class entries a sigmoid-adjusted Straight-Through Estimator for backpropagation.
    In the backward pass, the Straight-Through Estimator simply treats the binary neurons 
    as identify functions and ignores their gradients. A variant of the Straight-Through Estimator 
    is the sigmoid-adjusted Straight-Through Estimator, which multiplies the gradients in the 
    backward pass by the derivative of the sigmoid function.

    References:
        - Chung, J., Ahn, S., & Bengio, Y. (2016). Hierarchical multiscale recurrent neural networks. arXiv preprint arXiv:1609.01704.
        - Dong, H. W., & Yang, Y. H. (2018). Convolutional generative adversarial networks with binary neurons for polyphonic music generation. arXiv preprint arXiv:1804.09399.
        - Oza, M., Vaghela, H., & Srivastava, K. (2019). Progressive Generative Adversarial Binary Networks for Music Generation. arXiv preprint arXiv:1903.04722.
    '''

    # The value of the Heaviside step function when input is `0`.
    __zero_value = 0.5

    def get_zero_value(self):
        '''
        getter for the value of the Heaviside step function when input is `0`.
        '''
        return self.__zero_value
    
    def set_zero_value(self, value):
        '''
        setter for the value of the Heaviside step function when input is `0`.
        '''
        self.__zero_value = value

    zero_value = property(get_zero_value, set_zero_value)

    def __init__(self, memory_len=50):
        '''
        Init.

        Args:
            memory_len:     The number of memos of activities for derivative in backward.

        '''
        super().__init__(memory_len=memory_len)
        self.__logistic_function = LogisticFunction(memory_len=memory_len)
        self.__u_activated_arr_list = []
        self.__u_forwarded_arr_list = []

    def activate(self, np.ndarray x):
        '''
        Activate and extract feature points in forward propagation.

        Args:
            x   `np.ndarray` of observed data points.

        Returns:
            `np.ndarray` of the activated feature points.
        '''
        u_activated_arr = np.random.uniform(low=0, high=1, size=x.copy().shape)

        x = self.__logistic_function.activate(x)
        x = x - u_activated_arr
        x = np.heaviside(x, self.zero_value)

        self.__u_activated_arr_list.append(u_activated_arr)
        if len(self.__u_activated_arr_list) > self.memory_len:
            self.__u_activated_arr_list = self.__u_activated_arr_list[len(self.__u_activated_arr_list) - self.memory_len:]

        if self.batch_norm is not None:
            x = self.batch_norm.forward_propagation(x)

        return x

    def derivative(self, np.ndarray y):
        '''
        Derivative and extract delta in back propagation.

        Args:
            y:  `np.ndarray` of delta.

        Returns:
            `np.ndarray` of delta.
        '''
        if self.batch_norm is not None:
            y = self.batch_norm.back_propagation(y)

        u_activated_arr = self.__u_activated_arr_list.pop(-1)

        y = y + u_activated_arr
        y = self.__logistic_function.derivative(y)

        return y

    def forward(self, np.ndarray x):
        '''
        Forward propagation but not retain the activation.

        Args:
            x   `np.ndarray` of observed data points.

        Returns:
            The result.
        '''
        u_forward_arr = np.random.uniform(low=0, high=1, size=x.copy().shape)

        x = self.__logistic_function.forward(x)
        x = x - u_forward_arr
        x = np.heaviside(x, self.zero_value)

        self.__u_forward_arr_list.append(u_forward_arr)
        if len(self.__u_forward_arr_list) > self.memory_len:
            self.__u_forward_arr_list = self.__u_forward_arr_list[len(self.__u_forward_arr_list) - self.memory_len:]

        return x

    def backward(self, np.ndarray y):
        '''
        Back propagation but not operate the activation.

        Args:
            y:  `np.ndarray` of delta.

        Returns:
            The result.
        '''
        u_forward_arr = self.__u_forward_arr_list.pop(-1)
        y = y + u_forward_arr
        y = self.__logistic_function.backward(y)
        return y
