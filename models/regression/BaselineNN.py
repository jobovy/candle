from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers import Dense, Activation, Dropout, Input, BatchNormalization
from keras.models import Model, load_model
from keras.regularizers import l2
import numpy as np
import services.ModelPerformanceVisualization as model_visualizer

'''
A baseline neural network that consists of separate fully connected layers to a given star spectra and 
does regression on asteroseismic parameters, and is easily adaptable to regression or binary classification

Star spectra for this model should be dimensionally reduced prior to prediction due to the size of a large 
fully connected layer and low count of training data
'''

class BaselineNN(object):

	# Constant for where to save this model
	MODEL_FILEPATH = "models/regression/BaselineNN.h5"

	'''
	Creates the baseline NN with separate fully connected layers on stellar spectra
	Inputs:
		S_D - Dimension of spectra data
		shared - Use shared Dense layers to predict stellar parameters
	'''
	def __init__(self, S_D = 10, shared = False):
		self._shared = shared

		# Create the model
		input_spectra = Input(shape=(S_D,), name='input_spectra')

		dense_layer_1 = Dropout(0.15)(Dense(128, activation='relu')(input_spectra))
		dense_layer_2 = Dropout(0.15)(Dense(64, activation='relu')(dense_layer_1))
		prediction_ps = Dense(1, activation='linear', name='DPi1')(dense_layer_2)

		# Dense layers for Dnu
		dense_layer_1 = Dropout(0.1)(Dense(64, activation='relu')(input_spectra))
		dense_layer_2 = Dropout(0.1)(Dense(32, activation='relu')(dense_layer_1))
		prediction_dnu = Dense(1, activation='linear', name='Dnu')(dense_layer_2)
		self.model = Model(input=input_spectra, outputs=[prediction_ps, prediction_dnu])

	'''
	Compile the model given the optimizer, loss function, and the model architecture and metrics
	Input:
		loss_fn - The loss function to use
		optimizer - The optimizer to use
		metrics - Metrics for the model
	Returns:
		None
	'''
	def compile(self, loss_fn='mse', optimizer = 'adam', metrics = ['mae', 'mape']):
		self.model.compile(optimizer=optimizer, loss=loss_fn, metrics=metrics)


	'''
	Fits the model given the input data X and asteroseismic features y (DPi1, Dnu) and returns the history of the model
	Input:
		X - Stellar spectra (m x d) ndarray
		y - Asteroseismic parameters (m x 2) ndarray
		epochs - The number of epochs for this model
		batch_size - Batch size to train
		validation_split - Validation split percentage
		save_best_val - If true, the model is only updated if the validation loss is better than the current best one
	Returns:
		History object
	'''
	def fit(self, X, y, epochs = 10, batch_size = 32, validation_split = 0.1, save_best_val = False):
		callbacks = []
		if save_best_val:
			callbacks.append(ModelCheckpoint(BaselineNN.MODEL_FILEPATH, save_best_only=True, monitor='val_loss'))

		# Fit the model
		fit_results = self.model.fit(X, y, epochs = epochs, batch_size = batch_size, validation_split = validation_split, shuffle = True, callbacks = callbacks)

		if save_best_val:
			# Take the best validation error as the model parameters
			self.model.load()

		# Return the fit results
		return fit_results


	'''
	Returns a tuple of the model's performance based on the loss function value and the metrics given to it when compiled
	Inputs:
		X - Stellar spectra (m x d) ndarray
		y - Asteroseismic parameters (m x 2) ndarry
	Returns:
		List of scalars of loss function value and metrics
	'''
	def score(self, X, y):
		return self.model.evaluate(X, y)

	'''
	Predicts on a given test data sample
	Inputs:
		X - The spectra data
	Returns:
		array of nparray, [0] => PS, [1] => Δv
	'''
	def predict(self, X):
		return self.model.predict(X)

	'''
	Saves the model into its constant defined file
	'''
	def save(self):
		self.model.save(BaselineNN.MODEL_FILEPATH)

	'''
	If called, loads the current saved model as the starting point
	'''
	def load(self):
		self.model = load_model(BaselineNN.MODEL_FILEPATH)